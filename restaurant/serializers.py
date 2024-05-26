from .models import Category, MenuItem, Item, RequiredItem, Order, MealServing
from rest_framework import serializers


class SubItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source='menu_item.price', max_digits=10, decimal_places=2)

    class Meta:
        model = Item
        fields = ('id', 'name', 'price')


class RequiredItemSerializer(serializers.ModelSerializer):
    item = SubItemSerializer(many=True)
    class Meta:
        model = RequiredItem
        fields = '__all__'

class SimpleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('name', )
# class ItemServingSerializer(serializers.Serilalizer):
#     regular = serializers.DecimalField(max_digits=10, decimal_places=2)
#     large = serializers.DecimalField(max_digits=10, decimal_places=2)

class MenuItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='item.name')
    # serving = serializers.ChoiceField(choices=MealServing.choices, read_only=True)
    required_items = RequiredItemSerializer(many=True)
    optional_items = SubItemSerializer(many=True)
    class Meta:
        model = MenuItem
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.allow_serving:
            data['servings'] = [
                {
                    'id': serving[0],
                    'name': serving[1],
                    'price': instance.price * (2 if serving[0] == MealServing.LARGE else 1)}
                for serving in MealServing.choices
            ]
        return data





# class MealSerializer(serializers.ModelSerializer):
#     required_items = RequiredItemSerializer(read_only=True)
#     optional_items = SubItemSerializer(many=True)
#     is_meal = serializers.BooleanField(default=True, read_only=True)
#     class Meta:
#         model = Meal
#         fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True)

    class Meta:
        model = Category
        fields = '__all__'

    # def get_items(self, instance):
    #     items = list()
    #     items.extend(MealSerializer(instance.meals, many=True).data)
    #     items.extend(ItemSerializer(instance.items, many=True).data)
    #     return items

from .models import OrderTypes, OrderStatus, Order, OrderMeal
from datetime import datetime
from django.utils import timezone
from django.db import transaction
class OrderMealSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(default=1)
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    # menu_item_name = serializers.CharField(read_only=True, source='menu_item.item.name')
    # menu_item_image = serializers.CharField(read_only=True, source='menu_item.image')
    # menu_item_description = serializers.CharField(read_only=True, source='menu_item.description')
    # menu_item_name = serializers.CharField(read_only=True, source='menu_item.item.name')
    additional_items = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), many=True)
    required_items = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), many=True)
    # amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderMeal
        fields = (
            'note', 'serving', 'menu_item', 'additional_items', 'required_items', 'amount', 'quantity'
            # 'menu_item_name', 'menu_item_image', 'amount', 'menu_item_description'
        )
        extra_kwargs = {
            'amount': {'required': False},
        }

    # def get_amount(self, instance):
    #     # Note: This method assumes that `obj` is the validated data dict, not a model instance
    #     menu_item_price = instance.menu_item.price
    #     required_items_prices = sum(item.menu_item.price for item in instance.required_items.all())
    #     return menu_item_price + required_items_prices

    def create(self, validated_data):
        # import pdb; pdb.set_trace()
        additional_items_data = validated_data.pop('additional_items')
        required_items_data = validated_data.pop('required_items')
        menu_item_price = validated_data['menu_item'].price * int(validated_data.get('serving', 1))
        # import pdb; pdb.set_trace()
        required_items_prices = sum(
            item.menu_item.price for item in required_items_data
        )
        validated_data['amount'] = menu_item_price + required_items_prices
        order_meal = OrderMeal.objects.create(**validated_data)
        order_meal.additional_items.set(additional_items_data)
        order_meal.required_items.set(required_items_data)
        return order_meal



from restaurant_info.models import RestaurantConfiguration
from django.db.models import Sum
from decimal import Decimal

class OrderSerializer(serializers.ModelSerializer):
    order_type = serializers.ChoiceField(choices=OrderTypes.choices, required=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # min_delivery_time = serializers.SerializerMethodField()
    order_items = OrderMealSerializer(many=True, required=True)
    # total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'
        extra_kwargs = {
            'stripe_session_id': {'required': False},
            'total_amount': {'required': False},
        }


    def validate_order_items(self, value):
        if value is None or len(value) == 0:
            raise serializers.ValidationError("You cant place an empty order.")
        return value
    
    def get_min_delivery_time(self, instance):
        min_delivery_time = 45
        delivery_time_in_min =  RestaurantConfiguration.objects.filter(
            title='DeliveryConfig', key='delivery_time_in_min'
        ).first()
        if delivery_time_in_min:
            return delivery_time_in_min.value or min_delivery_time
        return min_delivery_time
    

    # def get_total_amount(self, instance):
    #     # Calculate total amount for the order
    #     return sum(item.get_amount() for item in instance.order_items.all())

    @transaction.atomic
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items')
        total_amount = Decimal('0.0')
        order = Order.objects.create(**validated_data, total_amount=total_amount)
        # import pdb; pdb.set_trace()
        for order_item_data in order_items_data:
            ordered_meal = OrderMealSerializer().create({**order_item_data, 'order': order})
            total_amount += ordered_meal.amount
        order.total_amount = total_amount
        order.save()
        
        return order
    # def create(self, validated_data):
    #     order_items = validated_data.pop('order_items')

        # menu_items = list()
        # additional_items = list()
        # items = validated_data.pop('menu_items', [])
        # for item in items:
        #     menu_items.append(item.get('id'))
        #     additional_items.extend(item.get('optional_items', []))
        #     additional_items.extend(item.get('required_items', []))
        # # validated_data['menu_items'] = menu_items
        # # validated_data['additional_items'] = additional_items
        # # abc = super().create(validated_data)

        # abc = Order.objects.create(**validated_data)
        # abc.menu_items.set(menu_items)
        # abc.additional_items.set(additional_items)
        # return abc
#     # address = serializers.TextField()
#     # order_date_time = serializers.DateTimeField()

# class Order(models.Model):
# 	items = models.ManyToManyField(Item)
# 	meals = models.ManyToManyField(Meal)
# 	order_type = models.SmallIntegerField(choices=OrderTypes.choices(), default=OrderTypes.DELIVERY)
# 	address = models.TextField(null=True, blank=True)
# 	order_date_time = models.DateTimeField()


# {
#     "order_type": 0,
#     "order_status": 0,
#     "meals": [{"id": 1, "optional_items": [1]}],
#     "address": ABC"",
#     "note": "XYZ",
#     "items": [1, 2]
# }
{
    "order_type": 0,
    "order_status": 1,
    "menu_items": [{"id": 1, "optional_items": [2,3]}],
    "address": "ABC"
}

{
    "order_type": 1,
    "order_items": [],
    "address": "ABC Lahore",
    "city": "Lahore",
    "zip_code": "53800",
    "phone": "03404242145",
    "total_amount": 500,
    "transaction_id": "A5478390F258",
    "transaction_code": "code-A5478390F258"
}