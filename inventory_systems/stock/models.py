from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings

class Category(models.Model):
    """
    Represents a product category.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Enter the category name (e.g. Electronics, Groceries)."
    )

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Represents a product with its details, including pricing, quantity,
    and an optional expiry date.
    """
    name = models.CharField(
        max_length=255,
        help_text="Enter the product name."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Enter an optional description for the product."
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Select the category for this product."
    )
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Enter the current stock level (must be 0 or greater)."
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Enter the price of the product (minimum 0.01)."
    )
    expiry_date = models.DateField(
        blank=True,
        null=True,
        help_text="Enter the expiry date (if applicable)."
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Enter the threshold below which stock is considered low."
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        """
        Returns True if the current quantity is at or below the low stock threshold.
        """
        return self.quantity <= self.low_stock_threshold

    @property
    def is_expired(self):
        """
        Returns True if the product has an expiry date and it is in the past.
        """
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    # stock/models.py (inside Product)
    def adjust_stock(self, delta):
        self.quantity += delta
        self.save()


    

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('sale', 'Sale'),
        ('restock', 'Restock'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    transaction_type = models.CharField(choices=TRANSACTION_TYPES, max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    # Audit field: record who performed this transaction
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} by {self.created_by}"
