"""
AI Services module with fallbacks for development
"""
import os
import openai
import cohere
from django.conf import settings

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
        return self.rule_based_response(message)
    
    def rule_based_response(self, message):
        """Rule-based responses for fallback"""
        message_lower = message.lower()
        
        responses = {
            'hello': "Hello! I'm JN Assistant from JavaNet EdTech Suite. How can I help you today?",
            'hi': "Hi there! I'm here to assist you with our education technology solutions.",
            'price': "Our pricing is customized based on your needs. Would you like to generate a custom proposal?",
            'demo': "You can try our live demo at https://www.ischool.ng/",
            'default': "Thank you for your message! I can help you with information about our ctb testing system, live classrooms, pricing, and demos."
        }
        
        for keyword, response in responses.items():
            if keyword in message_lower and keyword != 'default':
                return response
        
        return responses['default']

# Create singleton instance
ai_service = AIService()