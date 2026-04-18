from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.safestring import mark_safe
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import json
from django.core.serializers.json import DjangoJSONEncoder
import uuid

from .models import Product, Category, Transaction, TransactionItem

# ============================================================================
# POS CORE VIEWS
# ============================================================================

def pos_dashboard(request):
    """Main POS dashboard - shows product categories and current transaction (no login required)"""
    categories = Category.objects.all()
    
    # Get current session transaction (if exists)
    transaction_id = request.session.get('current_transaction')
    current_transaction = None
    if transaction_id:
        try:
            current_transaction = Transaction.objects.get(id=transaction_id, status='pending')
        except Transaction.DoesNotExist:
            del request.session['current_transaction']
    
    context = {
        'categories': categories,
        'current_transaction': current_transaction,
    }
    return render(request, 'store/pos_dashboard.html', context)

def category_products(request, slug):
    """Show products in a category for the POS"""
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(is_available=True)
    categories = Category.objects.all()

    all_products = []
    for prod in Product.objects.filter(is_available=True).select_related('category'):
        # Validate and safely convert price
        try:
            price = prod.price
            if price is None:
                price = Decimal('0.00')
            # Ensure it's a valid Decimal
            price = Decimal(str(price))
            if price.is_nan() or price.is_infinite():
                price = Decimal('0.00')
        except (TypeError, InvalidOperation, ValueError):
            price = Decimal('0.00')
        
        all_products.append({
            'id': prod.id,
            'name': prod.name,
            'price': str(price),
            'category_name': prod.category.name,
            'category_slug': prod.category.slug,
            'image_url': prod.image.url if prod.image else '',
        })

    transaction_id = request.session.get('current_transaction')
    current_transaction = None
    items = []
    if transaction_id:
        try:
            current_transaction = Transaction.objects.get(id=transaction_id, status='pending')
            items = current_transaction.items.all()
        except Transaction.DoesNotExist:
            del request.session['current_transaction']

    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'current_transaction': current_transaction,
        'items': items,
        'all_products_json': mark_safe(json.dumps(all_products, cls=DjangoJSONEncoder)),
    }
    return render(request, 'store/category_products.html', context)

@require_POST
def add_to_transaction(request, product_id):
    """Add product to current transaction"""
    product = get_object_or_404(Product, id=product_id, is_available=True)
    
    # Validate product price
    try:
        product_price = Decimal(str(product.price))
        if product_price.is_nan() or product_price.is_infinite():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Product has invalid price'})
            else:
                messages.error(request, 'Product has invalid price')
                return redirect('category_products', slug=product.category.slug)
    except (TypeError, InvalidOperation, ValueError):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Product has invalid price'})
        else:
            messages.error(request, 'Product has invalid price')
            return redirect('category_products', slug=product.category.slug)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Get or create transaction for this session
    transaction_id = request.session.get('current_transaction')
    
    if not transaction_id:
        # Create new transaction
        receipt_number = f"RCP-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        transaction = Transaction.objects.create(
            receipt_number=receipt_number,
            status='pending'
        )
        request.session['current_transaction'] = transaction.id
    else:
        transaction = get_object_or_404(Transaction, id=transaction_id, status='pending')
    
    # Add product to transaction
    trans_item, created = TransactionItem.objects.get_or_create(
        transaction=transaction,
        product=product,
        defaults={
            'product_name': product.name,
            'product_price': product.price,
            'quantity': quantity
        }
    )
    
    if not created:
        trans_item.quantity += quantity
        trans_item.save()
    
    transaction.calculate_total()
    transaction.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items_data = [
            {
                'id': item.id,
                'product_name': item.product_name,
                'product_price': str(item.product_price),
                'quantity': item.quantity,
                'line_total': str(item.line_total),
            }
            for item in transaction.items.all()
        ]
        return JsonResponse({
            'success': True,
            'items': items_data,
            'subtotal': str(transaction.subtotal),
            'tax_amount': str(transaction.tax_amount),
            'total_amount': str(transaction.total_amount),
        })
    
    messages.success(request, f'{product.name} added to transaction')
    return redirect('pos_dashboard')

def active_transactions(request):
    """View and manage current transaction/sale"""
    transaction_id = request.session.get('current_transaction')
    
    if not transaction_id:
        messages.warning(request, 'No active transaction')
        return redirect('pos_dashboard')
    
    transaction = get_object_or_404(Transaction, id=transaction_id, status='pending')
    items = transaction.items.all()
    
    context = {
        'transaction': transaction,
        'items': items,
        'categories': Category.objects.all(),
    }
    return render(request, 'store/active_transactions.html', context)

