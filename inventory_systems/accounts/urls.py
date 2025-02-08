# accounts/urls.py
from django.urls import path, include
from .views import login_page, dashboard

urlpatterns = [
    # Djoser authentication endpoints:
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    # Login page:
    path('login/', login_page, name='login'),
    
    # Dashboard page:
    path('dashboard/', dashboard, name='dashboard'),
]

