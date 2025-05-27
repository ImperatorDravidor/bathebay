from django.apps import AppConfig
from django.contrib import admin


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    verbose_name = 'Product Catalog'
    
    def ready(self):
        """Configure admin when app is ready"""
        # Import admin to ensure it's registered
        from . import admin as products_admin
        
        # Customize admin site
        admin.site.site_header = "🏢 Product Catalog Control Center"
        admin.site.site_title = "Product Admin"
        admin.site.index_title = "Product Catalog Management System"
        
        # Override admin index template
        admin.site.index_template = 'admin/index.html'
