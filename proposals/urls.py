from django.urls import path
from . import views

urlpatterns = [
    # Existing endpoints
    path('requests/', views.ProposalRequestListView.as_view(), name='proposal-requests-list'),
    path('requests/<uuid:pk>/', views.ProposalRequestDetailView.as_view(), name='proposal-request-detail'),
    
    # New endpoints for proposal generation and PDF
    path('generate/', views.GenerateProposalView.as_view(), name='generate-proposal'),
    path('generate-pdf/', views.GenerateProposalPDFView.as_view(), name='generate-pdf'),
]