from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, Order
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

# Product List
def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})


# Product Detail
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})


# Add to Cart
@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')


# Cart View
@login_required
def cart_view(request):
    items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


# Remove From Cart
@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(Cart, pk=pk)
    item.delete()
    return redirect('cart')


# Checkout
@login_required
def checkout(request):
    items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in items)

    Order.objects.create(user=request.user, total_price=total)
    items.delete()

    return render(request, 'store/checkout_success.html')


# Orders Page
@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user)
    return render(request, 'store/orders.html', {'orders': user_orders})


# Register
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})