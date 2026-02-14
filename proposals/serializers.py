from rest_framework import serializers
from .models import ProposalRequest

class ProposalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalRequest
        fields = '__all__'
        read_only_fields = ['id', 'status', 'proposal_pdf', 'created_at', 'updated_at', 'deployment_fee', 'currency']
    
    def create(self, validated_data):
        # Auto-detect currency based on country
        country = validated_data.get('country', '').lower()
        if country in ['nigeria', 'ghana', 'kenya', 'south africa']:
            validated_data['currency'] = 'NGN'
        else:
            validated_data['currency'] = 'USD'
        
        # Set initial status
        validated_data['status'] = 'PENDING'
        
        return super().create(validated_data)