@require_POST
def update_item_quantity(request, item_id):
    """Update quantity of item in current transaction"""
    item = get_object_or_404(TransactionItem, id=item_id)
    transaction = item.transaction
    
    # Verify this transaction belongs to the current session
    if request.session.get('current_transaction') != transaction.id or transaction.status != 'pending':
        messages.error(request, 'Cannot modify this transaction')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Cannot modify this transaction'})
        return redirect('active_transactions')
    
    new_quantity = int(request.POST.get('quantity', 1))
    
    if new_quantity <= 0:
        item.delete()
        messages.success(request, f'Removed {item.product_name} from transaction')
    else:
        item.quantity = new_quantity
        item.save()
        messages.success(request, f'Updated {item.product_name} quantity')
    
    transaction.calculate_total()
    transaction.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items_data = [
            {
                'id': item.id,
                'product_name': item.product_name,
                'product_price': str(item.product_price),
                'quantity': item.quantity,
                'line_total': str(item.line_total),
            }
            for item in transaction.items.all()
        ]
        return JsonResponse({
            'success': True,
            'items': items_data,
            'subtotal': str(transaction.subtotal),
            'tax_amount': str(transaction.tax_amount),
            'total_amount': str(transaction.total_amount),
        })
    
    return redirect('active_transactions')

@require_POST
def remove_item(request, item_id):
    """Remove item from current transaction"""
    item = get_object_or_404(TransactionItem, id=item_id)
    transaction = item.transaction
    
    if request.session.get('current_transaction') != transaction.id or transaction.status != 'pending':
        messages.error(request, 'Cannot modify this transaction')
        return redirect('active_transactions')
    
    product_name = item.product_name
    item.delete()
    
    transaction.calculate_total()
    transaction.save()
    
    messages.success(request, f'{product_name} removed')
    return redirect('active_transactions')

@require_POST
def update_transaction_summary(request):
    transaction_id = request.session.get('current_transaction')
    if not transaction_id:
        return JsonResponse({'success': False, 'error': 'No active transaction'})

    transaction = get_object_or_404(Transaction, id=transaction_id, status='pending')
    try:
        tax = Decimal(request.POST.get('tax', '0') or '0')
        if tax.is_nan() or tax.is_infinite():
            tax = Decimal('0')
    except InvalidOperation:
        tax = Decimal('0')

    transaction.tax_amount = tax
    transaction.discount_amount = Decimal('0')
    transaction.calculate_total()
    transaction.save()

    return JsonResponse({
        'success': True,
        'subtotal': str(transaction.subtotal),
        'tax_amount': str(transaction.tax_amount),
        'total_amount': str(transaction.total_amount),
    })

def checkout(request):
    """Complete the sale - payment screen"""
    transaction_id = request.session.get('current_transaction')
    
    if not transaction_id:
        messages.error(request, 'No active transaction')
        return redirect('pos_dashboard')
    
    transaction = get_object_or_404(Transaction, id=transaction_id, status='pending')
    items = transaction.items.all()
    
    if not items:
        messages.error(request, 'Transaction has no items')
        return redirect('active_transactions')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')
        try:
            amount_paid = Decimal(request.POST.get('amount_paid', '0') or '0')
            if amount_paid.is_nan() or amount_paid.is_infinite():
                raise InvalidOperation("Invalid decimal value")
        except InvalidOperation:
            messages.error(request, 'Invalid payment amount')
            return render(request, 'store/checkout.html', {
                'transaction': transaction,
                'items': items,
                'categories': Category.objects.all(),
            })

        # Update transaction — no discount
        transaction.payment_method = payment_method
        transaction.discount_amount = Decimal('0')
        transaction.calculate_total()

        if amount_paid < transaction.total_amount:
            messages.error(request, f'Amount paid (P{amount_paid}) is less than total (P{transaction.total_amount})')
            return render(request, 'store/checkout.html', {
                'transaction': transaction,
                'items': items,
                'categories': Category.objects.all(),
            })
        
        transaction.amount_paid = amount_paid
        transaction.change_amount = amount_paid - transaction.total_amount
        transaction.status = 'completed'
        transaction.save()

        # Deduct stock for each item sold
        for item in transaction.items.all():
            if item.product:
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save()
        
        # Clear session transaction
        if 'current_transaction' in request.session:
            del request.session['current_transaction']
        
        messages.success(request, f'Sale completed! Receipt #{transaction.receipt_number}')
        return redirect('receipt', transaction_id=transaction.id)
    
    context = {
        'transaction': transaction,
        'items': items,
        'categories': Category.objects.all(),
    }
    return render(request, 'store/checkout.html', context)

