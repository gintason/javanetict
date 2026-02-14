from rest_framework import serializers
from core.models import Feature, Testimonial, Client
from chatbot.models import ChatSession, ChatMessage
from proposals.models import ProposalRequest

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = '__all__'

class TestimonialSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.institution_name', read_only=True)
    client_country = serializers.CharField(source='client.country', read_only=True)
    
    class Meta:
        model = Testimonial
        fields = ['id', 'content', 'rating', 'client_name', 'client_country', 'created_at']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'message_type', 'content', 'timestamp']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['id', 'session_id', 'country', 'currency', 'user_info', 'created_at', 'last_activity', 'messages']

class ProposalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalRequest
        fields = '__all__'
        read_only_fields = ['status', 'proposal_pdf', 'created_at', 'updated_at', 'deployment_fee']
    
    def create(self, validated_data):
        # Auto-detect currency based on country
        country = validated_data.get('country', '').lower()
        if 'nigeria' in country or any(african_country in country for african_country in ['ghana', 'kenya', 'south africa']):
            validated_data['currency'] = 'NGN'
        else:
            validated_data['currency'] = 'USD'
        
        return super().create(validated_data)

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class PlatformDemoSerializer(serializers.Serializer):
    institution_name = serializers.CharField(max_length=200)
    primary_color = serializers.CharField(max_length=7, default='#1A237E')
    secondary_color = serializers.CharField(max_length=7, default='#00C853')
    accent_color = serializers.CharField(max_length=7, default='#7B1FA2')
    has_logo = serializers.BooleanField(default=False)
    logo_url = serializers.URLField(required=False, allow_blank=True)
    ctb_enabled = serializers.BooleanField(default=True)
    live_classes_enabled = serializers.BooleanField(default=False)