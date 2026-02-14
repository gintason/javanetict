from django.db import models
import uuid

class Client(models.Model):
    """Model for schools/education businesses using our platform"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    institution_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, default='Nigeria')
    currency = models.CharField(max_length=3, default='NGN', choices=[('NGN', '₦ Naira'), ('USD', '$ US Dollar')])
    
    # Platform preferences
    needs_ctb = models.BooleanField(default=True)
    needs_live_classes = models.BooleanField(default=False)
    
    # Branding preferences
    primary_color = models.CharField(max_length=7, default='#1A237E')  # Hex color
    secondary_color = models.CharField(max_length=7, default='#00C853')
    logo = models.ImageField(upload_to='client_logos/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.institution_name} - {self.name}"

class Feature(models.Model):
    """Features of our platform"""
    FEATURE_TYPES = [
        ('ctb', 'Computer-Based Testing'),
        ('LIVE', 'Live Classroom'),
        ('GEN', 'General'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Bootstrap icon class")
    feature_type = models.CharField(max_length=10, choices=FEATURE_TYPES)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name

class Testimonial(models.Model):
    """Client testimonials"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='testimonials')
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Testimonial from {self.client.institution_name}"


class Contact(models.Model):
    """Model for contact form submissions"""
    SUBJECT_CHOICES = [
        ('General Inquiry', 'General Inquiry'),
        ('Pricing Information', 'Pricing Information'),
        ('Technical Support', 'Technical Support'),
        ('Customization Request', 'Customization Request'),
        ('Partnership Inquiry', 'Partnership Inquiry'),
        ('Demo Request', 'Demo Request'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    institution = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='General Inquiry')
    message = models.TextField()
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject} - {self.created_at.strftime('%Y-%m-%d')}"