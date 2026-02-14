from django.db import models
import uuid

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    user_info = models.JSONField(blank=True, null=True)  # NEW FIELD
    country = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.session_id[:8]}..."

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('USER', 'User Message'),
        ('BOT', 'Bot Response'),
        ('SYSTEM', 'System Message'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class Intent(models.Model):
    tag = models.CharField(max_length=100, unique=True)
    patterns = models.JSONField(default=list)
    responses = models.JSONField(default=list)
    followups = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.tag

class ChatbotConfig(models.Model):
    name = models.CharField(max_length=100, default='default')
    intents = models.JSONField(default=list)
    conversation_flow = models.JSONField(default=list)
    industry_responses = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Chatbot Configuration'
        verbose_name_plural = 'Chatbot Configurations'
    
    def __str__(self):
        return f"Chatbot Config: {self.name}"