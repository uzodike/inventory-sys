# stock/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Product, Category

User = get_user_model()

class TransactionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create users: one manager and one cashier
        self.manager = User.objects.create_user(username='manager', password='managerpass', role='manager')
        self.cashier = User.objects.create_user(username='cashier', password='cashierpass', role='cashier')
        # Create a category and product
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(name='Laptop', category=self.category, quantity=10, price=1000.00)

    def authenticate(self, user):
        response = self.client.post('/api/accounts/auth/jwt/create/', {'username': user.username, 'password': 'managerpass' if user.username == 'manager' else 'cashierpass'}, format='json')
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_non_manager_cannot_restock(self):
        # Cashier should not be allowed to restock.
        self.authenticate(self.cashier)
        url = '/api/stock/restock/'
        data = {'product': self.product.id, 'quantity': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sale_updates_product_quantity(self):
        # A sale transaction should reduce product quantity.
        self.authenticate(self.cashier)
        url = '/api/stock/sales/'
        data = {'product': self.product.id, 'quantity': 3}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 10 - 3)

    def test_restock_updates_product_quantity(self):
        # A restock transaction should increase product quantity.
        self.authenticate(self.manager)
        url = '/api/stock/restock/'
        data = {'product': self.product.id, 'quantity': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 10 + 5)

    def test_insufficient_stock_for_sale(self):
        # Trying to sell more than available should return an error.
        self.authenticate(self.cashier)
        url = '/api/stock/sales/'
        data = {'product': self.product.id, 'quantity': 20}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data.get('detail', ''))

