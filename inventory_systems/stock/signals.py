import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, Product

audit_logger = logging.getLogger('audit')

@receiver(post_save, sender=Transaction)
def update_product_quantity(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        if instance.transaction_type == 'sale':
            product.quantity -= instance.quantity
        elif instance.transaction_type == 'restock':
            product.quantity += instance.quantity
        product.save()
        # Log audit information
        audit_logger.info(
            f"Transaction {instance.id}: {instance.transaction_type} of {instance.quantity} "
            f"units on product {product.id} by user {instance.created_by}"
        )
