from django.core.management.base import BaseCommand
from products.models import Product, ProductImage, ProductSpecification, ProductDocument


class Command(BaseCommand):
    help = 'Delete all products and related data'

    def handle(self, *args, **options):
        # Delete all products (this will cascade to related objects)
        count = Product.objects.count()
        Product.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} products and all related data')
        ) 