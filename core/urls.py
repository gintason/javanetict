from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'features', views.FeatureViewSet, basename='feature')
router.register(r'testimonials', views.TestimonialViewSet, basename='testimonial')
router.register(r'clients', views.ClientViewSet, basename='client')
router.register(r'contact', views.ContactViewSet, basename='contact')  # New endpoint

urlpatterns = [
    path('', include(router.urls)),
]