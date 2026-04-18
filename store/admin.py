from django.contrib import admin
from .models import Category, Product, Transaction, TransactionItem, ProductRequest

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'sku', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'is_available']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'total_amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['receipt_number']
    readonly_fields = ['receipt_number', 'created_at']

    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_number', 'created_at')
        }),
        ('Sale Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_method', 'amount_paid', 'change_amount')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
    )

@admin.register(TransactionItem)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'transaction', 'quantity', 'product_price', 'line_total']
    list_filter = ['added_at']
    search_fields = ['product_name', 'transaction__receipt_number']
    readonly_fields = ['transaction', 'product_name', 'product_price', 'line_total']

@admin.register(ProductRequest)
class ProductRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'requested_by', 'status', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['name', 'requested_by']
