from django.urls import path

from . import views

# Define the URL patterns for the store app
urlpatterns = [
    # This pattern maps the 'products/' URL to our product_list view
    path('products/', views.product_list, name='product-list'),
    # This pattern maps the 'cart/' URL to our get_cart view
    path('cart/', views.get_cart, name='get-cart'),
    path('cart/add/', views.add_to_cart, name='add-to-cart'),
    path('cart/delete/<int:item_id>/', views.delete_cart_item, name='delete-cart-item'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.list_orders, name='list-orders'),
    path('orders/<str:order_id>/', views.order_detail, name='order-detail'),
    path('orders/<str:order_id>/cancel/', views.cancel_order, name='cancel-order'),
] 