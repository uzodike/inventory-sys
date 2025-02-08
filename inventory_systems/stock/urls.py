from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet,
    SalesTransactionViewSet, RestockTransactionViewSet,
    manage_categories, manage_products,
    manage_sales, manage_restock,
    SalesTransactionAPIView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'sales', SalesTransactionViewSet, basename='sales')
router.register(r'restock', RestockTransactionViewSet, basename='restock')

urlpatterns = [
    # API endpoints under the 'api/' prefix:
    path('api/', include(router.urls)),
    # HTML views:
    path('manage/categories/', manage_categories, name='manage_categories'),
    path('manage/products/', manage_products, name='manage_products'),
    path('sales/', manage_sales, name='manage_sales'),
    path('restock/', manage_restock, name='manage_restock'),
    # Additional API view if needed for sales (with its own URL):
    path('api/sales/', SalesTransactionAPIView.as_view(), name='api_sales'),
]

