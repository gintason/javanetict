from django.contrib import admin
from .models import ChatSession, ChatMessage, Intent, ChatbotConfig

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('timestamp',)

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'country', 'currency', 'created_at', 'last_activity')
    list_filter = ('country', 'currency')
    inlines = [ChatMessageInline]
    readonly_fields = ('created_at', 'last_activity')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'message_type', 'content_preview', 'timestamp')
    list_filter = ('message_type', 'timestamp')
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Intent)
class IntentAdmin(admin.ModelAdmin):
    list_display = ('tag', 'created_at', 'updated_at')
    search_fields = ('tag', 'patterns')
    list_filter = ('created_at',)

@admin.register(ChatbotConfig)
class ChatbotConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)