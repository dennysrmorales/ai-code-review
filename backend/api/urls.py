from django.urls import path
from .views import CodeReviewView

def trigger_error(request):
    """Trigger a test error for Sentry debugging."""
    division_by_zero = 1 / 0

urlpatterns = [
    path('review/', CodeReviewView.as_view(), name='code-review'),
    path('sentry-debug/', trigger_error)
]
