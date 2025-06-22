from django.urls import path
from . import views

# Define the URL patterns for the store app
urlpatterns = [
    # This pattern maps the 'products/' URL to our product_list view
    path('products/', views.product_list, name='product-list'),
] 