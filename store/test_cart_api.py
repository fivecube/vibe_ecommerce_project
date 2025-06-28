from django.contrib.auth.models import User
from django.test import Client, TestCase

from .models import CartItem, Category, Product


class CartAPITestCase(TestCase):
    def setUp(self):
        # Create a user and log in
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client()
        self.client.login(username='testuser', password='testpass')

        # Create a category and product
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='iPhone',
            description='A smartphone',
            price=100,
            category=self.category,
            stock_quantity=10,
            is_active=True
        )

    def test_delete_cart_item_flow(self):
        # 1. Add to cart
        response = self.client.post('/api/cart/add/', {
            'product_id': self.product.id,
            'quantity': 1
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('cart_total_items', response.json())

        # 2. Check item is added (get cart)
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, 200)
        cart_data = response.json()
        self.assertEqual(cart_data['total_items'], 1)
        self.assertEqual(len(cart_data['items']), 1)
        item_id = cart_data['items'][0]['item_id']

        # 3. Delete cart item
        response = self.client.delete(f'/api/cart/delete/{item_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())

        # 4. Check item should not exist
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, 200)
        cart_data = response.json()
        self.assertEqual(cart_data['total_items'], 0)
        self.assertEqual(len(cart_data['items']), 0) 