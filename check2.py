import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product, Category
from django.contrib.auth.models import User

print("Users:", User.objects.count())
print("Categories:", Category.objects.count())
print("Products:", Product.objects.count())

categories = Category.objects.all()
for c in categories:
    print("Category:", c.name, "slug:", c.slug)

products = Product.objects.all()[:5]
for p in products:
    try:
        print("Product:", p.name, "price:", p.price, "type:", type(p.price))
    except Exception as e:
        print("Error with product", p.id, ":", e)