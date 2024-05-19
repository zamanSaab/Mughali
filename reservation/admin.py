from django.contrib import admin
from .models import ReservationStatus, Reservation, ReservationPending, ReservationApproved


# @admin.register(ReservationConfig)
# class ReservationConfigAdmin(admin.ModelAdmin):
#     list_display = ('__str__', 'max_seats_count')

# # @admin.register(Reservation)
# class ReservationAdmin(admin.ModelAdmin):
#     list_display = ('name', 'user', 'no_of_person', 'date', 'start_time', 'end_time', 'status')
#     list_filter = ('status',)
#     search_fields = ('name', 'user__username')
#     date_hierarchy = 'date'
#     list_editable = ('status',)
    
#     def save_model(self, request, obj, form, change):
#         if 'status' in form.changed_data:
#             obj.save()  # Save the object when status is changed
#         else:
#             super().save_model(request, obj, form, change)


# # @admin.register(Reservation)
# class CurrentReservationAdmin(admin.ModelAdmin):
#     list_display = ('name', 'user', 'no_of_person', 'date', 'start_time', 'end_time', 'status')
#     list_filter = ('status',)
#     search_fields = ('name', 'user__username')
#     date_hierarchy = 'date'
#     list_editable = ('status',)

#     def get_queryset(self, request):
#         # Modify the queryset as per your requirement
#         qs = super().get_queryset(request)
#         # For example, let's filter out reservations that are not confirmed
#         return qs.exclude(status__in=[ReservationStatus.CANCELLED, ReservationStatus.COMPLETED])

#     ordering = ['-date', 'start_time']  # Example ordering by date descending and start_time ascending



class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'no_of_person', 'date', 'start_time', 'end_time', 'status']
    search_fields = ['user__username', 'name']
    list_filter = ['status']

admin.site.register(Reservation, ReservationAdmin)

class ReservationPendingAdmin(ReservationAdmin):
    def get_queryset(self, request):
        return self.model.objects.filter(status=ReservationStatus.PENDING)

admin.site.register(ReservationPending, ReservationPendingAdmin)

class ReservationApprovedAdmin(ReservationAdmin):
    def get_queryset(self, request):
        return self.model.objects.filter(status=ReservationStatus.APPROVED)

admin.site.register(ReservationApproved, ReservationApprovedAdmin)