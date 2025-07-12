import json

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Cart, CartItem, Order, OrderItem, Product, User

# Create your views here.

@csrf_exempt
@require_POST
def login_user(request):
    """
    API view to authenticate user and create session.
    Expects JSON with 'username' and 'password'.
    Returns session information for UI use.
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    
    # Authenticate user
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        # Log in the user (creates session)
        login(request, user)
        
        # Get session key for UI use
        session_key = request.session.session_key
        
        return JsonResponse({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            },
            'session_id': session_key,
            'authenticated': True
        })
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

@csrf_exempt
@require_POST
def logout_user(request):
    """
    API view to logout user and destroy session.
    """
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({
            'message': 'Logout successful',
            'authenticated': False
        })
    else:
        return JsonResponse({'error': 'No user is currently logged in'}, status=400)

@csrf_exempt
def check_auth_status(request):
    """
    API view to check if user is authenticated and return user info.
    """
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            },
            'session_id': request.session.session_key
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'user': None
        })

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

def get_cart(request):
    """
    API view to get the current user's cart with all items.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        cart = Cart.objects.get(user=request.user, is_active=True)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        
        data = {
            'cart_id': cart.id,
            'total_items': cart.get_total_quantity(),
            'total_price': str(cart.get_total_price()),
            'is_empty': cart.is_empty(),
            'items': [
                {
                    'item_id': item.id,  # This is the item_id you need for deletion
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'product_sku': item.product.sku,
                    'quantity': item.quantity,
                    'price_per_unit': str(item.price),
                    'total_price': str(item.get_total_price()),
                    'currency': item.currency,
                    'added_at': timezone.localtime(item.added_at).strftime("%B %d, %Y, %I:%M %p"),
                }
                for item in cart_items
            ]
        }
        
        return JsonResponse(data)
        
    except Cart.DoesNotExist:
        # User has no active cart
        return JsonResponse({
            'cart_id': None,
            'total_items': 0,
            'total_price': '0.00',
            'is_empty': True,
            'items': []
        })

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

@csrf_exempt
def delete_cart_item(request, item_id):
    """
    API view to delete a specific cart item.
    Accepts both POST and DELETE methods.
    The user must be authenticated and the cart item must belong to them.
    """
    if request.method not in ['POST', 'DELETE']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # Get the cart item and ensure it belongs to the current user
        cart_item = CartItem.objects.select_related('cart', 'product').get(
            id=item_id,
            cart__user=request.user,
            cart__is_active=True
        )
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Cart item not found'}, status=404)

    # Store product name for response message
    product_name = cart_item.product.name
    quantity = cart_item.quantity
    
    # Delete the cart item
    cart_item.delete()
    
    # Get updated cart info
    cart = cart_item.cart
    
    return JsonResponse({
        'message': f'{quantity}x {product_name} removed from cart successfully',
        'cart_total_items': cart.get_total_quantity(),
        'cart_total_price': str(cart.get_total_price()),
    })

@csrf_exempt
@require_POST
def checkout(request):
    """
    API view to perform checkout (COD only).
    - Creates an Order and OrderItems from the user's cart.
    - Deletes CartItems after successful order creation.
    - Returns the new Order details.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        cart = Cart.objects.get(user=request.user, is_active=True)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        if not cart_items.exists():
            return JsonResponse({'error': 'Cart is empty'}, status=400)
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'No active cart found'}, status=400)

    # For now, only support COD
    data = json.loads(request.body or '{}')
    shipping_address = data.get('shipping_address', '')
    billing_address = data.get('billing_address', shipping_address)
    cod = data.get('cod', True)

    with transaction.atomic():
        # Create the order
        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total_price(),
            currency='USD',
            shipping_address=shipping_address,
            billing_address=billing_address,
            cod=cod,
            status='PENDING',
        )
        # Create order items and delete cart items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.price,
                currency=cart_item.currency,
            )
            cart_item.delete()
        # Optionally, mark cart as inactive
        cart.is_active = False
        cart.save()

    return JsonResponse({
        'message': 'Order placed successfully',
        'order_id': order.order_id,
        'order_status': order.status,
        'total_price': str(order.total_price),
        'cod': order.cod,
    })

@csrf_exempt
def list_orders(request):
    """
    API view to list all orders for the authenticated user, summary only (no order items, no addresses).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    data = {
        'orders': [
            {
                'order_id': order.order_id,
                'status': order.status,
                'total_price': str(order.total_price),
                'currency': order.currency,
                'cod': order.cod,
                'created_at': timezone.localtime(order.created_at).strftime("%B %d, %Y, %I:%M %p"),
                'total_items': order.get_total_quantity(),
            }
            for order in orders
        ]
    }
    return JsonResponse(data)

@csrf_exempt
def order_detail(request, order_id):
    """
    API view to get details of a specific order for the authenticated user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        order = Order.objects.prefetch_related('items__product').get(user=request.user, order_id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

    data = {
        'order_id': order.order_id,
        'status': order.status,
        'total_price': str(order.total_price),
        'currency': order.currency,
        'cod': order.cod,
        'created_at': timezone.localtime(order.created_at).strftime("%B %d, %Y, %I:%M %p"),
        'shipping_address': order.shipping_address,
        'billing_address': order.billing_address,
        'items': [
            {
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': str(item.price),
                'currency': item.currency,
                'total_price': str(item.get_total_price()),
            }
            for item in order.items.all()
        ]
    }
    return JsonResponse(data)

@csrf_exempt
def cancel_order(request, order_id):
    """
    API view to cancel an order for the authenticated user.
    Only allows cancellation if order is in PENDING or ACCEPTED status.
    Accepts POST or DELETE methods.
    """
    if request.method not in ["POST", "DELETE"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    try:
        order = Order.objects.get(user=request.user, order_id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    if order.status not in ["PENDING", "ACCEPTED"]:
        return JsonResponse({"error": f"Order cannot be cancelled in its current status: {order.status}"}, status=400)
    order.status = "CANCELLED"
    order.save()
    return JsonResponse({
        "message": f"Order {order.order_id} cancelled successfully.",
        "order_id": order.order_id,
        "status": order.status
    })
