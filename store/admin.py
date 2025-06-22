from django.contrib import admin
from .models import Category, Product

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
