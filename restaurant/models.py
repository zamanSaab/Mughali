from django.db import models
from stripe.api_resources import payment_method
# from model_utils.models import TimeStampedModel

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SpiceLevel(models.IntegerChoices):
    MILD = 0, 'Mild'
    HOT = 1, 'Hot'
    SPICY = 2, 'Spicy'


class Item(models.Model):
    name = models.CharField(max_length=100)
     
    def __str__(self):
        return self.name
     

class RequiredItem(models.Model):
    description = models.CharField(max_length=100)
    item = models.ManyToManyField(Item)
    def __str__(self):
        return self.description

class MealServing(models.IntegerChoices):
    REGULAR = 1, 'Regular'
    LARGE = 2, 'Large'


class MenuItem(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='menu_item')
    description = models.TextField(blank=True)
    
    is_vegitarian = models.BooleanField(default=False)
    show_salad = models.BooleanField(default=False)
    show_sauce = models.BooleanField(default=False)
    allow_serving = models.BooleanField(default=False)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(null=True, blank=True, upload_to='item_images')
    is_meal = models.BooleanField(default=False)
    spiciness_level = models.SmallIntegerField(null=True, blank=True, choices=SpiceLevel.choices)
    optional_items = models.ManyToManyField(Item, blank=True)
    required_items = models.ManyToManyField(RequiredItem, blank=True)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, related_name='items')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.item.name


class OrderTypes(models.IntegerChoices):
    PICK_UP = 0, 'Pick-Up'
    DELIVERY = 1, 'Delivery'


class OrderStatus(models.IntegerChoices):
    PENDING = 0, 'Pending'
    IN_PROGRESS = 1, 'In progress'
    OUT_FOR_DELIVERY = 2, 'Out for delivery'
    DELIVERED = 3, 'Delivered'
    PAID = 4, 'Paid'

class PaymentMethods(models.IntegerChoices):
    COD = 0, 'Cash on Delivery'
    ONLINE = 1, 'Online payment'

from django.contrib.auth.models import User
from django.utils import timezone

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_type = models.SmallIntegerField(choices=OrderTypes.choices, default=OrderTypes.DELIVERY)
    order_status = models.SmallIntegerField(choices=OrderStatus.choices, default=OrderStatus.PENDING)
    address = models.CharField(max_length=111)
    city = models.CharField(max_length=111)
    state = models.CharField(null=True, blank=True, max_length=111)
    zip_code = models.CharField(max_length=111)
    phone = models.CharField(max_length=111, default="")
    timestamp = models.DateTimeField(default=timezone.now)
    # delivery_time = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    stripe_session_id = models.CharField(max_length=512)
    payment_method = models.SmallIntegerField(choices=PaymentMethods.choices, default=PaymentMethods.COD)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    # order_date_time = models.DateTimeField()

    def __str__(self):
        return f"{OrderStatus.choices[self.order_status][1]} - {self.user.username}-{self.total_amount}€"

class OrderMeal(models.Model):
    note = models.TextField(null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    serving = models.SmallIntegerField(null=True, blank=True, choices=MealServing.choices)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.DO_NOTHING, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    quantity = models.PositiveSmallIntegerField(default=1)

    required_items = models.ManyToManyField(Item, blank=True, related_name='required_in')
    additional_items = models.ManyToManyField(Item, blank=True, related_name='optional_in')
    
    def __str__(self):
        return self.menu_item.item.name
