# stock/serializers.py
from rest_framework import serializers
from .models import Category, Product, Transaction

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'product', 'quantity', 'transaction_type', 'timestamp', 'created_by']
        read_only_fields = ['transaction_type', 'timestamp', 'created_by']
