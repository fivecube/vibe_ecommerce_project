from django.db import models
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    """Product category model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    """Product model for e-commerce store"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="in USD ($)")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="in grams (g)")
    length = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="in cm")
    width = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="in cm")
    height = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="in cm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0

    def get_display_price(self):
        """Return formatted price"""
        return f"${self.price}"

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            self.sku = f"SKU-{self.id or 'NEW'}-{timezone.now().strftime('%Y%m%d')}"
        super().save(*args, **kwargs)