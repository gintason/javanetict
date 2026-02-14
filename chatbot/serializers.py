from rest_framework import serializers
from .models import ChatSession, ChatMessage
from django.utils.timezone import now

class ChatMessageSerializer(serializers.ModelSerializer):
    # Add computed fields for better frontend display
    formatted_time = serializers.SerializerMethodField()
    is_user = serializers.SerializerMethodField()  # For frontend compatibility
    
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'message_type',      # Your model field: 'USER', 'BOT', 'SYSTEM'
            'content',           # Your model field
            'timestamp',         # Your model field
            'formatted_time',    # Computed: formatted timestamp
            'is_user',           # Computed: boolean for frontend
            'session_id'         # Include session ID for reference
        ]
        read_only_fields = ['timestamp']
    
    def get_formatted_time(self, obj):
        """Return formatted time for display (e.g., 02:30 PM)"""
        return obj.timestamp.strftime('%I:%M %p') if obj.timestamp else ''
    
    def get_is_user(self, obj):
        """Convert message_type to is_user boolean for frontend compatibility"""
        return obj.message_type == 'USER'

class ChatSessionSerializer(serializers.ModelSerializer):
    # Include related messages
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    # Add computed fields for better UI/analytics
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    user_country = serializers.SerializerMethodField()  # Alias for frontend
    
    class Meta:
        model = ChatSession
        fields = [
            'id',
            'session_id',       # Your model field
            'ip_address',       # Your model field
            'user_agent',       # Your model field
            'user_info',        # Your model field (JSON)
            'country',          # Your model field
            'currency',         # Your model field (default='USD')
            'created_at',       # Your model field
            'last_activity',    # Your model field
            'messages',         # Related messages
            'message_count',    # Computed: total messages
            'last_message',     # Computed: last message content
            'is_active',        # Computed: session active status
            'duration',         # Computed: session duration in minutes
            'user_country'      # Alias for frontend (same as country)
        ]
        read_only_fields = ['created_at', 'last_activity']
    
    def get_message_count(self, obj):
        """Return total number of messages in this session"""
        return obj.messages.count()
    
    def get_last_message(self, obj):
        """Return the last message content (truncated)"""
        last_msg = obj.messages.last()
        if last_msg:
            content = last_msg.content
            return content[:60] + '...' if len(content) > 60 else content
        return 'No messages yet'
    
    def get_is_active(self, obj):
        """Check if session is active (within last 30 minutes)"""
        if not obj.last_activity:
            return False
        time_diff = now() - obj.last_activity
        return time_diff.total_seconds() < 1800  # 30 minutes
    
    def get_duration(self, obj):
        """Calculate session duration in minutes"""
        if not obj.created_at or not obj.last_activity:
            return 0
        duration = obj.last_activity - obj.created_at
        return int(duration.total_seconds() / 60)  # Convert to minutes
    
    def get_user_country(self, obj):
        """Alias for country field (for frontend compatibility)"""
        return obj.country

# Create separate serializers for chatbot API requests/responses
class ChatbotRequestSerializer(serializers.Serializer):
    """Serializer for chatbot API requests"""
    session_id = serializers.CharField(required=True, max_length=100)
    message = serializers.CharField(required=True, min_length=1, max_length=1000)
    country = serializers.CharField(required=False, max_length=100, default='')
    currency = serializers.CharField(required=False, max_length=3, default='USD')
    
    def validate_session_id(self, value):
        """Validate session ID format"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Invalid session ID")
        return value.strip()

class ChatbotResponseSerializer(serializers.Serializer):
    """Serializer for chatbot API responses"""
    response = serializers.CharField()
    timestamp = serializers.DateTimeField()
    session_id = serializers.CharField()
    message_id = serializers.CharField(required=False)
    country = serializers.CharField(required=False, allow_blank=True)
    currency = serializers.CharField(required=False, default='USD')
    
    def create(self, validated_data):
        """Not needed for response serializer"""
        pass
    
    def update(self, instance, validated_data):
        """Not needed for response serializer"""
        pass