from django.contrib import admin
from django import forms
from .models import Category, Product, Cart, CartItem

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    ordering = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'sku']
    list_editable = ['price', 'stock_quantity', 'is_active']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_active', 'sku')
        }),
        ('Physical Details', {
            'fields': ('weight', 'length', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total_price', 'get_total_quantity', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_total_price(self, obj):
        return f"${obj.get_total_price()}"
    get_total_price.short_description = 'Total Price'
    
    def get_total_quantity(self, obj):
        return obj.get_total_quantity()
    get_total_quantity.short_description = 'Total Items'

class CartItemAdminForm(forms.ModelForm):
    """Custom form for CartItem to make price not required and relabel it as Unit Price"""
    class Meta:
        model = CartItem
        fields = '__all__'
        labels = {
            'price': 'Unit Price',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].required = False
        self.fields['price'].label = 'Unit Price'
        self.fields['price'].help_text = 'Will auto-populate with product price if left empty. You can override if needed.'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    form = CartItemAdminForm
    list_display = ['cart', 'product', 'quantity', 'price', 'currency', 'get_total_price', 'added_at']
    list_filter = ['added_at', 'product__category', 'currency']
    search_fields = ['product__name', 'cart__user__username']
    readonly_fields = ['added_at', 'updated_at', 'total_price']
    ordering = ['-added_at']

    def get_total_price(self, obj):
        return obj.get_display_total_price()
    get_total_price.short_description = 'Total Price'

    def total_price(self, obj):
        return obj.get_display_total_price()
    total_price.short_description = 'Total Price'
