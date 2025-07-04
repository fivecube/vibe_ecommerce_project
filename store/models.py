from django.contrib.auth.models import User
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

class Cart(models.Model):
    """Shopping cart model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart for {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"

    def get_total_price(self):
        """Calculate total price of all items in cart"""
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_quantity(self):
        """Calculate total quantity of all items in cart"""
        return sum(item.quantity for item in self.items.all())

    def is_empty(self):
        """Check if cart is empty"""
        return self.items.count() == 0

    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()

class CartItem(models.Model):
    """Individual item in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at the time of adding to cart")
    currency = models.CharField(max_length=8, default='USD', help_text="Currency code, e.g. USD, EUR")
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart} ({self.currency})"

    def get_total_price(self):
        """Calculate total price for this item"""
        if self.price is not None:
            return self.price * self.quantity
        return 0

    def get_display_total_price(self):
        """Return formatted total price for this item"""
        return f"{self.currency} {self.get_total_price()}"

    def save(self, *args, **kwargs):
        # Set price from product if not already set
        if not self.price:
            self.price = self.product.price
        if not self.currency:
            self.currency = 'USD'
        # Ensure quantity doesn't exceed available stock
        if self.quantity > self.product.stock_quantity:
            self.quantity = self.product.stock_quantity
        super().save(*args, **kwargs)

class Order(models.Model):
    """Order model representing a completed purchase"""
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("PACKED", "Packed"),
        ("DISPATCHED", "Dispatched"),
        ("IN_TRANSIT", "In Transit"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]
    order_id = models.CharField(max_length=32, unique=True, blank=True, help_text="Unique Order ID (auto-generated)")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PENDING', help_text="Order status")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default='USD', help_text="Currency code, e.g. USD, EUR")
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    cod = models.BooleanField(default=False, help_text="Is this order Cash on Delivery?")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id or self.id} by {self.user.username} ({self.status})"

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def save(self, *args, **kwargs):
        if not self.order_id:
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(created_at__date=datetime.now().date()).order_by('-id').first()
            next_num = 1
            if last_order and last_order.order_id and last_order.order_id.startswith(f'ORD-{today}'):
                try:
                    next_num = int(last_order.order_id.split('-')[-1]) + 1
                except Exception:
                    pass
            self.order_id = f"ORD-{today}-{next_num:04d}"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    """Individual item in an order (structure mirrors CartItem)"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at the time of ordering")
    currency = models.CharField(max_length=8, default='USD', help_text="Currency code, e.g. USD, EUR")
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Order #{self.order.id} ({self.currency})"

    def get_total_price(self):
        if self.price is not None:
            return self.price * self.quantity
        return 0

    def get_display_total_price(self):
        return f"{self.currency} {self.get_total_price()}"