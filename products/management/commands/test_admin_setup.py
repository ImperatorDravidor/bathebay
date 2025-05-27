from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test admin setup and create sample data if needed'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Testing Admin Setup...'))
        self.stdout.write('=' * 50)
        
        # Check admin user
        admin_users = User.objects.filter(is_superuser=True)
        self.stdout.write(f'📊 Admin users found: {admin_users.count()}')
        
        if admin_users.exists():
            admin_user = admin_users.first()
            self.stdout.write(self.style.SUCCESS(f'✅ Admin user: {admin_user.username}'))
        else:
            self.stdout.write(self.style.ERROR('❌ No admin user found'))
            self.stdout.write('💡 Run: python scripts/create_admin.py')
        
        # Check products
        product_count = Product.objects.count()
        self.stdout.write(f'📦 Products in database: {product_count}')
        
        # Create sample products if none exist
        if product_count == 0:
            self.stdout.write('🔄 Creating sample products...')
            self.create_sample_products()
        
        # Show brands
        brands = list(Product.objects.values_list('brand', flat=True).distinct())
        self.stdout.write(f'🏢 Brands: {brands[:5]}{"..." if len(brands) > 5 else ""}')
        
        self.stdout.write('\n🌐 Admin URLs:')
        self.stdout.write('   Main Admin: http://127.0.0.1:8000/admin/')
        self.stdout.write('   Product Catalog: http://127.0.0.1:8000/admin/products/product/')
        
        self.stdout.write('\n👤 Login credentials:')
        self.stdout.write('   Username: admin')
        self.stdout.write('   Password: magnesium')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Admin setup test complete!'))
    
    def create_sample_products(self):
        """Create sample products for testing"""
        sample_products = [
            {
                'title': 'HUUM DROP 4.5 Electric Sauna Heater',
                'brand': 'HUUM',
                'category': 'Sauna Heaters',
                'sku': 'HUUM-DROP-45',
                'price': Decimal('1299.99'),
                'short_description': 'Compact electric sauna heater with modern design',
                'source_url': 'https://bathingbrands.com/sample/huum-drop-45',
                'is_active': True,
            },
            {
                'title': 'Harvia Cilindro PC70 Electric Heater',
                'brand': 'Harvia',
                'category': 'Sauna Heaters',
                'sku': 'HARVIA-PC70',
                'price': Decimal('899.99'),
                'short_description': 'Traditional electric sauna heater',
                'source_url': 'https://bathingbrands.com/sample/harvia-pc70',
                'is_active': True,
            },
            {
                'title': 'Amerec AK 6 Steam Generator',
                'brand': 'Amerec',
                'category': 'Steam Generators',
                'sku': 'AMEREC-AK6',
                'price': Decimal('2199.99'),
                'short_description': 'Residential steam generator for home spas',
                'source_url': 'https://bathingbrands.com/sample/amerec-ak6',
                'is_active': True,
            },
            {
                'title': 'Finnmark FLB-60 Sauna Heater',
                'brand': 'Finnmark',
                'category': 'Sauna Heaters',
                'sku': 'FINNMARK-FLB60',
                'price': Decimal('749.99'),
                'short_description': 'Efficient electric sauna heater',
                'source_url': 'https://bathingbrands.com/sample/finnmark-flb60',
                'is_active': True,
            },
            {
                'title': 'ThermaSol PRO Series Steam Generator',
                'brand': 'ThermaSol',
                'category': 'Steam Generators',
                'sku': 'THERMASOL-PRO',
                'price': Decimal('3299.99'),
                'short_description': 'Professional steam generator system',
                'source_url': 'https://bathingbrands.com/sample/thermasol-pro',
                'is_active': True,
            },
        ]
        
        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'   ✅ Created: {product.title}')
            else:
                self.stdout.write(f'   ℹ️ Exists: {product.title}')
        
        self.stdout.write(self.style.SUCCESS(f'📦 Sample products ready!')) 