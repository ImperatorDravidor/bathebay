from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils.html import format_html
from .models import Product, ProductImage, ProductSpecification, ProductDocument, RelatedProduct, ProductVariant
from .scraper_enhanced import EnhancedBathingBrandsScraper
import json
import logging

logger = logging.getLogger(__name__)

class HierarchyAdminMixin:
    """Mixin for hierarchy-based admin views"""
    
    def get_brand_stats(self):
        """Get statistics for all brands"""
        brands = Product.objects.values('brand').annotate(
            product_count=Count('id'),
            categories=Count('category', distinct=True)
        ).order_by('brand')
        
        brand_stats = {}
        for brand_data in brands:
            brand_name = brand_data['brand']
            categories = Product.objects.filter(brand=brand_name).values('category').annotate(
                product_count=Count('id'),
                subcategories=Count('subcategory', distinct=True)
            ).order_by('category')
            
            brand_stats[brand_name] = {
                'total_products': brand_data['product_count'],
                'total_categories': brand_data['categories'],
                'categories': list(categories)
            }
        
        return brand_stats

@method_decorator(staff_member_required, name='dispatch')
class BrandHierarchyView(TemplateView, HierarchyAdminMixin):
    """Main brand selection view"""
    template_name = 'admin/products/brand_hierarchy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': '🏢 Brand Hierarchy Manager',
            'brand_stats': self.get_brand_stats(),
            'total_products': Product.objects.count(),
            'total_brands': Product.objects.values('brand').distinct().count(),
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class CategoryView(TemplateView, HierarchyAdminMixin):
    """Category view for a specific brand"""
    template_name = 'admin/products/category_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = kwargs.get('brand')
        
        categories = Product.objects.filter(brand=brand).values('category').annotate(
            product_count=Count('id'),
            subcategories=Count('subcategory', distinct=True)
        ).order_by('category')
        
        context.update({
            'title': f'📂 {brand} Categories',
            'brand': brand,
            'categories': categories,
            'brand_product_count': Product.objects.filter(brand=brand).count(),
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class CollectionView(TemplateView, HierarchyAdminMixin):
    """Collection view for a specific brand and category"""
    template_name = 'admin/products/collection_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = kwargs.get('brand')
        category = kwargs.get('category')
        
        collections = Product.objects.filter(
            brand=brand, 
            category=category
        ).values('subcategory').annotate(
            product_count=Count('id')
        ).order_by('subcategory')
        
        context.update({
            'title': f'📦 {brand} → {category} Collections',
            'brand': brand,
            'category': category,
            'collections': collections,
            'category_product_count': Product.objects.filter(brand=brand, category=category).count(),
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class ProductListView(TemplateView, HierarchyAdminMixin):
    """Product list view for a specific collection"""
    template_name = 'admin/products/product_list_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = kwargs.get('brand')
        category = kwargs.get('category')
        collection = kwargs.get('collection')
        
        products = Product.objects.filter(
            brand=brand,
            category=category,
            subcategory=collection
        ).select_related().prefetch_related('images', 'product_specifications')
        
        context.update({
            'title': f'🛍️ {brand} → {category} → {collection} Products',
            'brand': brand,
            'category': category,
            'collection': collection,
            'products': products,
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class ScrapingControlView(TemplateView):
    """Scraping control interface"""
    template_name = 'admin/products/scraping_control.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scraper = EnhancedBathingBrandsScraper()
        
        # Get available brands from scraper
        known_brands = scraper.known_brands
        
        context.update({
            'title': '🚀 Scraping Control Center',
            'known_brands': known_brands,
            'scraped_brands': Product.objects.values('brand').distinct(),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle scraping requests"""
        action = request.POST.get('action')
        
        if action == 'scrape_brand':
            brand = request.POST.get('brand')
            limit = request.POST.get('limit', 10)
            return self.scrape_brand(brand, int(limit))
        
        elif action == 'scrape_category':
            brand = request.POST.get('brand')
            category = request.POST.get('category')
            limit = request.POST.get('limit', 5)
            return self.scrape_category(brand, category, int(limit))
        
        elif action == 'scrape_product':
            url = request.POST.get('url')
            return self.scrape_single_product(url)
        
        return JsonResponse({'status': 'error', 'message': 'Invalid action'})
    
    def scrape_brand(self, brand, limit):
        """Scrape products for a specific brand"""
        try:
            scraper = EnhancedBathingBrandsScraper()
            products = scraper.run_intelligent_scraper(target_brand=brand, limit=limit)
            
            return JsonResponse({
                'status': 'success',
                'message': f'Successfully scraped {len(products)} products for {brand}',
                'products_count': len(products)
            })
        except Exception as e:
            logger.error(f"Error scraping brand {brand}: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    def scrape_category(self, brand, category, limit):
        """Scrape products for a specific category"""
        try:
            scraper = EnhancedBathingBrandsScraper()
            products = scraper.run_intelligent_scraper(
                target_brand=brand, 
                target_category=category, 
                limit=limit
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'Successfully scraped {len(products)} products for {brand} → {category}',
                'products_count': len(products)
            })
        except Exception as e:
            logger.error(f"Error scraping category {brand} → {category}: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    def scrape_single_product(self, url):
        """Scrape a single product"""
        try:
            scraper = EnhancedBathingBrandsScraper()
            product_data = scraper.extract_product_data(url)
            
            if product_data:
                product = scraper.save_product(product_data)
                if product:
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Successfully scraped: {product.title}',
                        'product_id': product.id
                    })
            
            return JsonResponse({'status': 'error', 'message': 'Failed to scrape product'})
        except Exception as e:
            logger.error(f"Error scraping product {url}: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

# Hierarchical admin classes will be added later
# class CollectionInline(admin.TabularInline):
# class CategoryInline(admin.TabularInline):
# class ProductInline(admin.TabularInline):
# class BrandAdmin(admin.ModelAdmin):
# class CategoryAdmin(admin.ModelAdmin):
# class CollectionAdmin(admin.ModelAdmin):

class ProductAdmin(admin.ModelAdmin):
    list_display = ['hierarchy_display', 'title', 'sku', 'price', 'created_at', 'action_buttons']
    list_filter = ['brand', 'category', 'subcategory', 'is_active', 'created_at']
    search_fields = ['title', 'sku', 'brand', 'model']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = (
        ('🏢 Brand & Category Hierarchy', {
            'fields': ('brand', 'category', 'subcategory')
        }),
        ('📦 Product Information', {
            'fields': ('title', 'model', 'sku', 'slug')
        }),
        ('💰 Pricing', {
            'fields': ('price', 'retail_price')
        }),
        ('📝 Descriptions', {
            'fields': ('short_description', 'full_description')
        }),
        ('🔧 Technical Details', {
            'fields': ('features', 'technical_info', 'includes', 'inspiration_content')
        }),
        ('📏 Physical Attributes', {
            'fields': ('dimensions', 'weight')
        }),
        ('🔗 External Links', {
            'fields': ('source_url', 'youtube_links')
        }),
        ('⚙️ System', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def hierarchy_display(self, obj):
        """Display the product hierarchy"""
        return format_html(
            '<div style="font-family: monospace;">'
            '<span style="color: #1e88e5;">🏢 {}</span> → '
            '<span style="color: #43a047;">📂 {}</span> → '
            '<span style="color: #fb8c00;">📦 {}</span>'
            '</div>',
            obj.brand, obj.category, obj.subcategory
        )
    hierarchy_display.short_description = 'Hierarchy'
    
    def action_buttons(self, obj):
        """Display action buttons for each product"""
        return format_html(
            '<a class="button" href="{}">View</a> '
            '<a class="button" href="{}">Edit</a>',
            f'/product/{obj.slug}/',
            reverse('admin:products_product_change', args=[obj.pk])
        )
    action_buttons.short_description = 'Actions'
    
    def get_urls(self):
        """Add custom URLs for hierarchy navigation"""
        urls = super().get_urls()
        custom_urls = [
            path('hierarchy/', BrandHierarchyView.as_view(), name='products_brand_hierarchy'),
            path('hierarchy/<str:brand>/', CategoryView.as_view(), name='products_category_view'),
            path('hierarchy/<str:brand>/<str:category>/', CollectionView.as_view(), name='products_collection_view'),
            path('hierarchy/<str:brand>/<str:category>/<str:collection>/', ProductListView.as_view(), name='products_product_list'),
            path('scraping/', ScrapingControlView.as_view(), name='products_scraping_control'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist to show hierarchy dashboard"""
        extra_context = extra_context or {}
        
        # Get hierarchy statistics
        brand_stats = {}
        brands = Product.objects.values('brand').annotate(
            product_count=Count('id'),
            categories=Count('category', distinct=True)
        ).order_by('brand')
        
        for brand_data in brands:
            brand_name = brand_data['brand']
            categories = Product.objects.filter(brand=brand_name).values('category').annotate(
                product_count=Count('id')
            ).order_by('category')
            
            brand_stats[brand_name] = {
                'total_products': brand_data['product_count'],
                'total_categories': brand_data['categories'],
                'categories': list(categories)
            }
        
        extra_context.update({
            'brand_stats': brand_stats,
            'total_products': Product.objects.count(),
            'total_brands': Product.objects.values('brand').distinct().count(),
            'hierarchy_url': reverse('admin:products_brand_hierarchy'),
            'scraping_url': reverse('admin:products_scraping_control'),
        })
        
        return super().changelist_view(request, extra_context)

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_type', 'is_primary', 'alt_text']
    list_filter = ['image_type', 'is_primary']
    search_fields = ['product__title', 'alt_text']

class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value']
    list_filter = ['name']
    search_fields = ['product__title', 'name', 'value']

class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ['product', 'title', 'document_type']
    list_filter = ['document_type']
    search_fields = ['product__title', 'title']

class RelatedProductAdmin(admin.ModelAdmin):
    list_display = ['main_product', 'related_product', 'relationship_type', 'is_mandatory']
    list_filter = ['relationship_type', 'is_mandatory']
    search_fields = ['main_product__title', 'related_product__title']

class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant_type', 'variant_value', 'price_modifier']
    list_filter = ['variant_type']
    search_fields = ['product__title', 'variant_value']

# Register models
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(ProductSpecification, ProductSpecificationAdmin)
admin.site.register(ProductDocument, ProductDocumentAdmin)
admin.site.register(RelatedProduct, RelatedProductAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
# Hierarchical models will be registered later
# admin.site.register(Brand, BrandAdmin)
# admin.site.register(Category, CategoryAdmin)
# admin.site.register(Collection, CollectionAdmin)

# Customize admin site
admin.site.site_header = '🏢 Bathing Brands Hierarchy Manager'
admin.site.site_title = 'Bathing Brands Admin'
admin.site.index_title = 'Brand → Category → Product Management'
