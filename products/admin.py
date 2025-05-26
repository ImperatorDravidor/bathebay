from django.contrib import admin
from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'brand', 'category', 'price', 'sku', 'is_active', 'created_at')
    list_filter = ('brand', 'category', 'is_active', 'created_at')
    search_fields = ('title', 'sku', 'brand', 'description')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'price', 'sku', 'brand')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory')
        }),
        ('Technical Details', {
            'fields': ('specifications', 'source_url')
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_primary', 'filename', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__title', 'alt_text')
    readonly_fields = ('created_at', 'filename')
