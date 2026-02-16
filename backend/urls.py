from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# -------------------------------------------------
# Health Check Endpoint (for DigitalOcean)
# -------------------------------------------------

def health(request):
    return JsonResponse({"status": "ok"})


# -------------------------------------------------
# URL Patterns
# -------------------------------------------------

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Health check
    path("health/", health),

    # API routes
    path("api/", include("api.urls")),
    path("api/auth/", include("users.urls")),
    path("api/users/", include("users.urls")),

    # App-specific APIs
    path("api/core/", include("core.urls")),
    path("api/chatbot/", include("chatbot.urls")),
    path("api/proposals/", include("proposals.urls")),

    # JWT Authentication
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# Serve media files in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
