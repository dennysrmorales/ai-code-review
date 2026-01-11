import json
import logging
import time
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import sentry_sdk
from openai import OpenAI

logger = logging.getLogger(__name__)


def safe_capture_exception(exception, **kwargs):
    """
    Safely capture exception in Sentry, handling Python 3.13 compatibility issues.
    
    Args:
        exception: The exception to capture
        **kwargs: Additional context (tags, extra, etc.)
    """
    try:
        sentry_sdk.capture_exception(exception, **kwargs)
    except Exception:
        # If Sentry capture fails (e.g., Python 3.13 compatibility issues), just log it
        logger.error(f"Sentry capture failed: {exception}", exc_info=True)


def safe_capture_message(message, level="info", **kwargs):
    """
    Safely capture message in Sentry, handling Python 3.13 compatibility issues.
    
    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context (tags, extra, etc.)
    """
    try:
        sentry_sdk.capture_message(message, level=level, **kwargs)
    except Exception:
        # If Sentry capture fails, just log it
        logger.warning(f"Sentry message capture failed: {message}")


class CodeReviewView(APIView):
    """
    API endpoint to review code using AI.
    """
    
    def post(self, request):
        # Start transaction for performance monitoring
        with sentry_sdk.start_transaction(op="http.server", name="POST /api/review/"):
            start_time = time.time()
            
            try:
                code = request.data.get('code', '')
                language = request.data.get('language', 'python')
                code_length = len(code) if code else 0
                
                # Set Sentry tags for context
                sentry_sdk.set_tag("feature", "code-review")
                sentry_sdk.set_tag("language", language)
                sentry_sdk.set_tag("ai.model", "gpt-4o-mini")
                sentry_sdk.set_tag("endpoint", "/api/review/")
                sentry_sdk.set_context("request", {
                    "code_length": code_length,
                    "language": language,
                    "method": "POST",
                })
                #sentry_sdk.capture_exception(Exception("Test code review error"))
                
                # Validate input with performance span
                with sentry_sdk.start_span(op="validation", description="Validate input"):
                    if not code or not isinstance(code, str):
                        safe_capture_message(
                            "Invalid input: empty or non-string code",
                            level="warning",
                            tags={"validation_error": "empty_or_invalid_type", "language": language}
                        )
                        return Response(
                            {'error': 'Code is required and must be a string'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    if code_length > 10000:
                        safe_capture_message(
                            f"Code too long: {code_length} characters",
                            level="warning",
                            tags={
                                "validation_error": "code_too_long",
                                "language": language,
                                "code_length": str(code_length)
                            },
                            extra={"code_length": code_length, "max_length": 10000}
                        )
                        return Response(
                            {'error': 'Code is too long. Maximum 10000 characters allowed'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Check if OpenAI API key is configured
                with sentry_sdk.start_span(op="config.check", description="Check OpenAI configuration"):
                    if not settings.OPENAI_API_KEY:
                        error_msg = "OpenAI API key not configured"
                        safe_capture_message(
                            error_msg,
                            level="error",
                            tags={"error_type": "configuration", "service": "openai"}
                        )
                        logger.error(error_msg)
                        return Response(
                            {'error': 'AI service not configured'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                
                # Analyze code using OpenAI with performance monitoring
                try:
                    with sentry_sdk.start_span(op="ai.analysis", description=f"Reviewing {language} code"):
                        # Set additional context for AI operation
                        sentry_sdk.set_context("ai_operation", {
                            "model": "gpt-4o-mini",
                            "language": language,
                            "code_length": code_length,
                            "temperature": 0.3,
                            "max_tokens": 2000,
                        })
                        
                        client = OpenAI(api_key=settings.OPENAI_API_KEY)
                        
                        prompt = f"""Analyze the following {language} code and provide a code review. 
Return a JSON response with the following structure:
{{
    "issues": [
        {{
            "line": <line_number>,
            "severity": "<error|warning|info>",
            "message": "<description>",
            "suggestion": "<suggested_fix>"
        }}
    ],
    "summary": "<overall_summary>",
    "score": <0-100>
}}

Code to review:
```
{code}
```

Only return the JSON, no other text."""

                        # OpenAI API call - this will be automatically tracked in the span
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a code review assistant. Always respond with valid JSON only."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                            max_tokens=2000,
                        )
                    
                    # Parse response with span
                    with sentry_sdk.start_span(op="response.parse", description="Parse AI response"):
                        review_text = response.choices[0].message.content.strip()
                        
                        # Try to extract JSON from response (handle markdown code blocks)
                        if review_text.startswith('```'):
                            # Remove markdown code block markers
                            review_text = review_text.split('```')[1]
                            if review_text.startswith('json'):
                                review_text = review_text[4:]
                            review_text = review_text.strip()
                        
                        review_data = json.loads(review_text)
                        
                        # Set success context
                        if review_data:
                            sentry_sdk.set_context("ai_response", {
                                "issues_count": len(review_data.get("issues", [])),
                                "score": review_data.get("score"),
                                "has_summary": bool(review_data.get("summary")),
                            })
                            sentry_sdk.set_tag("ai.success", "true")
                
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse AI response: {str(e)}"
                    sentry_sdk.set_tag("ai.success", "false")
                    sentry_sdk.set_tag("error_type", "json_parse_error")
                    safe_capture_exception(
                        e,
                        tags={
                            "error_type": "json_parse_error",
                            "language": language,
                            "ai.model": "gpt-4o-mini"
                        },
                        extra={
                            "code_length": code_length,
                            "language": language,
                            "response_preview": review_text[:200] if 'review_text' in locals() else None
                        }
                    )
                    logger.error(error_msg)
                    return Response(
                        {'error': 'Failed to parse AI response'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                except Exception as e:
                    error_msg = f"OpenAI API error: {str(e)}"
                    sentry_sdk.set_tag("ai.success", "false")
                    sentry_sdk.set_tag("error_type", "openai_api_error")
                    safe_capture_exception(
                        e,
                        tags={
                            "error_type": "openai_api_error",
                            "language": language,
                            "ai.model": "gpt-4o-mini",
                            "service": "openai"
                        },
                        extra={
                            "code_length": code_length,
                            "language": language,
                            "error_details": str(e)
                        }
                    )
                    logger.error(error_msg)
                    return Response(
                        {'error': 'AI analysis failed'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Calculate response time and monitor performance
                response_time = time.time() - start_time
                
                # Track performance metrics
                sentry_sdk.set_measurement("response_time", response_time, unit="second")
                sentry_sdk.set_tag("response_time_category", 
                    "slow" if response_time > 5.0 else "normal" if response_time > 2.0 else "fast")
                
                # Track slow responses
                if response_time > 5.0:
                    safe_capture_message(
                        f"Slow code review response: {response_time:.2f}s",
                        level="warning",
                        tags={
                            "performance": "slow_response",
                            "language": language,
                            "threshold": "5s"
                        },
                        extra={
                            "response_time": response_time,
                            "code_length": code_length,
                            "language": language
                        }
                    )
                elif response_time > 2.0:
                    # Log normal response times at info level
                    safe_capture_message(
                        f"Code review completed: {response_time:.2f}s",
                        level="info",
                        tags={
                            "performance": "normal_response",
                            "language": language
                        }
                    )
                
                return Response({
                    'review': review_data,
                    'response_time': round(response_time, 2)
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                error_msg = f"Unexpected error in code review: {str(e)}"
                sentry_sdk.set_tag("error_type", "unexpected_error")
                safe_capture_exception(
                    e,
                    tags={
                        "error_type": "unexpected_error",
                        "language": language if 'language' in locals() else "unknown",
                        "endpoint": "/api/review/"
                    },
                    extra={
                        "code_length": code_length if 'code_length' in locals() else 0,
                        "language": language if 'language' in locals() else "unknown"
                    }
                )
                logger.error(error_msg, exc_info=True)
                return Response(
                    {'error': 'An unexpected error occurred'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
