from django.contrib import admin
from .models import Client, Feature, Testimonial, Contact

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'name', 'country', 'currency', 'created_at')
    list_filter = ('country', 'currency', 'is_active')
    search_fields = ('institution_name', 'name', 'email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'institution_name')
        }),
        ('Location', {
            'fields': ('country', 'currency')
        }),
        ('Platform Preferences', {
            'fields': ('needs_ctb', 'needs_live_classes')
        }),
        ('Branding', {
            'fields': ('primary_color', 'secondary_color', 'logo'),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('wide',)
        }),
    )

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'feature_type', 'order', 'icon')
    list_filter = ('feature_type',)
    search_fields = ('name', 'description')
    ordering = ('order', 'feature_type')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'icon')
        }),
        ('Configuration', {
            'fields': ('feature_type', 'order')
        }),
    )

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client', 'rating', 'is_featured', 'created_at')
    list_filter = ('rating', 'is_featured', 'created_at')
    search_fields = ('client__institution_name', 'client__name', 'content')
    readonly_fields = ('created_at',)
    raw_id_fields = ('client',)
    fieldsets = (
        (None, {
            'fields': ('client', 'content', 'rating')
        }),
        ('Status', {
            'fields': ('is_featured', 'created_at')
        }),
    )

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'institution', 'is_read', 'is_replied', 'created_at')
    list_filter = ('subject', 'is_read', 'is_replied', 'created_at')
    search_fields = ('name', 'email', 'institution', 'message')
    readonly_fields = ('created_at', 'replied_at')
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_unread']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'institution')
        }),
        ('Message Details', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'is_replied', 'replied_at', 'created_at'),
            'classes': ('wide',)
        }),
    )
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_replied(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_replied=True, replied_at=timezone.now())
    mark_as_replied.short_description = "Mark selected messages as replied"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Mark selected messages as unread"