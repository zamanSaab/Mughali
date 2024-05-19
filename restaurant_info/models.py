from django.db import models

class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    # about =  models.TextField()
    address = models.CharField(max_length=255)
    address_url = models.URLField(max_length=255, blank=True, null=True)  # URL for the address
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class OpeningHour(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='opening_hours')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    kitchen_open = models.TimeField()
    kitchen_close = models.TimeField()
    delivery_open = models.TimeField()
    delivery_close = models.TimeField()

    class Meta:
        unique_together = ('restaurant', 'day_of_week')

    def __str__(self):
        return f"{self.restaurant.name} - {self.day_of_week}"
    

class RestaurantConfiguration(models.Model): 
    title = models.CharField(max_length=20)
    key = models.CharField(max_length=20)
    value = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"'{self.key}': {self.value}"
