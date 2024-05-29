from django.contrib import admin
from .models import ReservationStatus, Reservation

class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'no_of_person', 'date', 'start_time', 'end_time', 'status']
    search_fields = ['user__username', 'name']
    list_filter = ['status']

admin.site.register(Reservation, ReservationAdmin)
