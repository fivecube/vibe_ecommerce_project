from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from .models import Product

# Create your views here.

def product_list(request):
    """
    API view to list all products with their categories.
    """
    # Fetch all product objects, and pre-fetch the related category
    # to avoid extra database queries.
    products = Product.objects.all().select_related('category')
    
    # Prepare the data in a list of dictionaries
    data = {
        'products': [
            {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.get_display_price(),  # Use model method for currency
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                },
                'stock_quantity': product.stock_quantity,
                'is_active': product.is_active,
                'sku': product.sku,
                # Add units to dimensions
                'weight': f"{product.weight} g" if product.weight is not None else None,
                'length': f"{product.length} cm" if product.length is not None else None,
                'width': f"{product.width} cm" if product.width is not None else None,
                'height': f"{product.height} cm" if product.height is not None else None,
                # Format timestamps to be human-readable
                'created_at': timezone.localtime(product.created_at).strftime("%B %d, %Y, %I:%M %p"),
                'updated_at': timezone.localtime(product.updated_at).strftime("%B %d, %Y, %I:%M %p"),
            }
            for product in products
        ]
    }
    
    # Return the data as a JSON response
    return JsonResponse(data)
