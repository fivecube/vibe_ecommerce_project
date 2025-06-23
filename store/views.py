from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from .models import Product, Cart, CartItem, User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json

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

@csrf_exempt
@require_POST
def add_to_cart(request):
    """
    API view to add a product to the cart.
    Expects a JSON body with 'product_id' and 'quantity'.
    The user is identified from the request session.
    """
    if not request.user.is_authenticated:
        return HttpResponse(json.dumps({'error': 'Authentication required'}), content_type='application/json', status=401)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id or quantity < 1:
            return HttpResponseBadRequest(json.dumps({'error': 'Invalid product_id or quantity'}), content_type='application/json')

    except (json.JSONDecodeError, TypeError, ValueError):
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid or missing JSON data'}), content_type='application/json')

    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if created:
            final_quantity = quantity
        else:
            final_quantity = cart_item.quantity + quantity

        if product.stock_quantity < final_quantity:
            return JsonResponse({'error': f'Not enough stock for {product.name}. Only {product.stock_quantity} available.'}, status=400)

        cart_item.quantity = final_quantity
        cart_item.save()

    return JsonResponse({
        'message': f'{product.name} added to cart successfully',
        'cart_total_items': cart.get_total_quantity(),
    })
