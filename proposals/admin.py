from django.contrib import admin
from .models import ProposalRequest
from django.utils.html import format_html

@admin.register(ProposalRequest)
class ProposalRequestAdmin(admin.ModelAdmin):
    list_display = ('institution', 'name', 'email', 'country', 'deployment_fee', 'status', 'created_at', 'view_proposal_link')
    list_filter = ('status', 'country', 'created_at', 'needs_ctb', 'needs_live_classes')
    search_fields = ('name', 'email', 'institution', 'country')
    readonly_fields = ('id', 'created_at', 'updated_at', 'proposal_pdf_preview')
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'institution', 'phone', 'country')
        }),
        ('Requirements', {
            'fields': ('needs_ctb', 'needs_live_classes', 'estimated_students', 'estimated_teachers')
        }),
        ('Branding Preferences', {
            'fields': ('preferred_colors', 'has_logo')
        }),
        ('Proposal Details', {
            'fields': ('currency', 'deployment_fee', 'proposal_pdf', 'status')
        }),
        ('Metadata', {
            'fields': ('id', 'ip_address', 'created_at', 'updated_at', 'proposal_pdf_preview'),
            'classes': ('collapse',)
        }),
    )
    
    def view_proposal_link(self, obj):
        if obj.proposal_pdf:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.proposal_pdf.url)
        return "No PDF"
    view_proposal_link.short_description = 'PDF'
    
    def proposal_pdf_preview(self, obj):
        if obj.proposal_pdf:
            return format_html(
                '<div style="margin: 10px 0;">'
                '<a href="{}" target="_blank" style="background: #4CAF50; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; margin-right: 10px;">'
                '📄 View PDF</a>'
                '<span style="color: #666; font-size: 12px;">File: {}</span>'
                '</div>',
                obj.proposal_pdf.url,
                obj.proposal_pdf.name.split('/')[-1]
            )
        return "No PDF generated yet"
    proposal_pdf_preview.short_description = 'PDF Preview'
    
    def save_model(self, request, obj, form, change):
        # Update status if deployment fee is set
        if obj.deployment_fee and obj.status == 'PENDING':
            obj.status = 'GENERATED'
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_sent', 'mark_as_viewed', 'mark_as_expired']
    
    def mark_as_sent(self, request, queryset):
        queryset.update(status='SENT')
        self.message_user(request, f"{queryset.count()} proposals marked as sent.")
    mark_as_sent.short_description = "Mark selected proposals as sent"
    
    def mark_as_viewed(self, request, queryset):
        queryset.update(status='VIEWED')
        self.message_user(request, f"{queryset.count()} proposals marked as viewed.")
    mark_as_viewed.short_description = "Mark selected proposals as viewed"
    
    def mark_as_expired(self, request, queryset):
        queryset.update(status='EXPIRED')
        self.message_user(request, f"{queryset.count()} proposals marked as expired.")
    mark_as_expired.short_description = "Mark selected proposals as expired"