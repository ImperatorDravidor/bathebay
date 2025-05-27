from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Product, ProductImage, ProductSpecification, ProductDocument, RelatedProduct, ProductVariant
from .scrapers import EnhancedBathingBrandsScraper
import json
import logging
import csv
import subprocess
import sys
from django.core.management import call_command
from io import StringIO

logger = logging.getLogger(__name__)

# Custom Admin Site Class
class ProductCatalogAdminSite(admin.AdminSite):
    """Custom admin site that defaults to product catalog"""
    site_header = "🏢 Product Catalog Control Center"
    site_title = "Product Admin"
    index_title = "Product Catalog Management System"
    
    def index(self, request, extra_context=None):
        """Override admin index to redirect to product catalog"""
        return redirect('/admin/products/product/')

# Create custom admin site instance
admin_site = ProductCatalogAdminSite(name='product_admin')

class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'sku', 'price', 'created_at', 'is_active']
    list_filter = ['brand', 'category', 'is_active', 'created_at']
    search_fields = ['title', 'brand', 'sku', 'model']
    list_per_page = 25
    ordering = ['-created_at']
    
    # Enhanced list display with better formatting
    def get_list_display(self, request):
        return ['title_with_link', 'brand_badge', 'category_badge', 'sku', 'price_formatted', 'status_badge', 'created_at']
    
    def title_with_link(self, obj):
        """Display title with link to edit"""
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #0066cc;">{}</a>',
            reverse('admin:products_product_change', args=[obj.pk]),
            obj.title[:50] + ('...' if len(obj.title) > 50 else '')
        )
    title_with_link.short_description = 'Product Title'
    
    def brand_badge(self, obj):
        """Display brand as a badge"""
        colors = {
            'HUUM': '#ff6b6b', 'Harvia': '#4ecdc4', 'Amerec': '#45b7d1',
            'Finnmark': '#96ceb4', 'Saunum': '#feca57', 'ThermaSol': '#ff9ff3'
        }
        color = colors.get(obj.brand, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.brand
        )
    brand_badge.short_description = 'Brand'
    
    def category_badge(self, obj):
        """Display category as a badge"""
        if obj.category:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">{}</span>',
                obj.category
            )
        return format_html('<span style="color: #6c757d;">No Category</span>')
    category_badge.short_description = 'Category'
    
    def price_formatted(self, obj):
        """Display formatted price"""
        if obj.price:
            return format_html(
                '<span style="font-weight: bold; color: #28a745;">${:,.2f}</span>',
                obj.price
            )
        return format_html('<span style="color: #dc3545;">No Price</span>')
    price_formatted.short_description = 'Price'
    
    def status_badge(self, obj):
        """Display status badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">✗ Inactive</span>'
        )
    status_badge.short_description = 'Status'
    
    # Custom admin URLs - Comprehensive feature access
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Main Dashboard
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='products_dashboard'),
            
            # Scraping Operations
            path('scraping-control/', self.admin_site.admin_view(self.scraping_control_view), name='products_scraping_control'),
            path('scrape-huum/', self.admin_site.admin_view(self.scrape_huum), name='products_scrape_huum'),
            path('scrape-all-brands/', self.admin_site.admin_view(self.scrape_all_brands), name='products_scrape_all_brands'),
            path('intelligent-scrape/', self.admin_site.admin_view(self.intelligent_scrape), name='products_intelligent_scrape'),
            
            # Data Management
            path('data-validation/', self.admin_site.admin_view(self.data_validation), name='products_data_validation'),
            path('export-csv/', self.admin_site.admin_view(self.export_csv), name='products_export_csv'),
            path('clean-data/', self.admin_site.admin_view(self.clean_data), name='products_clean_data'),
            path('clear-all/', self.admin_site.admin_view(self.clear_all_products), name='products_clear_all'),
            
            # Hierarchy Management
            path('brand-hierarchy/', self.admin_site.admin_view(self.brand_hierarchy), name='products_brand_hierarchy'),
            path('category-view/', self.admin_site.admin_view(self.category_view), name='products_category_view'),
            path('collection-view/', self.admin_site.admin_view(self.collection_view), name='products_collection_view'),
            
            # Management Commands Interface
            path('run-management-command/', self.admin_site.admin_view(self.run_management_command), name='products_run_command'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist to show main dashboard - Single entry point"""
        return self.dashboard_view(request)
    
    def dashboard_view(self, request):
        """Comprehensive Product Catalog Control Center"""
        # Get comprehensive statistics
        total_products = Product.objects.count()
        total_brands = Product.objects.values('brand').distinct().count()
        total_categories = Product.objects.values('category').distinct().count()
        active_products = Product.objects.filter(is_active=True).count()
        
        # Get brand breakdown
        brands = Product.objects.values('brand').annotate(
            product_count=Count('id')
        ).order_by('-product_count')[:10]
        
        # Get category breakdown
        categories = Product.objects.values('category').annotate(
            product_count=Count('id')
        ).order_by('-product_count')[:10]
        
        # Get recent products
        recent_products = Product.objects.all().order_by('-created_at')[:5]
        
        # Get products with issues (missing data)
        products_missing_images = Product.objects.filter(images__isnull=True).count()
        products_missing_price = Product.objects.filter(price__isnull=True).count()
        products_missing_description = Product.objects.filter(
            Q(short_description='') | Q(short_description__isnull=True)
        ).count()
        
        # Calculate data quality score
        data_quality_score = self.calculate_data_quality_score()
        
        # Get average price
        avg_price = Product.objects.filter(price__isnull=False).aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0
        
        context = {
            'title': 'Product Catalog Control Center',
            'opts': self.model._meta,
            'has_permission': True,
            'total_products': total_products,
            'total_brands': total_brands,
            'total_categories': total_categories,
            'active_products': active_products,
            'top_brands': brands,
            'top_categories': categories,
            'recent_products': recent_products,
            'products_missing_images': products_missing_images,
            'products_missing_price': products_missing_price,
            'products_missing_description': products_missing_description,
            'data_quality_score': data_quality_score,
            'avg_price': round(avg_price, 2),
            'site_url': '/',  # Main site URL
        }
        
        return render(request, 'admin/products/dashboard.html', context)
    
    def calculate_data_quality_score(self):
        """Calculate overall data quality score"""
        total = Product.objects.count()
        if total == 0:
            return 100
        
        complete_products = Product.objects.filter(
            price__isnull=False,
            images__isnull=False
        ).exclude(
            Q(short_description='') | Q(short_description__isnull=True)
        ).distinct().count()
        
        return round((complete_products / total) * 100, 1)
    
    def scraping_control_view(self, request):
        """Enhanced scraping control interface"""
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'scrape_huum':
                try:
                    limit = int(request.POST.get('limit', 10))
                    self.execute_management_command('scrape_huum', [f'--limit={limit}'])
                    messages.success(request, f"HUUM scraping initiated for {limit} products")
                except Exception as e:
                    messages.error(request, f"HUUM scraping failed: {str(e)}")
                
            elif action == 'scrape_all_brands':
                try:
                    limit_per_brand = request.POST.get('limit_per_brand', '5')
                    self.execute_management_command('scrape_all_brands', [f'--limit-per-brand={limit_per_brand}'])
                    messages.success(request, f"All brands scraping initiated with {limit_per_brand} products per brand")
                except Exception as e:
                    messages.error(request, f"All brands scraping failed: {str(e)}")
                
            elif action == 'intelligent_scrape':
                try:
                    brand = request.POST.get('brand', '')
                    limit = request.POST.get('limit', '20')
                    args = [f'--limit={limit}']
                    if brand:
                        args.append(f'--brand={brand}')
                    self.execute_management_command('intelligent_scrape', args)
                    messages.success(request, f"Intelligent scraping initiated")
                except Exception as e:
                    messages.error(request, f"Intelligent scraping failed: {str(e)}")
                
            return redirect('admin:products_dashboard')
        
        context = {
            'title': 'Advanced Scraping Control Center',
            'opts': self.model._meta,
        }
        return render(request, 'admin/products/scraping_control.html', context)
    
    def execute_management_command(self, command, args=None):
        """Execute management command safely"""
        try:
            output = StringIO()
            call_command(command, *(args or []), stdout=output)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Management command {command} failed: {e}")
            raise
    
    def run_management_command(self, request):
        """Run management commands from admin interface"""
        if request.method == 'POST':
            command = request.POST.get('command')
            args = request.POST.get('args', '').split()
            
            try:
                result = self.execute_management_command(command, args)
                messages.success(request, f"Command '{command}' executed successfully")
                if result:
                    messages.info(request, f"Output: {result[:200]}...")
                
            except Exception as e:
                messages.error(request, f"Command '{command}' failed: {str(e)}")
        
        return redirect('admin:products_dashboard')
    
    def export_csv(self, request):
        """Export all products to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Title', 'Brand', 'Category', 'SKU', 'Price', 'Model', 
            'Short Description', 'Created At', 'Source URL'
        ])
        
        for product in Product.objects.all():
            writer.writerow([
                product.title,
                product.brand,
                product.category,
                product.sku,
                product.price,
                product.model,
                product.short_description,
                product.created_at.strftime('%Y-%m-%d %H:%M'),
                product.source_url,
            ])
        
        messages.success(request, f"Exported {Product.objects.count()} products to CSV")
        return response
    
    def clean_data(self, request):
        """Clean product data using management command"""
        try:
            self.execute_management_command('clean_product_data')
            messages.success(request, "Product data cleaning completed successfully")
        except Exception as e:
            messages.error(request, f"Data cleaning failed: {str(e)}")
        
        return redirect('admin:products_dashboard')
    
    def clear_all_products(self, request):
        """Clear all products from database"""
        if request.method == 'POST':
            count = Product.objects.count()
            Product.objects.all().delete()
            messages.success(request, f"Deleted {count} products from database")
            return redirect('admin:products_dashboard')
        
        context = {
            'title': 'Clear All Products',
            'opts': self.model._meta,
            'product_count': Product.objects.count(),
        }
        return render(request, 'admin/products/confirm_clear.html', context)
    
    def scrape_huum(self, request):
        """Quick HUUM scraping action"""
        try:
            self.execute_management_command('scrape_huum', ['--limit=5'])
            messages.success(request, "Quick HUUM scrape completed (5 products)")
        except Exception as e:
            messages.error(request, f"Quick HUUM scrape failed: {str(e)}")
        
        return redirect('admin:products_dashboard')
    
    def scrape_all_brands(self, request):
        """Scrape all brands"""
        try:
            self.execute_management_command('scrape_all_brands', ['--limit-per-brand=3'])
            messages.success(request, "All brands scraping initiated (3 products per brand)")
        except Exception as e:
            messages.error(request, f"All brands scraping failed: {str(e)}")
        
        return redirect('admin:products_dashboard')
    
    def intelligent_scrape(self, request):
        """Intelligent scraping"""
        try:
            self.execute_management_command('intelligent_scrape', ['--limit=10'])
            messages.success(request, "Intelligent scraping initiated (10 products)")
        except Exception as e:
            messages.error(request, f"Intelligent scraping failed: {str(e)}")
        
        return redirect('admin:products_dashboard')
    
    def data_validation(self, request):
        """Data validation view"""
        context = {
            'title': 'Data Validation & Quality Control',
            'opts': self.model._meta,
        }
        return render(request, 'admin/products/data_validation.html', context)
    
    def brand_hierarchy(self, request):
        """Brand hierarchy view"""
        brands = Product.objects.values('brand').annotate(
            total_products=Count('id'),
            categories=Count('category', distinct=True)
        ).order_by('-total_products')
        
        context = {
            'title': 'Brand Hierarchy Management',
            'opts': self.model._meta,
            'brands': brands,
        }
        return render(request, 'admin/products/brand_hierarchy.html', context)
    
    def category_view(self, request):
        """Category management view"""
        categories = Product.objects.values('category').annotate(
            total_products=Count('id'),
            brands=Count('brand', distinct=True)
        ).order_by('-total_products')
        
        context = {
            'title': 'Category Management',
            'opts': self.model._meta,
            'categories': categories,
        }
        return render(request, 'admin/products/category_view.html', context)
    
    def collection_view(self, request):
        """Collection management view"""
        context = {
            'title': 'Collection Management',
            'opts': self.model._meta,
        }
        return render(request, 'admin/products/collection_view.html', context)


# Enhanced admin classes for related models
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_url_preview', 'is_primary', 'image_type', 'created_at']
    list_filter = ['is_primary', 'image_type', 'created_at']
    search_fields = ['product__title', 'alt_text']
    list_per_page = 50
    ordering = ['-created_at']
    
    def image_url_preview(self, obj):
        """Show image preview"""
        if obj.image_url:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;"></a>',
                obj.image_url, obj.image_url
            )
        return "No Image"
    image_url_preview.short_description = 'Preview'

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value_preview', 'created_at']
    search_fields = ['product__title', 'name', 'value']
    list_filter = ['name', 'created_at']
    list_per_page = 50
    ordering = ['product', 'name']
    
    def value_preview(self, obj):
        """Show truncated value"""
        if len(obj.value) > 50:
            return obj.value[:50] + '...'
        return obj.value
    value_preview.short_description = 'Value'

@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ['product', 'title', 'document_type_badge', 'document_link', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['product__title', 'title']
    list_per_page = 50
    ordering = ['-created_at']
    
    def document_type_badge(self, obj):
        """Display document type as badge"""
        colors = {
            'manual': '#007bff', 'installation': '#28a745', 
            'warranty': '#ffc107', 'specification': '#17a2b8'
        }
        color = colors.get(obj.document_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">{}</span>',
            color, obj.document_type.title()
        )
    document_type_badge.short_description = 'Type'
    
    def document_link(self, obj):
        """Show document link"""
        return format_html(
            '<a href="{}" target="_blank" style="color: #007bff;">📄 View</a>',
            obj.document_url
        )
    document_link.short_description = 'Link'

@admin.register(RelatedProduct)
class RelatedProductAdmin(admin.ModelAdmin):
    list_display = ['main_product', 'related_product', 'relationship_badge', 'is_mandatory', 'created_at']
    list_filter = ['relationship_type', 'is_mandatory', 'created_at']
    search_fields = ['main_product__title', 'related_product__title']
    list_per_page = 50
    ordering = ['-created_at']
    
    def relationship_badge(self, obj):
        """Display relationship type as badge"""
        return format_html(
            '<span style="background-color: #6f42c1; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">{}</span>',
            obj.get_relationship_type_display()
        )
    relationship_badge.short_description = 'Relationship'

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant_type', 'variant_value', 'price_modifier_formatted']
    list_filter = ['variant_type']
    search_fields = ['product__title', 'variant_value']
    list_per_page = 50
    ordering = ['product', 'variant_type']
    
    def price_modifier_formatted(self, obj):
        """Format price modifier"""
        if obj.price_modifier > 0:
            return format_html(
                '<span style="color: #28a745;">+${:.2f}</span>',
                obj.price_modifier
            )
        elif obj.price_modifier < 0:
            return format_html(
                '<span style="color: #dc3545;">${:.2f}</span>',
                obj.price_modifier
            )
        return '$0.00'
    price_modifier_formatted.short_description = 'Price Modifier'

# Register the main Product admin - SINGLE REGISTRATION POINT
admin.site.register(Product, ProductAdmin)

# Customize admin site with professional branding
admin.site.site_header = "🏢 Product Catalog Control Center"
admin.site.site_title = "Product Admin"
admin.site.index_title = "Welcome to the Product Catalog Management System"