def receipt(request, transaction_id):
    """Display receipt for completed transaction"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    items = transaction.items.all()
    
    context = {
        'transaction': transaction,
        'items': items,
        'categories': Category.objects.all(),
    }
    return render(request, 'store/receipt.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def order_history(request):
    """Redirect to admin_dashboard where order history now lives"""
    return redirect('admin_dashboard')

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
@require_POST
def void_transaction(request, transaction_id):
    """Void a completed transaction (admin only)"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if transaction.status == 'voided':
        messages.warning(request, 'Transaction already voided')
    else:
        transaction.status = 'voided'
        transaction.save()
        messages.success(request, f'Receipt #{transaction.receipt_number} has been voided')
    
    return redirect('order_history')

@require_POST
def cancel_transaction(request):
    """Cancel current pending transaction"""
    transaction_id = request.session.get('current_transaction')
    
    if not transaction_id:
        messages.warning(request, 'No active transaction')
        return redirect('pos_dashboard')
    
    transaction = get_object_or_404(Transaction, id=transaction_id, status='pending')
    transaction.delete()
    del request.session['current_transaction']
    
    messages.success(request, 'Transaction cancelled')
    return redirect('pos_dashboard')

# ============================================================================
# AUTH VIEWS
# ============================================================================

from django.contrib.auth import authenticate, login

