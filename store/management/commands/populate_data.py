from django.core.management.base import BaseCommand
from store.models import Category, Product

class Command(BaseCommand):
    help = 'Populate the database with initial categories and products'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Classic Flavors', 'slug': 'classic-flavors', 'icon': '🍦', 'order': 1},
            {'name': 'Fruit Sorbets', 'slug': 'fruit-sorbets', 'icon': '🍓', 'order': 2},
            {'name': 'Premium', 'slug': 'premium', 'icon': '👑', 'order': 3},
        ]

        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f"Created category: {cat.name}")

        # Get categories
        classic = Category.objects.get(slug='classic-flavors')
        fruit = Category.objects.get(slug='fruit-sorbets')
        premium = Category.objects.get(slug='premium')

        # Classic Flavors products
        classic_products = [
            {'name': 'Vanilla Ice Cream', 'price': 25.00, 'stock': 50, 'description': 'Classic vanilla flavor'},
            {'name': 'Chocolate Ice Cream', 'price': 25.00, 'stock': 50, 'description': 'Rich chocolate flavor'},
            {'name': 'Strawberry Ice Cream', 'price': 25.00, 'stock': 50, 'description': 'Fresh strawberry flavor'},
            {'name': 'Mint Chocolate Chip', 'price': 30.00, 'stock': 40, 'description': 'Mint ice cream with chocolate chips'},
            {'name': 'Cookies and Cream', 'price': 30.00, 'stock': 40, 'description': 'Vanilla ice cream with cookie pieces'},
            {'name': 'Rocky Road', 'price': 30.00, 'stock': 40, 'description': 'Chocolate ice cream with marshmallows and nuts'},
            {'name': 'Butter Pecan', 'price': 28.00, 'stock': 45, 'description': 'Buttery pecan flavor'},
            {'name': 'Coffee Ice Cream', 'price': 28.00, 'stock': 45, 'description': 'Rich coffee flavor'},
            {'name': 'Pistachio', 'price': 32.00, 'stock': 35, 'description': 'Nutty pistachio flavor'},
            {'name': 'Caramel Swirl', 'price': 32.00, 'stock': 35, 'description': 'Vanilla with caramel swirl'},
            {'name': 'Neapolitan', 'price': 35.00, 'stock': 30, 'description': 'Three flavors in one: chocolate, vanilla, strawberry'},
            {'name': 'French Vanilla', 'price': 28.00, 'stock': 45, 'description': 'Premium French vanilla'},
        ]

        # Fruit Sorbets products
        fruit_products = [
            {'name': 'Lemon Sorbet', 'price': 22.00, 'stock': 60, 'description': 'Tangy lemon sorbet'},
            {'name': 'Orange Sorbet', 'price': 22.00, 'stock': 60, 'description': 'Sweet orange sorbet'},
            {'name': 'Strawberry Sorbet', 'price': 24.00, 'stock': 55, 'description': 'Fresh strawberry sorbet'},
            {'name': 'Raspberry Sorbet', 'price': 24.00, 'stock': 55, 'description': 'Tart raspberry sorbet'},
            {'name': 'Mango Sorbet', 'price': 26.00, 'stock': 50, 'description': 'Tropical mango sorbet'},
            {'name': 'Pineapple Sorbet', 'price': 26.00, 'stock': 50, 'description': 'Sweet pineapple sorbet'},
            {'name': 'Passion Fruit Sorbet', 'price': 28.00, 'stock': 45, 'description': 'Exotic passion fruit sorbet'},
            {'name': 'Kiwi Sorbet', 'price': 24.00, 'stock': 55, 'description': 'Fresh kiwi sorbet'},
            {'name': 'Watermelon Sorbet', 'price': 22.00, 'stock': 60, 'description': 'Refreshing watermelon sorbet'},
            {'name': 'Mixed Berry Sorbet', 'price': 30.00, 'stock': 40, 'description': 'Blend of mixed berries'},
            {'name': 'Coconut Sorbet', 'price': 26.00, 'stock': 50, 'description': 'Creamy coconut sorbet'},
            {'name': 'Peach Sorbet', 'price': 24.00, 'stock': 55, 'description': 'Juicy peach sorbet'},
        ]

        # Premium products
        premium_products = [
            {'name': 'Gold Dusted Vanilla', 'price': 45.00, 'stock': 20, 'description': 'Vanilla with edible gold dust'},
            {'name': 'Truffle Chocolate', 'price': 50.00, 'stock': 15, 'description': 'Chocolate with truffle pieces'},
            {'name': 'Saffron Pistachio', 'price': 55.00, 'stock': 12, 'description': 'Pistachio with saffron'},
            {'name': 'Caviar Ice Cream', 'price': 80.00, 'stock': 10, 'description': 'Vanilla with caviar pearls'},
            {'name': 'Rose Petal Sorbet', 'price': 40.00, 'stock': 25, 'description': 'Rose flavored sorbet with petals'},
            {'name': 'Matcha Green Tea', 'price': 35.00, 'stock': 30, 'description': 'Premium matcha flavor'},
            {'name': 'Lavender Honey', 'price': 38.00, 'stock': 28, 'description': 'Lavender with honey'},
            {'name': 'Champagne Sorbet', 'price': 42.00, 'stock': 22, 'description': 'Champagne infused sorbet'},
            {'name': 'Black Truffle', 'price': 65.00, 'stock': 14, 'description': 'Ice cream with black truffle'},
            {'name': '24K Gold Leaf', 'price': 100.00, 'stock': 8, 'description': 'Vanilla with 24K gold leaf'},
            {'name': 'Diamond Dust', 'price': 120.00, 'stock': 5, 'description': 'Ice cream with edible diamond dust'},
            {'name': 'Royal Bourbon', 'price': 60.00, 'stock': 16, 'description': 'Vanilla with aged bourbon'},
        ]

        # Create products
        for product_data in classic_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=classic,
                defaults=product_data
            )
            if created:
                self.stdout.write(f"Created product: {product.name}")

        for product_data in fruit_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=fruit,
                defaults=product_data
            )
            if created:
                self.stdout.write(f"Created product: {product.name}")

        for product_data in premium_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=premium,
                defaults=product_data
            )
            if created:
                self.stdout.write(f"Created product: {product.name}")

        self.stdout.write("Data population complete!")