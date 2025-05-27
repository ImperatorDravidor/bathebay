from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Clear all products from the database'
    
    def handle(self, *args, **options):
        count = Product.objects.count()
        Product.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Deleted {count} products')) 