def register_view(request):
    from django.contrib.auth.forms import UserCreationForm

    if request.user.is_authenticated:
        return redirect('pos_dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # 🔥 authenticate first
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

            return redirect('pos_dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'store/register.html', {'form': form})

def custom_login(request):
    """Login view — admin is redirected to admin_dashboard, others to pos_dashboard"""
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'pos_dashboard')

    if request.method == 'POST':
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('pos_dashboard')
    else:
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm()

    return render(request, 'store/login.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def admin_dashboard(request):
    """Admin dashboard — hub with product management + order history"""
    # --- Order history section ---
    transactions = Transaction.objects.filter(
        status__in=['completed', 'voided']
    ).order_by('-created_at')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)

    total_sales = transactions.filter(status='completed').aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or Decimal('0')
    total_transactions = transactions.count()

    # --- Product stats for analytics cards ---
    total_products = Product.objects.count()
    out_of_stock_count = Product.objects.filter(stock=0).count()
    context = {
        'transactions': transactions,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'date_from': date_from or '',
        'date_to': date_to or '',
        'total_products': total_products,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'store/admin_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def out_of_stock(request):
    """All products — admin can toggle available/out-of-stock and update stock"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        product = get_object_or_404(Product, id=product_id)

        if action == 'set_stock':
            try:
                product.stock = max(0, int(request.POST.get('stock', 0)))
                product.save()
                messages.success(request, f'Stock updated: {product.name} → {product.stock}')
            except ValueError:
                messages.error(request, 'Invalid stock value')
        elif action == 'toggle_available':
            product.is_available = not product.is_available
            product.save()
            state = 'Available' if product.is_available else 'Out of Stock'
            messages.success(request, f'{product.name} marked as {state}')
        return redirect('out_of_stock')

    filter_by = request.GET.get('filter', 'all')
    all_products = Product.objects.select_related('category').order_by('category__name', 'name')
    available_count = all_products.filter(stock__gt=0).count()
    oos_count = all_products.filter(stock=0).count()

    if filter_by == 'available':
        products = all_products.filter(stock__gt=0)
    elif filter_by == 'oos':
        products = all_products.filter(stock=0)
    else:
        products = all_products

    return render(request, 'store/out_of_stock.html', {
        'products': products,
        'filter_by': filter_by,
        'available_count': available_count,
        'oos_count': oos_count,
        'total_count': available_count + oos_count,
    })


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def change_price(request):
    """Update product prices"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_price = request.POST.get('price')
        product = get_object_or_404(Product, id=product_id)
        try:
            price = Decimal(new_price)
            if price <= 0:
                raise ValueError
            product.price = price
            product.save()
            messages.success(request, f'Price updated: {product.name} → P{product.price}')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid price value')
        return redirect('change_price')

    products = Product.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'store/change_price.html', {'products': products})


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def product_analytics(request):
    """Sales analytics per product"""
    from django.db.models import Sum, Count
    top_products = (
        TransactionItem.objects
        .values('product_name')
        .annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum('line_total'),
            order_count=Count('transaction', distinct=True),
        )
        .order_by('-total_revenue')[:20]
    )
    return render(request, 'store/product_analytics.html', {'top_products': top_products})


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def manage_products(request):
    """Add / edit / delete products and categories"""
    if request.method == 'POST':
        action = request.POST.get('action')

        # ── CATEGORY actions ──────────────────────────────────────
        if action == 'add_category':
            name = request.POST.get('cat_name', '').strip()
            icon = request.POST.get('cat_icon', '📦').strip()
            if name:
                Category.objects.get_or_create(
                    name=name,
                    defaults={'icon': icon or '📦'}
                )
                messages.success(request, f'Category "{name}" added.')
            else:
                messages.error(request, 'Category name is required.')

        elif action == 'edit_category':
            cat = get_object_or_404(Category, id=request.POST.get('cat_id'))
            cat.name = request.POST.get('cat_name', cat.name).strip()
            cat.icon = request.POST.get('cat_icon', cat.icon).strip() or '📦'
            cat.save()
            messages.success(request, f'Category "{cat.name}" updated.')

        elif action == 'delete_category':
            cat = get_object_or_404(Category, id=request.POST.get('cat_id'))
            name = cat.name
            cat.delete()
            messages.success(request, f'Category "{name}" deleted.')

        # ── PRODUCT actions ───────────────────────────────────────
        elif action == 'add_product':
            try:
                cat = get_object_or_404(Category, id=request.POST.get('prod_category'))
                prod = Product.objects.create(
                    name=request.POST.get('prod_name', '').strip(),
                    category=cat,
                    price=Decimal(request.POST.get('prod_price', '0')),
                    stock=int(request.POST.get('prod_stock', 0)),
                    description=request.POST.get('prod_description', '').strip(),
                    is_available=request.POST.get('prod_available') == 'on',
                )
                if request.FILES.get('prod_image'):
                    prod.image = request.FILES['prod_image']
                    prod.save()
                messages.success(request, 'Product added.')
            except Exception as e:
                messages.error(request, f'Could not add product: {e}')

        elif action == 'edit_product':
            try:
                prod = get_object_or_404(Product, id=request.POST.get('prod_id'))
                prod.name = request.POST.get('prod_name', prod.name).strip()
                prod.category = get_object_or_404(Category, id=request.POST.get('prod_category'))
                prod.price = Decimal(request.POST.get('prod_price', str(prod.price)))
                prod.stock = int(request.POST.get('prod_stock', prod.stock))
                prod.description = request.POST.get('prod_description', prod.description).strip()
                prod.is_available = request.POST.get('prod_available') == 'on'
                if request.FILES.get('prod_image'):
                    prod.image = request.FILES['prod_image']
                if request.POST.get('remove_image') == 'on' and prod.image:
                    prod.image.delete(save=False)
                    prod.image = None
                prod.save()
                messages.success(request, f'"{prod.name}" updated.')
            except Exception as e:
                messages.error(request, f'Could not update product: {e}')

        elif action == 'delete_product':
            prod = get_object_or_404(Product, id=request.POST.get('prod_id'))
            name = prod.name
            prod.delete()
            messages.success(request, f'"{name}" deleted.')

        return redirect('manage_products')

    categories = Category.objects.all().order_by('order', 'name')
    products = Product.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'store/manage_products.html', {
        'categories': categories,
        'products': products,
    })


def product_stats_api(request):
    """JSON endpoint — live stats for the admin dashboard grid"""
    return JsonResponse({
        'total_products': Product.objects.count(),
        'out_of_stock_count': Product.objects.filter(stock=0).count(),
        'unavailable_count': Product.objects.filter(is_available=False).count(),
    })


# ============================================================================
# LEGACY PRODUCT VIEWS (kept for compatibility)
# ============================================================================

def product_detail(request, slug):
    """Product detail view - simplified for POS"""
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]
    context = {
        'product': product,
        'related_products': related,
        'categories': Category.objects.all(),
    }
    return render(request, 'store/product_detail.html', context)
