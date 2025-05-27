#!/usr/bin/env python
"""
Management command to populate the brand hierarchy structure
Based on the bathingbrands.com product structure
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Brand, Category, Collection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate the brand hierarchy structure from bathingbrands.com'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing hierarchy data before populating',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏢 Populating Brand Hierarchy Structure...'))
        
        if options['clear']:
            self.stdout.write('🗑️ Clearing existing hierarchy data...')
            Collection.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Cleared existing data'))
        
        # Brand hierarchy structure from bathingbrands.com
        hierarchy_data = {
            'Amerec': {
                'Residential Steam': [
                    'Steam Shower Generators',
                    'Controls & Packages',
                    'Lighting',
                    'Aromatherapy Systems',
                    'Audio & Video',
                    'Seats',
                    'Water Treatment',
                    'Accessories',
                    'Installation Materials',
                    'Steam Heads',
                    'Aromas'
                ],
                'Commercial Steam': [
                    'Club Generators',
                    'Controls & Packages',
                    'Accessories',
                    'Steam Heads',
                    'Eucalyptus Pumps'
                ],
                'Sauna': [
                    'Electric Heaters',
                    'Controls & Packages',
                    'Gauges',
                    'Accessories',
                    'Safety'
                ]
            },
            'Aromamist': {
                'Commercial Steam': [
                    'Aromas',
                    'Aromatherapy Systems',
                    'Eucalyptus Pumps'
                ],
                'Residential Steam': [
                    'Aromas',
                    'Aromatherapy Systems',
                    'Eucalyptus Pumps'
                ]
            },
            'Auroom': {
                'Room Kits': [
                    'Modular',
                    'Outdoor'
                ],
                'Accessories': [],
                'Aroma': []
            },
            'Cozy Heat': {
                'Wood Sauna Stoves': [],
                'Accessories': [],
                'Backyard Fire Pits': []
            },
            'Delta': {
                'Residential Steam': [
                    'Steam Shower Generators',
                    'Generator Packages',
                    'Controls & Packages',
                    'Accessories',
                    'Audio & Video',
                    'Speakers',
                    'Seats',
                    'Installation Materials',
                    'Steam Heads'
                ],
                'Commercial Steam': [
                    'Steam Shower Generators',
                    'Steam Shower Generator Packages',
                    'Controls & Packages',
                    'Accessories',
                    'Aromatherapy Systems',
                    'Aroma',
                    'Installation Materials',
                    'Safety'
                ]
            },
            'EmotionWood': {
                'Sauna': [
                    'Decorative Sauna Walls'
                ]
            },
            'Finlandia': {
                'Sauna': [
                    'Electric Heaters',
                    'Controls & Packages',
                    'Accessories'
                ]
            },
            'Finnmark': {
                'Infrared Room Kits': [],
                'Infrared Sauna Essentials': []
            },
            'Haljas Houses': {
                'Room Kits': [
                    'Outdoor'
                ]
            },
            'Harvia': {
                'Sauna': [
                    'Electric Heaters',
                    'Wood Sauna Stoves',
                    'Controls & Packages',
                    'Accessories'
                ]
            },
            'HUUM': {
                'Sauna': [
                    'Electric Heaters',
                    'Heater Packages',
                    'Controls & Packages',
                    'Wood Sauna Stoves',
                    'Accessories',
                    'Safety'
                ]
            },
            'Hukka': {
                'Sauna': [
                    'Accessories'
                ]
            },
            'Kohler': {
                'Steam': [
                    'Steam Shower Generators',
                    'Controls & Packages',
                    'Accessories'
                ],
                'Shower': [
                    'Shower Systems'
                ]
            },
            'Kolo': {
                'Sauna': [
                    'Buckets & Ladles',
                    'Accessories'
                ]
            },
            'Mr.Steam': {
                'Residential Steam': [
                    'Generator Packages',
                    'Steam Shower Generators',
                    'Controls & Packages',
                    'Lighting',
                    'Chromotherapy',
                    'Aromatherapy Systems',
                    'Aromas',
                    'Audio & Video',
                    'Seats',
                    'Towel Warmers',
                    'Accessories',
                    'Installation Materials',
                    'Steam Heads'
                ],
                'Commercial Steam': [
                    'Club Generators',
                    'Eucalyptus Pumps',
                    'Spa Generators',
                    'Controls & Packages',
                    'Aromas',
                    'Audio & Video',
                    'Accessories',
                    'Safety',
                    'Maintenance',
                    'Installation Materials',
                    'Steam Heads'
                ]
            },
            'Narvi': {
                'Accessories': [],
                'Wood Sauna Stoves': []
            },
            'PROSAUNAS': {
                'Wall Cladding': [
                    'Alder',
                    'Aspen',
                    'Black Wax-Coated Aspen',
                    'Cedar',
                    'Hemlock',
                    'Thermo-Aspen',
                    'Thermo-Radiata Pine',
                    'Thermo-Spruce'
                ],
                'Bench Material': [
                    'Alder',
                    'Aspen',
                    'Cedar',
                    'Hemlock',
                    'Thermo-Aspen',
                    'Thermo-Radiata Pine',
                    'Thermo-Spruce'
                ],
                'Trim': [
                    'Alder',
                    'Aspen',
                    'Thermo-Aspen',
                    'Thermo-Radiata Pine'
                ],
                'Sauna Doors': [],
                'Lighting & Chromotherapy': [],
                'Back & Headrests': [],
                'Sauna Buckets & Ladles': [],
                'Sauna Accessories': []
            },
            'Rento': {
                'Buckets & Ladles': [],
                'Sauna Accessories': [],
                'Sauna Aromatherapy': []
            },
            'SaunaLife': {
                'Room Kits': [
                    'Barrel Saunas',
                    'Indoor',
                    'Outdoor'
                ],
                'Cold Plunge Tubs': [],
                'Hot Tubs': [],
                'Outdoor Showers': [],
                'Accessories': []
            },
            'Saunum': {
                'Sauna': [
                    'Electric Heaters',
                    'Heater Packages',
                    'Room Kits',
                    'Controls & Packages',
                    'Heat Equalizing Systems',
                    'Accessories',
                    'Aroma'
                ]
            },
            'Steamist': {
                'Residential Steam': [
                    'Steam Shower Generators',
                    'Controls & Packages',
                    'Audio & Video',
                    'Chromotherapy',
                    'Aromatherapy Systems',
                    'Aromas',
                    'Seats',
                    'Accessories',
                    'Installation Materials',
                    'Steam Heads'
                ],
                'Commercial Steam': [
                    'Club Generators',
                    'Controls & Packages',
                    'Chromotherapy',
                    'Aromatherapy Systems',
                    'Aromas',
                    'Accessories',
                    'Safety'
                ]
            },
            'ThermaSol': {
                'Residential Steam': [
                    'Steam Shower Generators',
                    'Controls & Packages',
                    'Steam Heads',
                    'Shower Systems',
                    'Speakers',
                    'Aromas',
                    'Installation Materials'
                ],
                'Commercial Steam': [
                    'Club Generators',
                    'Spa Generators',
                    'Controls & Packages',
                    'Shower Systems',
                    'Installation Materials'
                ],
                'Bath': [
                    'Fixtures & Drains',
                    'Fog-Free Mirrors',
                    'Lighting',
                    'Rains & Body Sprays',
                    'Seats',
                    'Shower Systems'
                ]
            }
        }
        
        # Additional brands that might not have detailed structure yet
        additional_brands = [
            'EOS', 'Wedi', 'Bathology'
        ]
        
        created_counts = {'brands': 0, 'categories': 0, 'collections': 0}
        
        with transaction.atomic():
            # Create brands and their hierarchies
            for brand_name, categories in hierarchy_data.items():
                brand, created = Brand.objects.get_or_create(
                    name=brand_name,
                    defaults={
                        'description': f'{brand_name} products from bathingbrands.com',
                        'is_active': True
                    }
                )
                if created:
                    created_counts['brands'] += 1
                    self.stdout.write(f'  🏢 Created brand: {brand_name}')
                
                # Create categories for this brand
                for category_name, collections in categories.items():
                    category, created = Category.objects.get_or_create(
                        brand=brand,
                        name=category_name,
                        defaults={
                            'description': f'{category_name} products from {brand_name}',
                            'is_active': True
                        }
                    )
                    if created:
                        created_counts['categories'] += 1
                        self.stdout.write(f'    📂 Created category: {brand_name} → {category_name}')
                    
                    # Create collections for this category
                    if collections:  # Only if collections are specified
                        for collection_name in collections:
                            collection, created = Collection.objects.get_or_create(
                                category=category,
                                name=collection_name,
                                defaults={
                                    'description': f'{collection_name} from {brand_name} {category_name}',
                                    'is_active': True
                                }
                            )
                            if created:
                                created_counts['collections'] += 1
                                self.stdout.write(f'      📦 Created collection: {brand_name} → {category_name} → {collection_name}')
                    else:
                        # Create a default collection with the same name as category
                        collection, created = Collection.objects.get_or_create(
                            category=category,
                            name=category_name,
                            defaults={
                                'description': f'{category_name} from {brand_name}',
                                'is_active': True
                            }
                        )
                        if created:
                            created_counts['collections'] += 1
                            self.stdout.write(f'      📦 Created default collection: {brand_name} → {category_name} → {category_name}')
            
            # Create additional brands without detailed structure
            for brand_name in additional_brands:
                brand, created = Brand.objects.get_or_create(
                    name=brand_name,
                    defaults={
                        'description': f'{brand_name} products from bathingbrands.com',
                        'is_active': True
                    }
                )
                if created:
                    created_counts['brands'] += 1
                    self.stdout.write(f'  🏢 Created additional brand: {brand_name}')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n📊 Hierarchy Population Summary:'))
        self.stdout.write(f'  🏢 Brands created: {created_counts["brands"]}')
        self.stdout.write(f'  📂 Categories created: {created_counts["categories"]}')
        self.stdout.write(f'  📦 Collections created: {created_counts["collections"]}')
        
        # Show totals
        total_brands = Brand.objects.count()
        total_categories = Category.objects.count()
        total_collections = Collection.objects.count()
        
        self.stdout.write(f'\n📈 Total in Database:')
        self.stdout.write(f'  🏢 Total Brands: {total_brands}')
        self.stdout.write(f'  📂 Total Categories: {total_categories}')
        self.stdout.write(f'  📦 Total Collections: {total_collections}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Brand hierarchy population complete!'))
        self.stdout.write('🔗 You can now view the hierarchy in the Django admin panel.') 