from django.db.models import Count
from .models import Product
from .product_hierarchy import get_flat_structure, get_all_brands, PRODUCT_HIERARCHY

def global_context(request):
    """
    Context processor to provide global data to all templates
    """
    # Get top brands with product counts (only if products exist)
    top_brands = Product.objects.filter(is_active=True).values('brand').annotate(
        product_count=Count('id')
    ).order_by('-product_count')[:10]
    
    # Get top categories with product counts (only if products exist)
    top_categories = Product.objects.filter(is_active=True).values('category').annotate(
        product_count=Count('id')
    ).order_by('-product_count')[:8]
    
    # Only include non-empty categories and brands
    top_brands = [b for b in top_brands if b['brand'] and b['brand'].strip()]
    top_categories = [c for c in top_categories if c['category'] and c['category'].strip()]
    
    return {
        'global_top_brands': top_brands,
        'global_top_categories': top_categories,
    }

def product_hierarchy(request):
    """
    Context processor to make product hierarchy available in all templates
    """
    return {
        'product_hierarchy': get_flat_structure(),
        'all_brands': get_all_brands(),
        'hierarchy_data': PRODUCT_HIERARCHY
    } 