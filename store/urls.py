from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='pos_dashboard'), name='logout'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage/out-of-stock/', views.out_of_stock, name='out_of_stock'),
    path('manage/change-price/', views.change_price, name='change_price'),
    path('manage/product-analytics/', views.product_analytics, name='product_analytics'),
    path('manage/products/', views.manage_products, name='manage_products'),
    path('manage/products/stats/', views.product_stats_api, name='product_stats_api'),

    # POS views
    path('', views.pos_dashboard, name='pos_dashboard'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('add-to-transaction/<int:product_id>/', views.add_to_transaction, name='add_to_transaction'),
    path('active-transactions/', views.active_transactions, name='active_transactions'),
    path('update-transaction-summary/', views.update_transaction_summary, name='update_transaction_summary'),
    path('update-item/<int:item_id>/', views.update_item_quantity, name='update_item_quantity'),
    path('remove-item/<int:item_id>/', views.remove_item, name='remove_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('receipt/<int:transaction_id>/', views.receipt, name='receipt'),
    path('cancel-transaction/', views.cancel_transaction, name='cancel_transaction'),
    path('void-transaction/<int:transaction_id>/', views.void_transaction, name='void_transaction'),
    path('order-history/', views.order_history, name='order_history'),

    # Legacy product view
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]
