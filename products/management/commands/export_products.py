import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from products.models import Product
from products.exporters import (
    export_to_csv, export_to_ebay, 
    export_to_amazon, export_to_shopify
)


class Command(BaseCommand):
    help = 'Export products to various formats (CSV, eBay, Amazon, Shopify)'

    def add_arguments(self, parser):
        parser.add_argument(
            'format',
            choices=['csv', 'ebay', 'amazon', 'shopify'],
            help='Export format'
        )
        parser.add_argument(
            '--filename',
            type=str,
            help='Output filename (optional)',
        )
        parser.add_argument(
            '--brand',
            type=str,
            help='Filter by brand',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Filter by category',
        )

    def handle(self, *args, **options):
        # Build queryset with filters
        queryset = Product.objects.filter(is_active=True)
        
        if options['brand']:
            queryset = queryset.filter(brand__icontains=options['brand'])
            
        if options['category']:
            queryset = queryset.filter(category__icontains=options['category'])
        
        count = queryset.count()
        if count == 0:
            self.stdout.write(
                self.style.WARNING('No products found matching the criteria')
            )
            return
        
        self.stdout.write(f"Exporting {count} products...")
        
        # Determine filename
        format_type = options['format']
        filename = options.get('filename') or f"products_{format_type}.csv"
        
        # Export based on format
        try:
            if format_type == 'csv':
                response = export_to_csv(queryset, filename)
            elif format_type == 'ebay':
                response = export_to_ebay(queryset, filename)
            elif format_type == 'amazon':
                response = export_to_amazon(queryset, filename)
            elif format_type == 'shopify':
                response = export_to_shopify(queryset, filename)
            
            # Save to file instead of returning HTTP response
            output_path = os.path.join(settings.BASE_DIR, filename)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                f.write(response.content.decode('utf-8'))
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully exported to {output_path}')
            )
            
        except Exception as e:
            raise CommandError(f'Export failed: {e}') 