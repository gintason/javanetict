#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Feature, Client, Testimonial
from django.contrib.auth import get_user_model

User = get_user_model()

def create_features():
    features = [
        {
            'name': 'Automated Grading',
            'description': 'Instant grading with detailed analytics and performance reports',
            'icon': 'bi-speedometer2',
            'feature_type': 'ctb',
            'order': 1
        },
        {
            'name': 'Question Bank',
            'description': 'Organized question repository with tagging and categorization',
            'icon': 'bi-database',
            'feature_type': 'ctb',
            'order': 2
        },
        {
            'name': 'Anti-Cheat System',
            'description': 'Advanced monitoring for exam integrity with screen recording',
            'icon': 'bi-shield-check',
            'feature_type': 'ctb',
            'order': 3
        },
        {
            'name': 'Virtual Whiteboard',
            'description': 'Interactive whiteboard for live teaching with drawing tools',
            'icon': 'bi-easel',
            'feature_type': 'LIVE',
            'order': 1
        },
        {
            'name': 'Session Recording',
            'description': 'Record and replay all classroom sessions for later review',
            'icon': 'bi-camera-reels',
            'feature_type': 'LIVE',
            'order': 2
        },
        {
            'name': 'Breakout Rooms',
            'description': 'Create separate discussion groups for collaborative learning',
            'icon': 'bi-people',
            'feature_type': 'LIVE',
            'order': 3
        },
        {
            'name': 'Custom Branding',
            'description': 'Your logo, colors, and domain name on the platform',
            'icon': 'bi-palette',
            'feature_type': 'GEN',
            'order': 1
        },
        {
            'name': 'Multi-Platform',
            'description': 'Works on web, tablets, and mobile devices',
            'icon': 'bi-phone',
            'feature_type': 'GEN',
            'order': 2
        },
        {
            'name': 'Analytics Dashboard',
            'description': 'Comprehensive analytics for student performance',
            'icon': 'bi-graph-up',
            'feature_type': 'GEN',
            'order': 3
        },
    ]
    
    for feature_data in features:
        Feature.objects.create(**feature_data)
    
    print(f"Created {len(features)} features")

def create_sample_clients():
    clients = [
        {
            'name': 'Dr. Adebayo Johnson',
            'email': 'adebayo@prestigeacademy.edu.ng',
            'phone': '+2348012345678',
            'institution_name': 'Prestige Academy',
            'country': 'Nigeria',
            'currency': 'NGN',
            'needs_ctb': True,
            'needs_live_classes': True,
            'primary_color': '#1E3A8A',
            'secondary_color': '#10B981',
            'is_active': True
        },
        {
            'name': 'Sarah Williams',
            'email': 'sarah@globalinstitute.com',
            'phone': '+1-555-0123',
            'institution_name': 'Global Institute of Technology',
            'country': 'United States',
            'currency': 'USD',
            'needs_ctb': True,
            'needs_live_classes': False,
            'primary_color': '#7C3AED',
            'secondary_color': '#F59E0B',
            'is_active': True
        },
        {
            'name': 'Kwame Mensah',
            'email': 'kwame@accratechschool.edu.gh',
            'phone': '+233201234567',
            'institution_name': 'Accra Tech School',
            'country': 'Ghana',
            'currency': 'NGN',
            'needs_ctb': True,
            'needs_live_classes': True,
            'primary_color': '#059669',
            'secondary_color': '#DC2626',
            'is_active': True
        },
    ]
    
    for client_data in clients:
        Client.objects.create(**client_data)
    
    print(f"Created {len(clients)} sample clients")

def create_testimonials():
    # Get clients first
    clients = Client.objects.all()
    
    testimonials = [
        {
            'client': clients[0],
            'content': 'JavaNet EdTech Suite transformed our examination process. The ctb system reduced grading time by 80% and the analytics helped us identify learning gaps.',
            'rating': 5,
            'is_featured': True
        },
        {
            'client': clients[1],
            'content': 'As an international institution, we needed a platform that could handle our diverse student base. JavaNet delivered with their white-label solution.',
            'rating': 5,
            'is_featured': True
        },
        {
            'client': clients[2],
            'content': 'The live classroom feature has been a game-changer for our remote learning programs. Easy to use and highly reliable.',
            'rating': 4,
            'is_featured': True
        },
    ]
    
    for testimonial_data in testimonials:
        Testimonial.objects.create(**testimonial_data)
    
    print(f"Created {len(testimonials)} testimonials")

def create_demo_user():
    # Create a demo user for testing
    try:
        user = User.objects.create_user(
            email='demo@school.edu.ng',
            username='demoschool',
            password='demo123',
            first_name='Demo',
            last_name='School',
            company='Demo School',
            country='Nigeria',
            currency='NGN',
            is_client=True
        )
        print(f"Created demo user: {user.email}")
    except:
        print("Demo user already exists")

if __name__ == '__main__':
    print("Creating initial data for JavaNet EdTech Suite...")
    create_features()
    create_sample_clients()
    create_testimonials()
    create_demo_user()
    print("Initial data creation completed!")