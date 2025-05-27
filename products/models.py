from django.db import models
from django.utils.text import slugify
import os


class Product(models.Model):
    # Basic product information
    title = models.CharField(max_length=500)
    short_description = models.TextField(blank=True)
    full_description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    
    brand = models.CharField(max_length=100)
    
    # Product categorization
    category = models.CharField(max_length=200, blank=True)
    subcategory = models.CharField(max_length=200, blank=True)
    
    # Product details
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=200, blank=True)
    series = models.CharField(max_length=200, blank=True)
    
    # Product specifications and details
    specifications = models.TextField(blank=True, help_text="JSON format specifications")
    features = models.TextField(blank=True, help_text='Product features')
    technical_info = models.TextField(blank=True, help_text='Technical details and requirements')
    important_details = models.TextField(blank=True, help_text="Important details like 'sold separately' items")
    includes = models.TextField(blank=True, help_text="What's included in the box")
    inspiration_content = models.TextField(blank=True, help_text='Inspiration content and links')
    
    # Physical attributes
    dimensions = models.CharField(max_length=200, blank=True)
    weight = models.CharField(max_length=100, blank=True)
    
    # Media
    youtube_links = models.TextField(blank=True, help_text='JSON array of YouTube video URLs')
    
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
        if not self.slug or kwargs.get('force_insert'):
            base_slug_text = f"{self.brand}-{self.title}"
            self.slug = slugify(f"{base_slug_text}-{self.sku}")
            
            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    local_path = models.ImageField(upload_to='products/', blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    image_type = models.CharField(max_length=50, blank=True, help_text='e.g., main, gallery, technical, lifestyle')
    
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


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_type = models.CharField(max_length=100, help_text='e.g., Panel Options, Color, Size')
    variant_value = models.CharField(max_length=200, help_text='e.g., Black, Glass, Mirror')
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Price difference from base product')
    sku_suffix = models.CharField(max_length=50, blank=True, help_text='Additional SKU identifier for this variant')
    
    def __str__(self):
        return f"{self.product.title} - {self.variant_type}: {self.variant_value}"


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_specifications')
    name = models.CharField(max_length=100)
    value = models.TextField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['product', 'name']
    
    def __str__(self):
        return f"{self.product.title} - {self.name}: {self.value}"


class ProductDocument(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_url = models.URLField(max_length=500)
    document_type = models.CharField(max_length=50, blank=True, help_text='e.g., manual, warranty, specification')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.title} - {self.title}"


class RelatedProduct(models.Model):
    RELATIONSHIP_CHOICES = [
        ('required_operation', 'Required for Operation'),
        ('heater_control', 'Sauna Heater Controls'),
        ('recommended', 'Recommended'),
        ('related_item', 'Related Items'),
        ('accessory', 'Accessory'),
        ('replacement_part', 'Replacement Part'),
    ]
    
    main_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_products_as_main')
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='appears_as_related_in')
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    description = models.TextField(blank=True, help_text='Description of the relationship')
    quantity_needed = models.IntegerField(default=1, help_text='How many of this item are needed')
    is_mandatory = models.BooleanField(default=False, help_text='Is this item mandatory for operation')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('main_product', 'related_product', 'relationship_type')
    
    def __str__(self):
        return f"{self.main_product.title} -> {self.related_product.title} ({self.get_relationship_type_display()})"
