# management/commands/fix_feature_types.py
from django.core.management.base import BaseCommand
from core.models import Feature

class Command(BaseCommand):
    help = 'Fix feature_type casing to match model choices'
    
    def handle(self, *args, **kwargs):
        # Fix CTB to ctb
        updated = Feature.objects.filter(feature_type='CTB').update(feature_type='ctb')
        self.stdout.write(f"Updated {updated} CTB features to 'ctb'")
        
        # Verify all feature types are valid
        valid_types = ['ctb', 'LIVE', 'GEN']
        invalid = Feature.objects.exclude(feature_type__in=valid_types)
        
        if invalid.exists():
            self.stdout.write(self.style.ERROR(f"Found invalid feature types: {list(invalid.values_list('feature_type', flat=True).distinct())}"))
        else:
            self.stdout.write(self.style.SUCCESS("All feature types are valid!"))