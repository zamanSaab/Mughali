from django.shortcuts import get_object_or_404
from .models import Reservation, ReservationStatus
from restaurant_info.models import RestaurantConfiguration
from django.db.models import Sum
from django.core.cache import cache


def get_max_seats_count():
    max_seats = cache.get('max_seats')
    if max_seats is None:
        max_seats_config = get_object_or_404(RestaurantConfiguration, key='max_seats_count')
        max_seats = int(max_seats_config.value)
        cache.set('max_seats', max_seats, timeout=3600)  # Cache for 1 hour
    return max_seats


def get_reserved_seats(date, start_time):
    return Reservation.objects.filter(
        date=date,
        start_time__lte=start_time,
        end_time__gt=start_time,
        status__in=[ReservationStatus.CONFIRMED, ReservationStatus.IN_PROGRESS]
    ).aggregate(total_reserved_seats=Sum('no_of_person'))['total_reserved_seats'] or 0