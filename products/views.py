from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from .models import Product, ProductImage, ProductSpecification, ProductDocument, RelatedProduct
import json

def home(request):
    """Homepage with featured products and brand showcase"""
    # Get featured products (latest or most popular)
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    # Get all brands with product counts
    brands = Product.objects.filter(is_active=True).values('brand').annotate(
        product_count=Count('id')
    ).order_by('brand')
    
    # Get categories with product counts
    categories = Product.objects.filter(is_active=True).values('category').annotate(
        product_count=Count('id')
    ).order_by('category')
    
    context = {
        'featured_products': featured_products,
        'brands': brands,
        'categories': categories,
        'total_products': Product.objects.filter(is_active=True).count(),
    }
    return render(request, 'products/home.html', context)

def product_list(request):
    """Product listing with hierarchical filtering and pagination"""
    products = Product.objects.filter(is_active=True).prefetch_related('images').order_by('-created_at')
    
    # Get filtering parameters
    brand = request.GET.get('brand', '').strip()
    category = request.GET.get('category', '').strip()
    collection = request.GET.get('collection', '').strip()
    search = request.GET.get('search', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    
    # Apply hierarchical filters
    if brand:
        products = products.filter(brand__iexact=brand)
    
    if category:
        products = products.filter(category__iexact=category)
    
    # Collection filtering (this would need to be implemented based on your data structure)
    # For now, we'll use it as an additional search term
    if collection:
        products = products.filter(
            Q(title__icontains=collection) |
            Q(short_description__icontains=collection) |
            Q(full_description__icontains=collection)
        )
    
    # Search filtering
    if search:
        products = products.filter(
            Q(title__icontains=search) |
            Q(short_description__icontains=search) |
            Q(full_description__icontains=search) |
            Q(brand__icontains=search) |
            Q(sku__icontains=search) |
            Q(model__icontains=search)
        )
    
    # Price filtering
    if min_price:
        try:
            min_val = float(min_price)
            products = products.filter(price__gte=min_val)
        except (ValueError, TypeError):
            pass
    
    if max_price:
        try:
            max_val = float(max_price)
            products = products.filter(price__lte=max_val)
        except (ValueError, TypeError):
            pass
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for sidebar
    all_brands = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct().order_by('brand')
    all_categories = Product.objects.filter(is_active=True).values_list('category', flat=True).distinct().order_by('category')
    
    # Get categories for selected brand
    brand_categories = []
    if brand:
        brand_categories = Product.objects.filter(
            is_active=True, 
            brand__iexact=brand
        ).values_list('category', flat=True).distinct().order_by('category')
    
    # Build page title based on filters
    page_title = "All Products"
    if brand and category and collection:
        page_title = f"{brand} - {category} - {collection}"
    elif brand and category:
        page_title = f"{brand} - {category}"
    elif brand:
        page_title = f"{brand} Products"
    elif category:
        page_title = f"{category} Products"
    elif search:
        page_title = f"Search Results for '{search}'"
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'all_brands': all_brands,
        'all_categories': all_categories,
        'brand_categories': brand_categories,
        'page_title': page_title,
        'total_results': products.count(),
        'current_filters': {
            'brand': brand,
            'category': category,
            'collection': collection,
            'search': search,
            'min_price': min_price,
            'max_price': max_price,
        }
    }
    return render(request, 'products/product_list.html', context)

def brand_products(request, brand_name):
    """Products filtered by brand"""
    products = Product.objects.filter(
        is_active=True, 
        brand__iexact=brand_name
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'brand_name': brand_name,
        'total_products': products.count(),
    }
    return render(request, 'products/brand_products.html', context)

def category_products(request, category_name):
    """Products filtered by category"""
    products = Product.objects.filter(
        is_active=True, 
        category__iexact=category_name
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'category_name': category_name,
        'total_products': products.count(),
    }
    return render(request, 'products/category_products.html', context)

def product_detail(request, slug):
    """Product detail page by slug"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return _render_product_detail(request, product)

def product_detail_by_id(request, pk):
    """Product detail page by ID"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return _render_product_detail(request, product)

def _render_product_detail(request, product):
    """Helper function to render product detail"""
    # Get related data
    images = ProductImage.objects.filter(product=product).order_by('is_primary', 'id')
    specifications = ProductSpecification.objects.filter(product=product).order_by('name')
    documents = ProductDocument.objects.filter(product=product).order_by('document_type', 'title')
    
    # Get related products
    related_products = RelatedProduct.objects.filter(
        main_product=product
    ).select_related('related_product')
    
    # Group related products by type
    related_by_type = {}
    for rel in related_products:
        rel_type = rel.get_relationship_type_display()
        if rel_type not in related_by_type:
            related_by_type[rel_type] = []
        related_by_type[rel_type].append(rel)
    
    # Get similar products (same brand or category)
    similar_products = Product.objects.filter(
        Q(brand=product.brand) | Q(category=product.category),
        is_active=True
    ).exclude(id=product.id)[:6]
    
    context = {
        'product': product,
        'images': images,
        'specifications': specifications,
        'documents': documents,
        'related_by_type': related_by_type,
        'similar_products': similar_products,
        'primary_image': images.filter(is_primary=True).first() or images.first(),
    }
    return render(request, 'products/product_detail.html', context)

def search_products(request):
    """Search products"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(full_description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__icontains=query) |
            Q(sku__icontains=query) |
            Q(model__icontains=query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'query': query,
        'total_results': products.count(),
    }
    return render(request, 'products/search_results.html', context)

# API Views for AJAX requests
@require_http_methods(["GET"])
def api_brands(request):
    """API endpoint to get all brands"""
    brands = Product.objects.filter(is_active=True).values('brand').annotate(
        product_count=Count('id')
    ).order_by('brand')
    
    return JsonResponse({
        'brands': list(brands)
    })

@require_http_methods(["GET"])
def api_categories(request):
    """API endpoint to get all categories"""
    categories = Product.objects.filter(is_active=True).values('category').annotate(
        product_count=Count('id')
    ).order_by('category')
    
    return JsonResponse({
        'categories': list(categories)
    })

@require_http_methods(["GET"])
def api_hierarchy(request):
    """API endpoint to get product hierarchy"""
    from .product_hierarchy import get_flat_structure
    
    return JsonResponse({
        'hierarchy': get_flat_structure()
    })
