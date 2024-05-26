from django.db import models

class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=255)
    amount = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)