from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('remove/<int:pk>/', views.remove_from_cart, name='remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders, name='orders'),
    path('register/', views.register, name='register'),
]