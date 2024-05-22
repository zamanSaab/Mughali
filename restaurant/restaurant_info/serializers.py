from rest_framework import serializers
from .models import Restaurant, OpeningHour, RestaurantConfiguration

class OpeningHourSerializer(serializers.ModelSerializer):
    kitchen_open = serializers.TimeField(format='%H:%M')
    kitchen_close = serializers.TimeField(format='%H:%M')
    delivery_open = serializers.TimeField(format='%H:%M')
    delivery_close = serializers.TimeField(format='%H:%M')

    class Meta:
        model = OpeningHour
        fields = ['day_of_week', 'kitchen_open', 'kitchen_close', 'delivery_open', 'delivery_close']

class RestaurantSerializer(serializers.ModelSerializer):
    opening_hours = OpeningHourSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = ['name', 'address', 'address_url', 'phone_number', 'opening_hours']


class RestaurantConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantConfiguration
        fields = ['key', 'value']



from django.contrib.auth.models import User
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('password', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user