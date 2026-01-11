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


def safe_capture_exception(exception):
    """Safely capture exception in Sentry, handling Python 3.13 compatibility issues."""
    try:
        sentry_sdk.capture_exception(exception)
    except Exception:
        # If Sentry capture fails (e.g., Python 3.13 compatibility issues), just log it
        logger.error(f"Sentry capture failed: {exception}", exc_info=True)


class CodeReviewView(APIView):
    """
    API endpoint to review code using AI.
    """
    
    def post(self, request):
        start_time = time.time()
        
        try:
            code = request.data.get('code', '')
            language = request.data.get('language', 'python')
            
            # Validate input
            if not code or not isinstance(code, str):
                sentry_sdk.capture_message(
                    "Invalid input: empty or non-string code",
                    level="warning"
                )
                return Response(
                    {'error': 'Code is required and must be a string'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(code) > 10000:
                sentry_sdk.capture_message(
                    f"Code too long: {len(code)} characters",
                    level="warning"
                )
                return Response(
                    {'error': 'Code is too long. Maximum 10000 characters allowed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if OpenAI API key is configured
            if not settings.OPENAI_API_KEY:
                error_msg = "OpenAI API key not configured"
                sentry_sdk.capture_message(error_msg, level="error")
                logger.error(error_msg)
                return Response(
                    {'error': 'AI service not configured'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Analyze code using OpenAI
            try:
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

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a code review assistant. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                )
                
                review_text = response.choices[0].message.content.strip()
                
                # Try to extract JSON from response (handle markdown code blocks)
                if review_text.startswith('```'):
                    # Remove markdown code block markers
                    review_text = review_text.split('```')[1]
                    if review_text.startswith('json'):
                        review_text = review_text[4:]
                    review_text = review_text.strip()
                
                review_data = json.loads(review_text)
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse AI response: {str(e)}"
                safe_capture_exception(e)
                logger.error(error_msg)
                return Response(
                    {'error': 'Failed to parse AI response'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                error_msg = f"OpenAI API error: {str(e)}"
                safe_capture_exception(e)
                logger.error(error_msg)
                return Response(
                    {'error': 'AI analysis failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Track slow responses
            if response_time > 5.0:
                sentry_sdk.capture_message(
                    f"Slow code review response: {response_time:.2f}s",
                    level="warning"
                )
            
            return Response({
                'review': review_data,
                'response_time': round(response_time, 2)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_msg = f"Unexpected error in code review: {str(e)}"
            safe_capture_exception(e)
            logger.error(error_msg, exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
