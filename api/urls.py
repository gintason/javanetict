from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'features', views.FeatureViewSet, basename='feature')
router.register(r'testimonials', views.TestimonialViewSet, basename='testimonial')

urlpatterns = [
    # API Root
    path('', views.api_root, name='api-root'),
    
    # Features & Testimonials
    path('', include(router.urls)),
    
    # AI Chatbot
    path('chat/send/', views.ChatBotView.as_view(), name='chat-send'),
    
    # Proposal Generator (One-time fee)
    path('proposals/generate/', views.ProposalGeneratorView.as_view(), name='generate-proposal'),
    
    # Platform Demo Simulator
    path('demo/platform/', views.PlatformDemoView.as_view(), name='platform-demo'),
    
    # Currency & Localization with Deployment Fee
    path('currency/detect/', views.CurrencyDetectView.as_view(), name='detect-currency'),
    
    # Health Check
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]