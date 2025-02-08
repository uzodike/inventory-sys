from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Category, Product, Transaction
from .serializers import CategorySerializer, ProductSerializer, TransactionSerializer
from .permissions import IsCashierOrManager, IsManager
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CategoryForm, ProductForm, SalesTransactionForm, RestockTransactionForm
from django.db import transaction

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsManager]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsManager]  # For product management, restrict to managers

# Sales Transaction endpoint – available to cashiers and managers
class SalesTransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsCashierOrManager]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['transaction_type'] = 'sale'
        product_id = data.get('product')
        quantity = int(data.get('quantity', 0))
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_400_BAD_REQUEST)
        # Check if product has sufficient stock for the sale
        if product.quantity < quantity:
            return Response({'detail': 'Insufficient stock for sale.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# Restock Transaction endpoint – available only to managers
class RestockTransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsManager]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['transaction_type'] = 'restock'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@login_required
def manage_categories(request):
    # Allow only managers to access this page.
    if request.user.role != 'manager':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_categories')
    else:
        form = CategoryForm()

    categories = Category.objects.all().order_by('name')
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'stock/manage_categories.html', context)

@login_required
def manage_products(request):
    # Allow only managers to access this page.
    if request.user.role != 'manager':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_products')
    else:
        form = ProductForm()

    products = Product.objects.all().order_by('name')
    context = {
        'form': form,
        'products': products,
    }
    return render(request, 'stock/manage_products.html', context)

@login_required
def manage_sales(request):
    """
    HTML view for recording a sale.
    After a successful sale, renders a receipt page for printing.
    """
    # Allow both cashiers and managers to record sales.
    if request.user.role not in ['cashier', 'manager']:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SalesTransactionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                sale = form.save(commit=False)
                sale.transaction_type = 'sale'
                sale.created_by = request.user
                product = sale.product
                if product.quantity < sale.quantity:
                    form.add_error('quantity', 'Insufficient stock for sale.')
                else:
                    sale.save()  # Save the sale transaction
                    product.quantity -= sale.quantity
                    product.save()
                    # Render a receipt page with sale details.
                    return render(request, 'stock/sales_receipt.html', {'sale': sale})
    else:
        form = SalesTransactionForm()
    
    transactions = Transaction.objects.filter(transaction_type='sale').order_by('-timestamp')
    context = {
        'form': form,
        'transactions': transactions,
    }
    return render(request, 'stock/manage_sales.html', context)



@login_required
def manage_restock(request):
    """
    HTML view for recording restock transactions.
    Only managers are allowed to restock.
    Automatically increments product stock if restock is successful.
    """
    if request.user.role != 'manager':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RestockTransactionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                restock = form.save(commit=False)
                restock.transaction_type = 'restock'
                restock.created_by = request.user
                restock.save()
                product = restock.product
                # Automatic stock balancing: add restocked quantity.
                product.quantity += restock.quantity
                product.save()
                return redirect('manage_restock')
    else:
        form = RestockTransactionForm()
    
    transactions = Transaction.objects.filter(transaction_type='restock').order_by('-timestamp')
    context = {
        'form': form,
        'transactions': transactions,
    }
    return render(request, 'stock/manage_restock.html', context)

# stock/api_views.py

class SalesTransactionAPIView(APIView):
    """
    This view returns a list of sales transactions and renders an HTML form when requested.
    It accepts GET (to list transactions and display the form) and POST (to create a new sale).
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stock/manage_sales.html'
    
    def get(self, request, format=None):
        # Retrieve all sales transactions (ordered by most recent)
        transactions = Transaction.objects.filter(transaction_type='sale').order_by('-timestamp')
        serializer = TransactionSerializer(transactions, many=True)
        # Prepare a blank Django form for HTML form rendering.
        form = SalesTransactionForm()
        return Response({
            'transactions': serializer.data,
            'form': form
        }, template_name=self.template_name)
    
    def post(self, request, format=None):
        # When posted from an HTML form, the data is in request.data (or request.POST)
        # First try the DRF serializer
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']
            # Check if there is sufficient stock for a sale.
            if product.quantity < quantity:
                # If not enough stock, either re-render with an error or return JSON error.
                error_msg = 'Insufficient stock for sale.'
                # For HTML form rendering, re-render with the error in the form.
                form = SalesTransactionForm(data=request.data)
                form.add_error('quantity', error_msg)
                transactions = Transaction.objects.filter(transaction_type='sale').order_by('-timestamp')
                serializer_list = TransactionSerializer(transactions, many=True)
                return Response({
                    'transactions': serializer_list.data,
                    'form': form
                }, status=status.HTTP_400_BAD_REQUEST, template_name=self.template_name)
            # Save the transaction with transaction_type fixed to 'sale' and created_by from request.user.
            transaction = serializer.save(transaction_type='sale', created_by=request.user)
            # Update the product stock.
            product.quantity -= quantity
            product.save()
            # Return the created transaction. For HTML rendering, you might redirect to GET.
            # Here we redirect so that the form is cleared.
            return redirect(request.path)
        else:
            # If serializer errors occur, re-render the HTML form.
            form = SalesTransactionForm(data=request.data)
            transactions = Transaction.objects.filter(transaction_type='sale').order_by('-timestamp')
            serializer_list = TransactionSerializer(transactions, many=True)
            return Response({
                'transactions': serializer_list.data,
                'form': form,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST, template_name=self.template_name)
