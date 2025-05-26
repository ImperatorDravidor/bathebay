from django.db import models
from django.utils.text import slugify
import os


class Product(models.Model):
    # Basic product information
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=100)
    
    # Product categorization
    category = models.CharField(max_length=200, blank=True)
    subcategory = models.CharField(max_length=200, blank=True)
    
    # Product specifications (stored as JSON-like text)
    specifications = models.TextField(blank=True, help_text="JSON format specifications")
    
    # URLs and metadata
    source_url = models.URLField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['brand', 'title']
        indexes = [
            models.Index(fields=['brand']),
            models.Index(fields=['category']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return f"{self.brand} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand}-{self.title}")
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    local_path = models.ImageField(upload_to='products/', blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'id']
    
    def __str__(self):
        return f"Image for {self.product.title}"
    
    @property
    def filename(self):
        if self.local_path:
            return os.path.basename(self.local_path.name)
        return None
