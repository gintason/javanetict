from django.db import models
import uuid

class ProposalRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GENERATED', 'Generated'),
        ('SENT', 'Sent'),
        ('VIEWED', 'Viewed'),
        ('EXPIRED', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    institution = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)
    
    # Requirements
    needs_ctb = models.BooleanField(default=True)
    needs_live_classes = models.BooleanField(default=False)
    estimated_students = models.IntegerField(default=100)
    estimated_teachers = models.IntegerField(default=10)
    
    # Branding preferences
    preferred_colors = models.CharField(max_length=200, blank=True)
    has_logo = models.BooleanField(default=False)
    
    # Proposal details
    currency = models.CharField(max_length=3, default='USD')
    deployment_fee = models.CharField(max_length=100, blank=True)
    proposal_pdf = models.FileField(upload_to='proposals/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Proposal for {self.institution} by {self.name}"
    
    # Add this method to save PDF file path
    def save_proposal_pdf(self, file_path):
        """Save the generated PDF to the model"""
        # This method can be called after PDF generation
        self.proposal_pdf = file_path
        self.status = 'GENERATED'
        self.save()
    
    def get_proposal_data(self):
        """Return data for PDF generation"""
        return {
            'proposal_id': str(self.id),
            'name': self.name,
            'email': self.email,
            'institution': self.institution,
            'phone': self.phone,
            'country': self.country,
            'needs_ctb': self.needs_ctb,
            'needs_live_classes': self.needs_live_classes,
            'estimated_students': self.estimated_students,
            'estimated_teachers': self.estimated_teachers,
            'preferred_colors': self.preferred_colors,
            'has_logo': self.has_logo,
            'currency': self.currency,
            'deployment_fee': self.deployment_fee,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }