from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatSession, ChatMessage, ChatbotConfig, Intent
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from django.shortcuts import get_object_or_404
from openai import OpenAI
import json
from django.conf import settings
from datetime import datetime
import uuid
import re

class ChatSessionListView(APIView):
    """List chat sessions (admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        sessions = ChatSession.objects.all().order_by('-last_activity')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data)

class ChatSessionDetailView(APIView):
    """Get specific chat session details"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)


class ChatbotView(APIView):
    """Handle chatbot messages using JSON knowledge base with conversation state"""
    permission_classes = [permissions.AllowAny]
    
    def load_knowledge_base(self):
        """Load chatbot knowledge base from database or default JSON"""
        try:
            config = ChatbotConfig.objects.filter(is_active=True).first()
            if config:
                return config.intents
        except:
            pass
        
        # Fallback to JSON structure
        return [
            {
                "tag": "about_javanet",
                "patterns": [
                    "What is JavaNet edTech Suite?",
                    "Tell me about JavaNet",
                    "What does your platform do?",
                    "JavaNet edtech",
                    "JavaNet ict",
                    "JavaNet software"
                ],
                "responses": [
                    "JavaNet edTech Suite is an all-in-one education technology platform combining CBT-based assessment, Live Interactive Virtual Classroom, E-Library, AI-powered learning support, and school management tools. We deploy fully branded platforms for schools and education businesses with a one-time license."
                ],
                "followups": ["user_type"],
                "next_step": "user_type"
            },
            {
                "tag": "school_type",
                "patterns": [
                    "I am a school",
                    "School",
                    "Secondary school",
                    "Primary school",
                    "High school",
                    "K-12 school"
                ],
                "responses": [
                    "Perfect! Schools love our platform. JavaNet edTech Suite helps you conduct secure CBT exams, teach online, manage students, and publish digital learning content under your own school brand.\n\nAre you interested mainly in CBT exams, online classes, or both?"
                ],
                "followups": ["cbt_exams", "online_classes", "both_platforms", "school_branding"]
            },
            {
                "tag": "training_type",
                "patterns": [
                    "Training center",
                    "Training Centre",
                    "Training institute",
                    "Training academy",
                    "Vocational center",
                    "I am a training center"
                ],
                "responses": [
                    "Great choice! Training centers thrive with our platform. Deploy your own branded online academy with CBT testing, live classes, certificates, and comprehensive student management.\n\nDo you issue certificates after training?"
                ],
                "followups": ["certificates_yes", "certificates_no", "cbt_training", "training_demo"]
            },
            {
                "tag": "university_type",
                "patterns": [
                    "University",
                    "College",
                    "Higher institution",
                    "Polytechnic",
                    "I am a university"
                ],
                "responses": [
                    "Excellent! Universities benefit from our large-scale platform. We support online examinations, virtual lectures, e-library systems, and result processing specifically designed for higher education institutions.\n\nHow many faculties will be using the platform?"
                ],
                "followups": ["faculties_1_3", "faculties_4_10", "faculties_10plus", "university_demo"]
            },
            {
                "tag": "government_type",
                "patterns": [
                    "Government",
                    "Government agency",
                    "Exam body",
                    "Ministry of education",
                    "I am a government institution"
                ],
                "responses": [
                    "Perfect for government needs! Our platform supports nationwide CBT exams, secure candidate registration, and detailed analytics for government and examination bodies.\n\nIs this for state-wide or national deployment?"
                ],
                "followups": ["state_wide", "national", "regional", "government_security"]
            },
            {
                "tag": "company_type",
                "patterns": [
                    "Education company",
                    "EdTech company",
                    "Business",
                    "Enterprise",
                    "Startup",
                    "I am an education company"
                ],
                "responses": [
                    "Ideal for education businesses! Get a complete white-label education platform to offer online learning and testing services under your own brand with revenue sharing options.\n\nWhat is your target student capacity?"
                ],
                "followups": ["capacity_1000", "capacity_5000", "capacity_10000", "white_label_demo"]
            },
            {
                "tag": "modules",
                "patterns": [
                    "What modules are included?",
                    "Features",
                    "What do I get?",
                    "Platform features",
                    "Modules",
                    "What are the modules"
                ],
                "responses": [
                    "The JavaNet edTech Suite includes:\n\n1. **JN Assess**: A comprehensive CBT-based testing platform\n2. **JN Learning**: Live Interactive Virtual Classroom & Teacher-Student matching system\n3. **E-Library**: Digital content management system\n4. **AI Learning Support**: Personalized learning assistance\n5. **School Management Tools**: Complete administrative system\n\nAll modules can be fully customized and branded for your institution."
                ],
                "followups": ["priority_module"],
                "next_step": "priority_module"
            },
            {
                "tag": "priority_module",
                "patterns": [
                    "CBT",
                    "Virtual classroom",
                    "Both",
                    "All",
                    "Testing platform",
                    "Online classes",
                    "Assess",
                    "Learning"
                ],
                "responses": [
                    "Excellent! That module can be fully customized and branded for you. Would you like to know more about our pricing?"
                ],
                "followups": ["pricing"],
                "next_step": "pricing"
            },
            {
                "tag": "pricing",
                "patterns": [
                    "How much",
                    "Cost",
                    "Price",
                    "Pricing",
                    "Fee",
                    "How much does it cost",
                    "Deployment fee"
                ],
                "responses": [
                    "We offer flexible pricing based on your location and requirements:\n\n**For Africa (Nigeria, Ghana, etc.):**\n• One-time license fee: ₦5,000,000 – ₦7,500,000\n\n**International Pricing (USA, UK, Canada, etc.):**\n• One-time license fee: $10,000 – $25,000\n\nThese are one-time fees with no monthly subscriptions. Would you like to know which price range applies to your location?"
                ],
                "followups": ["deployment_country", "generate_proposal", "demo"],
                "next_step": "deployment_country"
            },
            {
                "tag": "deployment_country",
                "patterns": [
                    "Nigeria",
                    "Ghana",
                    "UK",
                    "USA",
                    "Other",
                    "Canada",
                    "Europe",
                    "Africa",
                    "Kenya",
                    "South Africa"
                ],
                "responses": [
                    "Thank you! Approximately how many users (students, teachers, administrators) will you start with?"
                ],
                "followups": ["user_volume"],
                "next_step": "user_volume"
            },
            {
                "tag": "user_volume",
                "patterns": [
                    "500",
                    "1000",
                    "5000",
                    "Not sure",
                    "2000",
                    "10000",
                    "Less than 500",
                    "3000",
                    "5",
                    "10",
                    "50",
                    "100",
                    "200",
                    "5 faculties",
                    "10 faculties"
                ],
                "responses": [
                    "Noted. Would you like to see a live demo of our platform?"
                ],
                "followups": ["demo"],
                "next_step": "demo"
            },
            {
                "tag": "demo",
                "patterns": [
                    "Yes",
                    "Show demo",
                    "View demo",
                    "Demo",
                    "I want to see demo",
                    "Show me demo links"
                ],
                "responses": [
                    "Great! You can view our live demos here:\n\n🎓 **JN Learning Demo** (Virtual Classroom):\nhttps://www.ischool.ng/ole_home\n\n📝 **JN Assess Demo** (CBT Testing):\nhttps://www.ischool.ng/ola_home\n\nWould you like a guided walkthrough with our sales team?"
                ],
                "followups": ["lead_capture", "generate_proposal"],
                "next_step": "lead_capture",
                "flags": ["demo_shown"]
            },
            {
                "tag": "demo_yes",
                "patterns": [
                    "Yes I want walkthrough",
                    "Yes walkthrough",
                    "I want guided walkthrough",
                    "Yes with sales team"
                ],
                "responses": [
                    "Perfect! Here's how to contact our sales team:\n\n📱 **WhatsApp:** +2347030673089\n📞 **Phone:** +2349128688164\n📧 **Email:** info@javanetict.com\n\nYou can also schedule a call or request a personalized demo."
                ],
                "followups": [],
                "requires_previous": "demo"
            },
            {
                "tag": "lead_capture",
                "patterns": [
                    "Contact me",
                    "Talk to sales",
                    "Schedule meeting",
                    "Get quote",
                    "Proposal",
                    "Talk to sales team",
                    "Sales team",
                    "Contact sales"
                ],
                "responses": [
                    "Perfect! Here are our contact details:\n\n📱 **WhatsApp:** +2347030673089\n📞 **Phone:** +2349128688164\n📧 **Email:** info@javanetict.com\n\nWe're available Monday to Friday, 8am to 6pm Nigeria time."
                ],
                "followups": []
            },
            {
                "tag": "generate_proposal",
                "patterns": [
                    "Generate proposal",
                    "Create proposal",
                    "I want proposal",
                    "Get proposal",
                    "Proposal form",
                    "Custom quote",
                    "Price quote",
                    "Generate quote"
                ],
                "responses": [
                    "Great! You can generate a customized proposal using our proposal generator:\n\n📋 **Proposal Generator:**\nhttps://www.javanetict.com/proposal\n\n**What you can do there:**\n• Select which platform(s) you need\n• Specify user counts and requirements\n• Get detailed pricing breakdown\n• Download or share the proposal\n\nAfter generating your proposal, you can discuss it with our sales team."
                ],
                "followups": ["lead_capture", "demo"],
                "next_step": "lead_capture"
            },
            {
                "tag": "schedule_call",
                "patterns": [
                    "Schedule call",
                    "Book a call",
                    "Schedule meeting",
                    "Arrange call",
                    "Schedule a call",
                    "Schedule a call: +2349128688164",
                    "+2349128688164",
                    "Call sales",
                    "Phone sales",
                    "Make a call"
                ],
                "responses": [
                    "Great! Here are our contact details for scheduling:\n\n📱 **WhatsApp:** +2347030673089\n📞 **Phone:** +2349128688164\n\nYou can call us directly or message on WhatsApp to schedule:\n• Product demo\n• Technical consultation\n• Custom solution discussion\n• Implementation planning"
                ],
                "followups": ["send_email", "whatsapp_contact"]
            },
            {
                "tag": "send_email",
                "patterns": [
                    "Send email",
                    "Email",
                    "Email address",
                    "Contact email",
                    "Sales email",
                    "Email sales",
                    "Email: info@javanetict.com",
                    "info@javanetict.com",
                    "Send mail"
                ],
                "responses": [
                    "You can email us at:\n\n📧 **Email:** info@javanetict.com\n\n**What to include in your email:**\n• Your organization name\n• Contact person details\n• Brief description of your needs\n• Preferred contact method\n\nWe typically respond within 24 hours during business days."
                ],
                "followups": ["whatsapp_contact", "schedule_call"],
                "next_step": "whatsapp_contact"
            },
            {
                "tag": "whatsapp_contact",
                "patterns": [
                    "WhatsApp",
                    "WhatsApp contact",
                    "Chat on WhatsApp",
                    "Message on WhatsApp",
                    "WhatsApp: +2347030673089",
                    "+2347030673089",
                    "WhatsApp chat"
                ],
                "responses": [
                    "📱 **WhatsApp:** +2347030673089\n\nClick the link below to start chatting with our sales team directly on WhatsApp:\nhttps://wa.me/2347030673089\n\nWe're available Monday to Friday, 8am to 6pm Nigeria time."
                ],
                "followups": ["send_email", "schedule_call"]
            },
            {
                "tag": "cbt_tests",
                "patterns": [
                    "CBT Tests",
                    "CBT exams",
                    "Online tests",
                    "Computer based tests",
                    "CBT",
                    "Tests",
                    "Exams"
                ],
                "responses": [
                    "Our **JN Assess** module is perfect for CBT tests and exams. Features include:\n• Secure online exam delivery\n• Question randomization\n• Instant result processing\n• Offline exam capability\n• Detailed analytics and reporting\n\nWould you like to see the CBT demo or get pricing details?"
                ],
                "followups": ["demo", "pricing", "generate_proposal"]
            },
            {
                "tag": "virtual_classroom",
                "patterns": [
                    "Live Virtual Classroom",
                    "Online classes",
                    "Virtual lectures",
                    "Live teaching",
                    "Virtual classroom",
                    "Classroom",
                    "Online teaching"
                ],
                "responses": [
                    "Our **JN Learning** module provides a complete virtual classroom solution:\n• Live interactive video classes\n• Digital whiteboard and screen sharing\n• Teacher-student matching\n• Assignment management\n• Parent portal access\n\nWould you like to see the virtual classroom demo?"
                ],
                "followups": ["demo", "pricing", "generate_proposal"]
            },
            {
                "tag": "greeting",
                "patterns": [
                    "Hi",
                    "Hello",
                    "Hey",
                    "Good morning",
                    "Good afternoon",
                    "Good evening"
                ],
                "responses": [
                    "Hello! 👋 I'm JN Assistant from JavaNet edTech Suite. I can help you learn about our all-in-one education platform with CBT testing, virtual classrooms, and school management tools. How can I assist you today?"
                ],
                "followups": ["about_javanet", "modules", "pricing", "generate_proposal"],
                "next_step": "about_javanet"
            },
            {
                "tag": "goodbye",
                "patterns": [
                    "Bye",
                    "Goodbye",
                    "See you",
                    "Thanks",
                    "Thank you",
                    "That's all"
                ],
                "responses": [
                    "You're welcome! 🎓\n\n**Next Steps:**\n• View demos: https://www.ischool.ng\n• Generate proposal: https://www.javanetict.com/proposal\n• Contact us: +2347030673089 (WhatsApp)\n\nHave a great day! 👋"
                ],
                "followups": []
            }
        ]
    
    def get_conversation_state(self, session_id):
        """Get or create conversation state for the session"""
        try:
            session, created = ChatSession.objects.get_or_create(
                session_id=session_id,
                defaults={'conversation_state': {}}
            )
            return session.conversation_state or {}
        except:
            return {}
    
    def update_conversation_state(self, session_id, updates):
        """Update conversation state"""
        try:
            session = ChatSession.objects.get(session_id=session_id)
            state = session.conversation_state or {}
            state.update(updates)
            session.conversation_state = state
            session.save()
            return True
        except:
            return False
    
    def is_javanet_related(self, user_message):
        """Check if the user message is related to JavaNet edTech Suite"""
        user_msg_lower = user_message.lower()
        
        # Always allow sales/contact related messages
        sales_keywords = [
            'schedule', 'call', 'phone', '+2349128688164', '+2347030673089',
            'whatsapp', 'email', 'info@javanetict.com', 'contact', 'sales',
            'talk to', 'meeting', 'book', 'arrange', 'discuss'
        ]
        
        for keyword in sales_keywords:
            if keyword in user_msg_lower:
                return True
        
        # JavaNet specific keywords
        javanet_keywords = [
            'javanet', 'edtech', 'cbt', 'test', 'exam', 'virtual', 'classroom',
            'learning', 'assess', 'school', 'university', 'training', 'government',
            'company', 'price', 'cost', 'fee', 'module', 'feature', 'demo',
            'proposal', 'platform', 'software', 'system', 'online', 'education',
            'teaching', 'student', 'teacher', 'faculty', 'institution', 'academy',
            'center', 'how much', 'what is', 'tell me', 'show me', 'help',
            'faculties', 'users', 'students', 'nigeria', 'ghana', 'uk', 'usa',
            'country', 'deployment', 'implementation'
        ]
        
        for keyword in javanet_keywords:
            if keyword in user_msg_lower:
                return True
        
        # Check if it's a number (for user/faculty count)
        if user_msg_lower.strip().isdigit():
            return True
        
        # Check if it's a greeting
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        for greeting in greetings:
            if greeting in user_msg_lower:
                return True
        
        # Check if it's a goodbye
        goodbyes = ['bye', 'goodbye', 'thanks', 'thank you', 'that\'s all']
        for goodbye in goodbyes:
            if goodbye in user_msg_lower:
                return True
        
        return False
    
    def extract_user_info(self, user_message, conversation_state):
        """Extract and store user information from messages"""
        user_message_lower = user_message.lower()
        
        # Extract industry type
        industry_keywords = {
            'school': ['school', 'secondary', 'primary'],
            'university': ['university', 'college', 'faculty', 'campus'],
            'training': ['training', 'academy', 'tutor', 'coach', 'training center'],
            'government': ['government', 'ministry', 'public', 'state'],
            'company': ['company', 'business', 'enterprise', 'startup']
        }
        
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in user_message_lower:
                    conversation_state['user_industry'] = industry
                    break
        
        # Extract country
        countries = ['nigeria', 'ghana', 'usa', 'uk', 'canada', 'kenya', 'south africa']
        for country in countries:
            if country in user_message_lower:
                conversation_state['user_country'] = country.title()
                break
        
        # Extract user volume (numbers)
        numbers = re.findall(r'\d+', user_message)
        if numbers:
            conversation_state['user_volume'] = numbers[0]
            
            # Check if it's faculty count (university context)
            if conversation_state.get('last_intent') == 'university_type':
                conversation_state['faculty_count'] = numbers[0]
        
        return conversation_state
    
    def get_intent(self, user_message, knowledge_base, conversation_state):
        """Match user message to an intent with conversation context"""
        user_message_lower = user_message.lower().strip()
        
        # First, check if this is related to JavaNet
        if not self.is_javanet_related(user_message):
            return None
        
        # Check conversation state for progression
        demo_shown = conversation_state.get('demo_shown', False)
        last_intent = conversation_state.get('last_intent')
        
        # SPECIAL FIX: If last intent was sales-related, handle schedule/call queries
        if last_intent in ['lead_capture', 'demo_yes', 'send_email', 'whatsapp_contact', 'schedule_call']:
            # Check for schedule/call keywords in the context of sales follow-up
            if any(keyword in user_message_lower for keyword in [
                'schedule', 'call', 'phone', '+2349128688164', '+2347030673089',
                'whatsapp', 'email', 'info@javanetict.com', 'contact', 'sales'
            ]):
                # Return appropriate intent based on content
                if 'schedule' in user_message_lower or 'call' in user_message_lower:
                    for intent in knowledge_base:
                        if intent['tag'] == 'schedule_call':
                            return intent
                elif 'whatsapp' in user_message_lower:
                    for intent in knowledge_base:
                        if intent['tag'] == 'whatsapp_contact':
                            return intent
                elif 'email' in user_message_lower or 'info@javanetict.com' in user_message_lower:
                    for intent in knowledge_base:
                        if intent['tag'] == 'send_email':
                            return intent
                else:
                    # Default to lead capture for other sales-related queries
                    for intent in knowledge_base:
                        if intent['tag'] == 'lead_capture':
                            return intent
        
        # Special handling for walkthrough after demo
        if demo_shown and any(phrase in user_message_lower for phrase in [
            'yes i want walkthrough', 'yes walkthrough', 'i want guided', 
            'with sales team', 'walkthrough'
        ]):
            for intent in knowledge_base:
                if intent['tag'] == 'demo_yes':
                    return intent
        
        # Handle faculty numbers for universities
        if last_intent == 'university_type' and user_message_lower.isdigit():
            for intent in knowledge_base:
                if intent['tag'] == 'user_volume':
                    return intent
        
        # Check for exact pattern matches first
        for intent in knowledge_base:
            for pattern in intent['patterns']:
                pattern_lower = pattern.lower()
                if (pattern_lower == user_message_lower or 
                    pattern_lower in user_message_lower or 
                    user_message_lower in pattern_lower):
                    
                    # Don't show demo again if it was already shown
                    if intent['tag'] == 'demo' and demo_shown:
                        # Instead, redirect to lead capture
                        for next_intent in knowledge_base:
                            if next_intent['tag'] == 'lead_capture':
                                return next_intent
                    return intent
        
        # Check for keyword matches with priority
        keyword_to_intent = {
            'javanet': 'about_javanet',
            'what is': 'about_javanet',
            'tell me about': 'about_javanet',
            'school': 'school_type',
            'university': 'university_type',
            'college': 'university_type',
            'training center': 'training_type',
            'training centre': 'training_type',
            'training': 'training_type',
            'academy': 'training_type',
            'government': 'government_type',
            'ministry': 'government_type',
            'company': 'company_type',
            'business': 'company_type',
            'startup': 'company_type',
            'module': 'modules',
            'feature': 'modules',
            'include': 'modules',
            'what do i get': 'modules',
            'cbt test': 'cbt_tests',
            'cbt exam': 'cbt_tests',
            'cbt': 'cbt_tests',
            'test': 'cbt_tests',
            'exam': 'cbt_tests',
            'assess': 'cbt_tests',
            'virtual classroom': 'virtual_classroom',
            'live virtual': 'virtual_classroom',
            'virtual': 'virtual_classroom',
            'classroom': 'virtual_classroom',
            'learning': 'virtual_classroom',
            'online class': 'virtual_classroom',
            'price': 'pricing',
            'cost': 'pricing',
            'how much': 'pricing',
            'fee': 'pricing',
            'deployment fee': 'pricing',
            'nigeria': 'deployment_country',
            'ghana': 'deployment_country',
            'usa': 'deployment_country',
            'uk': 'deployment_country',
            'canada': 'deployment_country',
            'user': 'user_volume',
            'student': 'user_volume',
            'how many': 'user_volume',
            'faculty': 'user_volume',
            'faculties': 'user_volume',
            'demo': 'demo',
            'show': 'demo',
            'view': 'demo',
            'link': 'demo',
            'contact': 'lead_capture',
            'sales': 'lead_capture',
            'talk to': 'lead_capture',
            'meeting': 'schedule_call',
            'quote': 'generate_proposal',
            'proposal': 'generate_proposal',
            'generate': 'generate_proposal',
            'create': 'generate_proposal',
            'custom quote': 'generate_proposal',
            'email': 'send_email',
            'send email': 'send_email',
            'info@javanetict.com': 'send_email',
            'whatsapp': 'whatsapp_contact',
            'chat': 'whatsapp_contact',
            'message': 'whatsapp_contact',
            'schedule': 'schedule_call',
            'call': 'schedule_call',
            'book': 'schedule_call',
            'phone': 'schedule_call',
            '+2349128688164': 'schedule_call',
            '+2347030673089': 'whatsapp_contact',
            'hi': 'greeting',
            'hello': 'greeting',
            'hey': 'greeting',
            'good morning': 'greeting',
            'good afternoon': 'greeting',
            'good evening': 'greeting',
            'bye': 'goodbye',
            'goodbye': 'goodbye',
            'thank': 'goodbye',
            'thanks': 'goodbye'
        }
        
        # Check keywords in order of priority (longer phrases first)
        sorted_keywords = sorted(keyword_to_intent.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in user_message_lower:
                for intent in knowledge_base:
                    if intent['tag'] == keyword_to_intent[keyword]:
                        return intent
        
        # Default to greeting if no match but it's JavaNet related
        for intent in knowledge_base:
            if intent['tag'] == 'greeting':
                return intent
        
        return None
    
    def get_followup_suggestions(self, intent, knowledge_base, conversation_state):
        """Get context-aware followup suggestions - FIXED DUPLICATES"""
        suggestions = []
        
        # Special handling for modules intent
        if intent['tag'] == 'modules':
            suggestions = [
                'CBT Tests',
                'Live Virtual Classroom',
                'Generate Proposal'
            ]
        
        # Special handling for demo intent
        elif intent['tag'] == 'demo':
            conversation_state['demo_shown'] = True
            self.update_conversation_state(
                conversation_state.get('session_id', 'default'),
                {'demo_shown': True}
            )
            
            # After showing demo, suggest sales contact and proposal
            suggestions = [
                'Talk to sales team',
                'Generate proposal'
            ]
        
        elif intent['tag'] == 'generate_proposal':
            # After proposal generation, suggest next steps
            suggestions = [
                'Discuss with sales team',
                'View demo links'
            ]
        
        elif intent['tag'] == 'lead_capture' or intent['tag'] == 'demo_yes':
            # After lead capture, suggest contact methods
            suggestions = [
                'Schedule a call',
                'WhatsApp chat',
                'Send email'
            ]
        
        elif intent['tag'] == 'pricing':
            # After pricing, suggest proposal and demo
            suggestions = [
                'Generate proposal',
                'Show me demo links'
            ]
        
        elif intent['tag'] == 'send_email':
            # After email request, show contact options
            suggestions = [
                'WhatsApp chat',
                'Schedule a call',
                'Talk to sales team'
            ]
        
        elif intent['tag'] == 'whatsapp_contact':
            # After WhatsApp, show other contact methods
            suggestions = [
                'Send email',
                'Schedule a call',
                'Talk to sales team'
            ]
        
        elif intent['tag'] == 'schedule_call':
            # After schedule call, show direct contact
            suggestions = [
                'WhatsApp chat',
                'Send email',
                'Talk to sales team'
            ]
        
        elif intent['tag'] == 'cbt_tests':
            # After CBT tests, show relevant options
            suggestions = [
                'Virtual Classroom',
                'Generate Proposal',
                'View CBT Demo'
            ]
        
        elif intent['tag'] == 'virtual_classroom':
            # After virtual classroom, show relevant options
            suggestions = [
                'CBT Tests',
                'Generate Proposal',
                'View Classroom Demo'
            ]
        
        elif intent['tag'] == 'user_volume':
            # Check context for university faculty count
            last_intent = conversation_state.get('last_intent')
            if last_intent == 'university_type':
                suggestions = ['Show me demo links', 'Generate proposal', 'Talk to sales team']
            else:
                suggestions = ['Show me demo links', 'Generate proposal']
        
        elif intent['tag'] == 'about_javanet' or intent['tag'] == 'greeting':
            # For greeting and about, show main options
            suggestions = [
                'What modules are included?',
                'How much does it cost?',
                'Generate Proposal'
            ]
        
        else:
            # Default behavior for other intents
            for followup_tag in intent.get('followups', []):
                for followup_intent in knowledge_base:
                    if followup_intent['tag'] == followup_tag:
                        if followup_intent['patterns']:
                            suggestion = followup_intent['patterns'][0]
                            # Don't add duplicates
                            if suggestion not in suggestions:
                                suggestions.append(suggestion)
                        break
        
        # Remove duplicates while preserving order (case-insensitive)
        seen = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            # Normalize for comparison
            normalized = suggestion.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_suggestions.append(suggestion)
        
        # Ensure we don't have "Generate Proposal" and "Generate proposal" as duplicates
        final_suggestions = []
        generate_proposal_added = False
        
        for suggestion in unique_suggestions:
            normalized = suggestion.lower().strip()
            if normalized == 'generate proposal' or normalized == 'generate proposal':
                if not generate_proposal_added:
                    # Use consistent casing: "Generate Proposal"
                    final_suggestions.append('Generate Proposal')
                    generate_proposal_added = True
            else:
                final_suggestions.append(suggestion)
        
        return final_suggestions[:3]  # Limit to 3 suggestions
    
    def get_personalized_proposal_response(self, conversation_state):
        """Generate personalized proposal response based on conversation"""
        if not all(key in conversation_state for key in ['user_industry', 'user_country']):
            return None
        
        industry = conversation_state.get('user_industry', 'school').title()
        country = conversation_state.get('user_country', 'Nigeria')
        volume = conversation_state.get('user_volume', '500')
        
        # Create personalized message
        response = "\n\n🎯 **Based on our conversation:**\n"
        response += f"• Industry: {industry}\n"
        response += f"• Location: {country}\n"
        
        if volume:
            response += f"• Estimated Users: {volume}\n"
        
        response += f"\n💡 **Personalized Proposal Link:**\n"
        response += f"https://www.javanetict.com/proposal?industry={industry.lower()}&country={country.lower()}"
        
        if volume:
            response += f"&users={volume}"
        
        response += "\n\nThis link will pre-fill your information for faster proposal generation!"
        
        return response
    
    def post(self, request):
        try:
            data = request.data
            user_message = data.get('message', '').strip()
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            if not user_message:
                return Response({
                    'error': 'Message cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get current timestamp
            current_time = datetime.now().isoformat()
            
            # Load knowledge base
            knowledge_base = self.load_knowledge_base()
            
            # Get conversation state
            conversation_state = self.get_conversation_state(session_id)
            conversation_state['session_id'] = session_id
            
            # First, check if this is JavaNet related
            if not self.is_javanet_related(user_message):
                # Out of scope response
                response_text = "I'm sorry, that's outside the scope of this conversation about JavaNet edTech Suite.\n\nPlease contact our sales team for assistance with other inquiries:\n\n📱 **WhatsApp:** +2347030673089\n📞 **Phone:** +2349128688164\n📧 **Email:** info@javanetict.com\n\nHow can I help you with JavaNet edTech Suite?"
                followup_suggestions = [
                    "What is JavaNet edTech Suite?",
                    "What modules are included?",
                    "Generate proposal",
                    "Show me demo links"
                ]
                
                return Response({
                    'response': response_text,
                    'timestamp': current_time,
                    'context': {
                        'last_intent': 'out_of_scope',
                        'followup_suggestions': followup_suggestions,
                        'message_id': str(uuid.uuid4()),
                        'timestamp': current_time,
                        'conversation_state': conversation_state,
                        'session_id': session_id
                    },
                    'suggestions': followup_suggestions,
                    'intent': 'out_of_scope',
                    'session_id': session_id
                }, status=status.HTTP_200_OK)
            
            # Extract user information from message
            conversation_state = self.extract_user_info(user_message, conversation_state)
            
            # Get matching intent with context
            intent = self.get_intent(user_message, knowledge_base, conversation_state)
            
            if not intent:
                # Fallback response for JavaNet related but no intent match
                response_text = "I'm here to help you with JavaNet edTech Suite! You can ask me about:\n\n• What JavaNet is\n• Available modules and features\n• Pricing for different regions\n• Live demos\n• Generating custom proposals\n• Contacting our sales team\n\nWhat would you like to know?"
                followup_suggestions = [
                    "What is JavaNet edTech Suite?",
                    "What modules are included?",
                    "Generate proposal",
                    "Show me demo links"
                ]
            else:
                # Get response from intent
                response_text = intent['responses'][0] if intent['responses'] else "I understand. How can I help you further?"
                
                # Add personalized proposal info if relevant
                if intent['tag'] == 'generate_proposal':
                    personalized = self.get_personalized_proposal_response(conversation_state)
                    if personalized:
                        response_text += personalized
                
                # Customize response for user volume/faculty count
                if user_message.isdigit():
                    user_count = int(user_message)
                    # Check if this is in university context
                    last_intent = conversation_state.get('last_intent')
                    if last_intent == 'university_type':
                        if user_count <= 3:
                            response_text += "\n\nPerfect! We have specialized packages for smaller universities."
                        elif user_count <= 10:
                            response_text += "\n\nExcellent! That's an ideal size for our platform's capabilities."
                        else:
                            response_text += "\n\nGreat! We specialize in large-scale university deployments with multi-faculty support."
                    else:
                        if user_count < 500:
                            response_text += "\n\nPerfect! We have packages specifically designed for smaller institutions."
                        elif user_count <= 5000:
                            response_text += "\n\nGreat! That's a typical size we work with. Our platform scales perfectly for your needs."
                        else:
                            response_text += "\n\nExcellent! We specialize in large-scale deployments and can ensure optimal performance."
                
                # Get context-aware followup suggestions
                followup_suggestions = self.get_followup_suggestions(intent, knowledge_base, conversation_state)
                
                # Update conversation state
                state_updates = {
                    'last_intent': intent['tag'],
                    'last_interaction': current_time,
                    'message_count': conversation_state.get('message_count', 0) + 1
                }
                
                if 'flags' in intent:
                    for flag in intent['flags']:
                        state_updates[flag] = True
                
                if intent['tag'] == 'demo':
                    state_updates['demo_shown'] = True
                elif intent['tag'] == 'demo_yes' or intent['tag'] == 'lead_capture':
                    state_updates['ready_for_sales'] = True
                elif intent['tag'] == 'generate_proposal':
                    state_updates['proposal_requested'] = True
                
                self.update_conversation_state(session_id, state_updates)
            
            # Prepare conversation context
            conversation_context = {
                'last_intent': intent['tag'] if intent else 'unknown',
                'followup_suggestions': followup_suggestions,
                'message_id': str(uuid.uuid4()),
                'timestamp': current_time,
                'conversation_state': conversation_state,
                'session_id': session_id
            }
            
            return Response({
                'response': response_text,
                'timestamp': current_time,
                'context': conversation_context,
                'suggestions': followup_suggestions,
                'intent': intent['tag'] if intent else 'unknown',
                'session_id': session_id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)