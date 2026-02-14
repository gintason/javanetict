from rest_framework import serializers
from .models import Feature, Testimonial, Client, Contact

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

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'institution', 'phone', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']