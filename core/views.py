from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import EmailMessage  # Use EmailMessage instead of send_mail
from django.conf import settings
from .models import Feature, Testimonial, Client, Contact
from .serializers import FeatureSerializer, TestimonialSerializer, ClientSerializer, ContactSerializer

# Add this new viewset for contact submissions
class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for contact form submissions"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to submit contact form
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the contact submission
        self.perform_create(serializer)
        
        # Send email notification to admin using EmailMessage
        try:
            subject = f"New Contact Form Submission: {serializer.validated_data['subject']}"
            message = f"""
            Name: {serializer.validated_data['name']}
            Email: {serializer.validated_data['email']}
            Phone: {serializer.validated_data.get('phone', 'Not provided')}
            Institution: {serializer.validated_data.get('institution', 'Not provided')}
            Subject: {serializer.validated_data['subject']}
            
            Message:
            {serializer.validated_data['message']}
            
            ---
            Submitted at: {serializer.instance.created_at.strftime('%Y-%m-%d %H:%M:%S') if serializer.instance else 'N/A'}
            """
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],  # Admin email to receive notifications
                reply_to=[serializer.validated_data['email']],  # Reply to the person who submitted
            )
            
            # Optional: Add headers
            email.extra_headers = {
                'X-Priority': '1',  # High priority
                'X-Mailer': 'JavaNet EdTech Contact Form',
            }
            
            # Send the email
            email.send(fail_silently=False)
            print(f"✅ Contact form email sent successfully to {settings.CONTACT_EMAIL}")
            
        except Exception as e:
            # Log email error but don't fail the request
            print(f"❌ Email notification failed: {e}")
            import traceback
            traceback.print_exc()  # Print full traceback for debugging
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                'message': 'Message sent successfully! We will get back to you within 24 hours.',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def get_permissions(self):
        """Only allow authenticated users to view/list contacts"""
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        else:
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()

# Keep your existing viewsets
class FeatureViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for features"""
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def ctb_features(self, request):
        features = Feature.objects.filter(feature_type='ctb').order_by('order')
        serializer = self.get_serializer(features, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def live_features(self, request):
        features = Feature.objects.filter(feature_type='LIVE').order_by('order')
        serializer = self.get_serializer(features, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def general_features(self, request):
        features = Feature.objects.filter(feature_type='GEN').order_by('order')
        serializer = self.get_serializer(features, many=True)
        return Response(serializer.data)

class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for testimonials"""
    queryset = Testimonial.objects.filter(is_featured=True)
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]

class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet for clients (admin only)"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAdminUser]