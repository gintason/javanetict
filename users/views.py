from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
import traceback
from django.core.mail import EmailMessage

from .models import CustomUser, UserActivity
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    UserActivitySerializer, PasswordChangeSerializer, ProfileUpdateSerializer
)

def track_activity(user, action, details=None, request=None):
    """Helper function to track user activities"""
    UserActivity.objects.create(
        user=user,
        action=action,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else None
    )

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Track activity
        track_activity(user, 'REGISTER', {'method': 'email'}, request)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find user by email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check password directly (bypass Django's authenticate)
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Track activity
        track_activity(user, 'LOGIN', {}, request)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Track activity
            track_activity(request.user, 'LOGOUT', {}, request)
            
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        # Track activity
        track_activity(request.user, 'PROFILE_UPDATE', request.data, request)
        
        response = super().update(request, *args, **kwargs)
        return response

class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Track activity
        track_activity(user, 'PASSWORD_CHANGE', {}, request)
        
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

class UserActivityView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)

class CheckAuthView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user is authenticated via JWT
        if request.user and request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'user': UserSerializer(request.user).data
            })
        return Response({'authenticated': False})


# ============================================================================
# NEW: Password Reset Views (Public endpoints - No authentication required!)
# ============================================================================

class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'email': ['Email is required']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(email=email)
            
            # Generate token and uid
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://javanetict.com')
            reset_url = f"{frontend_url}/reset-password?uid={uid}&token={token}"
            
            # Create email using EmailMessage
            subject = 'Password Reset Request - JavaNet EdTech'
            message = f'''
            Hello {user.email},
            
            You requested a password reset for your JavaNet EdTech account.
            
            Click the link below to reset your password:
            {reset_url}
            
            If you didn't request this, please ignore this email.
            
            This link will expire in 24 hours.
            
            Best regards,
            JavaNet EdTech Team
            '''
            
            email_message = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
                reply_to=[getattr(settings, 'CONTACT_EMAIL', settings.DEFAULT_FROM_EMAIL)],
            )
            
            email_message.send(fail_silently=False)
            
            # Track activity
            track_activity(user, 'PASSWORD_RESET_REQUEST', {'email': email}, request)
            
        except CustomUser.DoesNotExist:
            # Don't reveal that the user doesn't exist
            pass
        
        return Response(
            {'message': 'If an account exists with this email, a password reset link has been sent.'},
            status=status.HTTP_200_OK
        )
    

class PasswordResetConfirmView(APIView):
    """
    Reset password using token.
    POST: /api/auth/password/reset/confirm/
    """
    permission_classes = [permissions.AllowAny]  # 🔴 IMPORTANT: Public endpoint!
    
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        # Validate input
        if not all([uid, token, new_password]):
            return Response(
                {'error': 'uid, token, and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode uid
            user_id = urlsafe_base64_decode(uid).decode()
            user = CustomUser.objects.get(pk=user_id)
            
            # Verify token
            if default_token_generator.check_token(user, token):
                # Set new password
                user.set_password(new_password)
                user.save()
                
                # Track activity
                track_activity(user, 'PASSWORD_RESET_SUCCESS', {}, request)
                
                return Response(
                    {'message': 'Password has been reset successfully.'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid or expired reset token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {'error': 'Invalid reset link.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetVerifyView(APIView):
    """
    Verify if a reset token is valid.
    POST: /api/auth/password/reset/verify/
    """
    permission_classes = [permissions.AllowAny]  # 🔴 IMPORTANT: Public endpoint!
    
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        
        if not all([uid, token]):
            return Response(
                {'valid': False, 'error': 'uid and token are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = CustomUser.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                return Response({'valid': True}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'valid': False, 'error': 'Invalid or expired token'},
                    status=status.HTTP_200_OK
                )
                
        except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {'valid': False, 'error': 'Invalid reset link'},
                status=status.HTTP_200_OK
            )


class TestEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            email = EmailMessage(
                subject='✅ JavaNet EdTech - Test Email',
                body=f'''
                Hello!
                
                Your email configuration is WORKING!
                
                Server: {settings.EMAIL_HOST}
                Port: {settings.EMAIL_PORT}
                SSL: {settings.EMAIL_USE_SSL}
                From: {settings.DEFAULT_FROM_EMAIL}
                
                Timestamp: {timezone.now()}
                
                Best regards,
                JavaNet EdTech Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['javanetict@gmail.com'],  # Send to yourself
                reply_to=[settings.DEFAULT_FROM_EMAIL],
            )
            email.send(fail_silently=False)
            return Response({'message': '✅ Test email sent successfully!'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)