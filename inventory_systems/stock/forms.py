from django import forms
from .models import Category, Product, Transaction

class SalesTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['product', 'quantity']
        # transaction_type will be set in the view
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionally restrict products to those with some stock.
        self.fields['product'].queryset = Product.objects.filter(quantity__gt=0)

class RestockTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['product', 'quantity']
        # transaction_type will be set in the view

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter category name'}),
        }

class ProductForm(forms.ModelForm):
    expiry_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 
            'quantity', 'price', 'expiry_date', 'low_stock_threshold'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter product name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter product description'}),
            'quantity': forms.NumberInput(attrs={'min': 0}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'low_stock_threshold': forms.NumberInput(attrs={'min': 0}),
        }
