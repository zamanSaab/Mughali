from django.db import models
from django.contrib.auth.models import User


class ReservationStatus(models.IntegerChoices):
    PENDING = 1, 'Pending'
    CONFIRMED = 2, 'Confirmed'
    CANCELLED = 3, 'Cancelled'
    IN_PROGRESS = 4, 'In Progress'
    COMPLETED = 5, 'Completed'


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    no_of_person = models.IntegerField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    note = models.TextField(blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=111, default="")
    status = models.IntegerField(choices=ReservationStatus.choices, default=ReservationStatus.PENDING)

    def __str__(self):
        return f"{self.name}'s reservation at {self.date} from {self.start_time} to {self.end_time}"
