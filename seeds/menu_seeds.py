from decimal import Decimal
from menu.models import Category, FoodItem, Discount
from menu.choices import Type

FoodItem.objects.all().delete()
Category.objects.all().delete()
Discount.objects.all().delete()

d5  = Discount.objects.create(discount_type=Type.PERCENT, amount=5, description="5% off")
d10 = Discount.objects.create(discount_type=Type.PERCENT, amount=10, description="10% off")
d15 = Discount.objects.create(discount_type=Type.PERCENT, amount=15, description="15% off")
d20 = Discount.objects.create(discount_type=Type.PERCENT, amount=20, description="20% off")
d2  = Discount.objects.create(discount_type=Type.FIXED, amount=2, description="$2 off")
d3  = Discount.objects.create(discount_type=Type.FIXED, amount=3, description="$3 off")

hot = Category.objects.create(name="Hot Drinks", discount=d10)
cold = Category.objects.create(name="Cold Drinks")
dessert = Category.objects.create(name="Desserts", discount=d15)
food = Category.objects.create(name="Main Food")
bakery = Category.objects.create(name="Bakery", discount=d5)
breakfast = Category.objects.create(name="Breakfast")
snacks = Category.objects.create(name="Snacks", discount=d20)

items = [
("Espresso", hot, "3.00", "Strong espresso shot.", None),
("Cappuccino", hot, "4.50", "Espresso with milk foam.", d2),
("Latte", hot, "4.80", "Creamy milk coffee.", None),
("Flat White", hot, "4.60", "Microfoam espresso drink.", None),

("Iced Coffee", cold, "4.20", "Chilled coffee over ice.", d10),
("Cold Brew", cold, "5.50", "Slow brewed cold coffee.", None),
("Iced Latte", cold, "5.20", "Cold milk espresso.", None),
("Frappe", cold, "5.90", "Blended iced coffee.", d2),

("Cheesecake", dessert, "6.50", "Creamy cheesecake.", None),
("Chocolate Cake", dessert, "6.80", "Layered chocolate cake.", None),
("Tiramisu", dessert, "7.20", "Coffee dessert.", d10),
("Ice Cream", dessert, "4.00", "Vanilla ice cream.", None),

("Chicken Sandwich", food, "8.50", "Grilled chicken sandwich.", None),
("Beef Burger", food, "9.80", "Beef burger.", d3),
("Veggie Burger", food, "9.20", "Vegetarian burger.", None),
("Club Sandwich", food, "8.90", "Triple sandwich.", None),

("Croissant", bakery, "3.20", "Butter croissant.", None),
("Bagel", bakery, "2.80", "Fresh bagel.", None),
("Muffin", bakery, "3.50", "Blueberry muffin.", None),
("Donut", bakery, "2.50", "Sugar donut.", None),

("Omelette", breakfast, "6.20", "Egg omelette.", None),
("Pancakes", breakfast, "6.80", "Stack pancakes.", d5),
("French Toast", breakfast, "6.40", "Sweet toast.", None),
("Granola Bowl", breakfast, "5.90", "Yogurt granola.", None),

("Fries", snacks, "3.50", "Crispy fries.", None),
("Nachos", snacks, "4.80", "Cheese nachos.", None),
("Onion Rings", snacks, "4.20", "Onion rings.", None),
("Mozzarella Sticks", snacks, "5.30", "Cheese sticks.", None),
]

for n,c,p,d,disc in items:
    FoodItem.objects.create(
        name=n,
        category=c,
        price=Decimal(p),
        description=d,
        discount=disc,
        is_available=True
    )

print("SEEDED")
