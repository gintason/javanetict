from django.urls import path
from . import views

urlpatterns = [
    path('sessions/', views.ChatSessionListView.as_view(), name='chat-sessions-list'),
    path('sessions/<str:session_id>/', views.ChatSessionDetailView.as_view(), name='chat-session-detail'),
    # Add the chatbot endpoint
    path('chat/', views.ChatbotView.as_view(), name='chatbot'),
]