from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import FileResponse, HttpResponse
from django.core.files.base import ContentFile
import json
import uuid
import os
from datetime import datetime, timedelta
import io

# PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# AI Integration
import openai
import cohere

# Import models
from core.models import Feature, Testimonial, Client
from chatbot.models import ChatSession, ChatMessage
from proposals.models import ProposalRequest
from users.models import CustomUser, UserActivity

# Import serializers
from .serializers import (
    FeatureSerializer, TestimonialSerializer,
    ChatSessionSerializer, ChatMessageSerializer,
    ProposalRequestSerializer, ClientSerializer,
    PlatformDemoSerializer
)

# ============================================================================
# AI SERVICE HELPER CLASS
# ============================================================================

class AIService:
    """Unified AI service with fallbacks"""
    
    def __init__(self):
        self.openai_available = False
        self.cohere_available = False
        
        # Check OpenAI
        openai_key = os.getenv('OPENAI_API_KEY', '')
        if openai_key and len(openai_key) > 10:
            openai.api_key = openai_key
            self.openai_available = True
        
        # Check Cohere
        cohere_key = os.getenv('COHERE_API_KEY', '')
        if cohere_key and len(cohere_key) > 10:
            try:
                self.cohere_client = cohere.Client(cohere_key)
                self.cohere_available = True
            except:
                self.cohere_available = False
        else:
            self.cohere_available = False
    
    def chat_with_openai(self, messages, max_tokens=500, temperature=0.7):
        """Chat with OpenAI"""
        if not self.openai_available:
            return None
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {e}")
            return None
    
    def chat_with_cohere(self, prompt, max_tokens=500, temperature=0.7):
        """Chat with Cohere"""
        if not self.cohere_available:
            return None
        
        try:
            response = self.cohere_client.generate(
                model='command',
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.generations[0].text.strip()
        except Exception as e:
            print(f"Cohere error: {e}")
            return None
    
    def get_response(self, message, context=None):
        """Get AI response with fallbacks"""
        # Try OpenAI first
        if self.openai_available:
            messages = [
                {"role": "system", "content": context or "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
            response = self.chat_with_openai(messages)
            if response:
                return response
        
        # Try Cohere next
        if self.cohere_available:
            prompt = f"{context or 'You are a helpful assistant.'}\n\nUser: {message}\nAssistant:"
            response = self.chat_with_cohere(prompt)
            if response:
                return response
        
        # Fallback to rule-based
        return self.rule_based_response(message, context)
    
    def rule_based_response(self, message, context=None):
        """Rule-based responses for fallback"""
        message_lower = message.lower()
        
        # Extract currency and country from context if available
        currency = 'USD'
        currency_symbol = '$'
        country = 'International'
        
        if context:
            if 'NGN' in context:
                currency = 'NGN'
                currency_symbol = '₦'
            if 'Nigeria' in context:
                country = 'Nigeria'
            elif 'Africa' in context:
                country = 'Africa'
        
        responses = {
            'hello': f"Hello! I'm JN Assistant from JavaNet EdTech Suite. How can I help you with our education technology solutions today?",
            'hi': f"Hi there! I'm here to assist you with JavaNet's custom edtech platform. Are you interested in our CBT testing system or live interactive classrooms?",
            'price': f"We offer one-time deployment fees: ₦5-10 million for African institutions, $10,000 for international institutions. Contact us for a custom quote.",
            'cost': f"Our one-time deployment fee ranges from ₦5-10 million for African countries to $10,000 - $25,000 for international institutions.",
            'demo': f"You can try our live demo at https://www.ischool.ng/ or use our interactive platform simulator on the website. Would you like me to guide you through the demo features?",
            'CBT': f"Our Computer-Based Testing system includes: automated grading, question banks, anti-cheat monitoring, detailed analytics, and certificate generation. All fully customizable with your branding.",
            'live class': f"Our Live Interactive Classroom features: virtual whiteboard, screen sharing, session recording, breakout rooms, teacher-student matching, and real-time collaboration tools.",
            'nigeria': f"For Nigerian institutions, we offer one-time deployment fees starting from ₦5 million. Many schools across Nigeria use our platform. You can see examples at ischool.ng.",
            'africa': f"For African institutions, we offer one-time deployment fees ranging from ₦5-10 million depending on requirements.",
            'international': f"For international institutions outside Africa, we offer a one-time deployment fee of $10,000 USD.",
            'custom': f"Yes! Our platform is 100% white-label. We customize it with your logo, colors, and domain name. It will look and feel like your own in-house developed platform.",
            'proposal': f"I can help you generate a custom proposal! Please use our proposal generator on the website, or tell me about your institution and I'll guide you through the process.",
            'contact': f"You can contact us at info@javanetict.com or call +234 703067 3089. Would you like to schedule a consultation call with our team?",
            'time': f"Deployment typically takes 2-4 weeks depending on customization requirements. We handle everything from setup to training your staff.",
            'integration': f"Our platform can integrate with existing systems like student management systems, payment gateways, and learning management systems. We provide API access for custom integrations.",
            'support': f"We offer 24/7 technical support, regular updates, and dedicated account management. Our support team is based in Nigeria with international coverage.",
            'default': f"Thank you for your message! I'm JN Assistant from JavaNet EdTech Suite. I can help you with:\n\n1. Information about our CBT testing system\n2. Details about our live interactive classrooms\n3. Customization and branding options\n4. Deployment fees\n5. Platform demonstration\n\nWhat would you like to know more about?"
        }
        
        # Check for keywords
        for keyword, response in responses.items():
            if keyword in message_lower and keyword != 'default':
                return response
        
        # Default response
        return responses['default']

# Create singleton instance
ai_service = AIService()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_activity(user, action, details=None, request=None):
    """Helper function to track user activities"""
    UserActivity.objects.create(
        user=user,
        action=action,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else None
    )

def detect_user_location(request):
    """Detect user location from IP or headers"""
    # Simplified detection
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '').lower()
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Check for Nigerian/African indicators
    african_languages = ['yo', 'ha', 'ig', 'sw', 'am', 'fr', 'ar']
    african_keywords = ['nigeria', 'ghana', 'kenya', 'south africa', 'tanzania', 'uganda']
    
    if 'ng' in accept_language or any(lang in accept_language for lang in african_languages):
        country = 'Nigeria'
        currency = 'NGN'
    elif any(keyword in accept_language for keyword in african_keywords):
        country = 'Africa'
        currency = 'NGN'
    elif ip and ip.startswith(('41.', '105.', '197.', '154.', '102.')):
        country = 'Africa'
        currency = 'NGN'
    else:
        country = 'International'
        currency = 'USD'
    
    return {
        'country': country,
        'currency': currency,
        'ip': ip
    }

def calculate_deployment_fee(country, needs_ctb=True, needs_live_classes=False, estimated_students=100):
    """Calculate one-time deployment fee based on client requirements"""
    if country.lower() in ['nigeria', 'ghana', 'kenya', 'south africa', 'tanzania', 'uganda']:
        # African countries: ₦5-10 million
        base_fee = 5000000  # ₦5 million base
        if needs_ctb and needs_live_classes:
            base_fee += 2000000  # ₦2 million extra for both modules
        elif needs_live_classes:
            base_fee += 1500000  # ₦1.5 million extra for live classes
        
        # Scale based on students
        if estimated_students > 1000:
            base_fee += 2000000
        elif estimated_students > 500:
            base_fee += 1000000
        elif estimated_students > 200:
            base_fee += 500000
            
        return {
            'amount': f"₦{base_fee:,.0f}",
            'currency': 'NGN',
            'currency_symbol': '₦',
            'range': '₦5,000,000 - ₦10,000,000',
            'note': 'One-time deployment fee'
        }
    else:
        # International: $10,000
        base_fee = 10000  # $10,000 base
        if needs_ctb and needs_live_classes:
            base_fee += 3000  # $3,000 extra for both modules
        elif needs_live_classes:
            base_fee += 2000  # $2,000 extra for live classes
        
        return {
            'amount': f"${base_fee:,.0f}",
            'currency': 'USD',
            'currency_symbol': '$',
            'range': '$10,000 - $15,000',
            'note': 'One-time deployment fee'
        }

# ============================================================================
# FEATURE VIEWS
# ============================================================================

class FeatureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for platform features
    """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def ctb_features(self, request):
        """Get all CTB testing features"""
        from django.db.models import Q
        features = Feature.objects.filter(Q(feature_type__iexact='ctb')).order_by('order')
        serializer = self.get_serializer(features, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def live_features(self, request):
        """Get all live classroom features"""
        features = Feature.objects.filter(feature_type='LIVE').order_by('order')
        serializer = self.get_serializer(features, many=True)
        return Response(serializer.data)

# ============================================================================
# TESTIMONIAL VIEWS
# ============================================================================

class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for client testimonials
    """
    queryset = Testimonial.objects.filter(is_featured=True).order_by('-created_at')
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent testimonials"""
        testimonials = Testimonial.objects.filter(
            is_featured=True
        ).order_by('-created_at')[:6]
        serializer = self.get_serializer(testimonials, many=True)
        return Response(serializer.data)

# ============================================================================
# AI CHATBOT VIEWS
# ============================================================================

class ChatBotView(APIView):
    """
    AI Chatbot endpoint (JN Assistant)
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle chatbot messages"""
        try:
            data = request.data
            session_id = data.get('session_id', str(uuid.uuid4()))
            message = data.get('message', '').strip()
            
            if not message:
                return Response(
                    {'error': 'Message is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Detect user location and currency
            location_data = detect_user_location(request)
            currency = location_data['currency']
            country = location_data['country']
            
            # Get or create chat session
            session, created = ChatSession.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'ip_address': location_data.get('ip'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'country': country,
                    'currency': currency,
                }
            )
            
            # Save user message
            ChatMessage.objects.create(
                session=session,
                message_type='USER',
                content=message
            )
            
            # Generate AI response using unified AI service
            bot_response = self.generate_response(
                message=message,
                currency=currency,
                country=country,
                session=session
            )
            
            # Save bot response
            ChatMessage.objects.create(
                session=session,
                message_type='BOT',
                content=bot_response
            )
            
            # Update session activity
            session.last_activity = timezone.now()
            session.save()
            
            return Response({
                'response': bot_response,
                'session_id': session_id,
                'currency': currency,
                'country': country,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            print(f"Chatbot error: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def generate_response(self, message, currency, country, session):
        """Generate response using AI service"""
        # Build context
        currency_symbol = '₦' if currency == 'NGN' else '$'
        deployment_fee = calculate_deployment_fee(country)
        
        context = f"""You are JN Assistant for JavaNet EdTech Suite.
        Company: JavaNet ICT Solutions Ltd
        Website: www.javanetict.com
        Live Demo: ischool.ng
        Location: {country}
        Currency: {currency} ({currency_symbol})
        Deployment Fee: {deployment_fee['amount']} one-time fee
        
        Products:
        1. ctb Testing System - Computer-based testing with automated grading
        2. Live Classroom Platform - Interactive virtual classrooms
        
        Key Features:
        - White-label/custom branding
        - One-time deployment fee (no monthly subscriptions)
        - African countries: ₦5-10 million
        - International: $10,000 USD
        - Custom proposal generator
        - Platform demo simulator
        
        Always be helpful, professional, and encourage users to:
        1. Try the live demo at ischool.ng
        2. Use the platform simulator
        3. Generate a custom proposal
        4. Contact for consultation"""
        
        # Use AI service
        response = ai_service.get_response(message, context)
        
        return response

# ============================================================================
# PROPOSAL GENERATOR VIEWS
# ============================================================================

class ProposalGeneratorView(APIView):
    """
    Proposal Generator with One-time Deployment Fee
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Generate a custom proposal with one-time deployment fee"""
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'email', 'institution', 'country']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'{field} is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Calculate deployment fee
            deployment_fee = calculate_deployment_fee(
                country=data['country'],
                needs_ctb=data.get('needs_ctb', True),
                needs_live_classes=data.get('needs_live_classes', False),
                estimated_students=data.get('estimated_students', 100)
            )
            
            # Create proposal record
            proposal_request = ProposalRequest.objects.create(
                name=data['name'],
                email=data['email'],
                institution=data['institution'],
                phone=data.get('phone', ''),
                country=data['country'],
                needs_ctb=data.get('needs_ctb', True),
                needs_live_classes=data.get('needs_live_classes', False),
                estimated_students=data.get('estimated_students', 100),
                estimated_teachers=data.get('estimated_teachers', 10),
                preferred_colors=data.get('preferred_colors', ''),
                has_logo=data.get('has_logo', False),
                currency=deployment_fee['currency'],
                deployment_fee=deployment_fee['amount'],
                status='GENERATED'
            )
            
            return Response({
                'status': 'success',
                'message': 'Proposal generated successfully',
                'proposal_id': proposal_request.id,
                'deployment_fee': deployment_fee,
                'data': ProposalRequestSerializer(proposal_request).data
            })
            
        except Exception as e:
            print(f"Proposal generator error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ============================================================================
# PLATFORM DEMO SIMULATOR VIEWS
# ============================================================================

class PlatformDemoView(APIView):
    """
    Interactive Platform Demo Simulator
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Generate platform preview based on branding"""
        try:
            data = request.data
            
            # Default values
            institution_name = data.get('institution_name', 'Your Institution')
            primary_color = data.get('primary_color', '#1A237E')
            secondary_color = data.get('secondary_color', '#00C853')
            accent_color = data.get('accent_color', '#7B1FA2')
            
            # Module selections
            ctb_enabled = data.get('ctb_enabled', True)
            live_classes_enabled = data.get('live_classes_enabled', False)
            
            # Create demo session
            demo_session = {
                'session_id': str(uuid.uuid4()),
                'institution_name': institution_name,
                'branding': {
                    'primary_color': primary_color,
                    'secondary_color': secondary_color,
                    'accent_color': accent_color,
                },
                'modules': {
                    'ctb': ctb_enabled,
                    'live_classes': live_classes_enabled
                },
                'created_at': timezone.now().isoformat(),
                'expires_at': (timezone.now() + timedelta(hours=24)).isoformat()
            }
            
            return Response({
                'status': 'success',
                'demo_session': demo_session,
                'message': 'Platform demo generated successfully'
            })
            
        except Exception as e:
            print(f"Demo generator error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ============================================================================
# CURRENCY & LOCALIZATION VIEWS
# ============================================================================

class CurrencyDetectView(APIView):
    """Detect user currency and location"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        location_data = detect_user_location(request)
        
        # Calculate deployment fee for this location
        deployment_fee = calculate_deployment_fee(location_data['country'])
        
        return Response({
            'currency': location_data['currency'],
            'country': location_data['country'],
            'deployment_fee': deployment_fee,
            'pricing_model': 'One-time deployment fee (no monthly subscriptions)'
        })

# ============================================================================
# HEALTH CHECK VIEW
# ============================================================================

class HealthCheckView(APIView):
    """System health check"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'chatbot': 'active',
                'proposal_generator': 'active',
                'demo_simulator': 'active'
            },
            'pricing_model': 'One-time deployment fee'
        })

# ============================================================================
# API ROOT VIEW
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    """API root endpoint with documentation"""
    base_url = request.build_absolute_uri('/')
    
    endpoints = {
        'features': {
            'url': f"{base_url}api/features/",
            'methods': ['GET'],
            'description': 'Platform features by category'
        },
        'testimonials': {
            'url': f"{base_url}api/testimonials/",
            'methods': ['GET'],
            'description': 'Client testimonials'
        },
        'chatbot': {
            'url': f"{base_url}api/chat/send/",
            'methods': ['POST'],
            'description': 'AI chatbot (JN Assistant)'
        },
        'proposal_generator': {
            'url': f"{base_url}api/proposals/generate/",
            'methods': ['POST'],
            'description': 'Generate custom proposals with one-time deployment fee'
        },
        'demo_simulator': {
            'url': f"{base_url}api/demo/platform/",
            'methods': ['POST'],
            'description': 'Interactive platform demo'
        },
        'currency_detection': {
            'url': f"{base_url}api/currency/detect/",
            'methods': ['GET'],
            'description': 'Detect user currency and location with deployment fee'
        },
        'health_check': {
            'url': f"{base_url}api/health/",
            'methods': ['GET'],
            'description': 'System health check'
        }
    }
    
    return Response({
        'api_name': 'JavaNet EdTech Suite API',
        'version': '1.0.0',
        'endpoints': endpoints,
        'status': 'operational',
        'timestamp': timezone.now().isoformat(),
        'pricing_model': 'One-time deployment fee (₦5-10M for Africa, $10K for International)'
    })