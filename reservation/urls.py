from django.urls import path
from .views import ReservationViewSet, item_list, ReservationListView, update_reservation_status
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', ReservationViewSet, basename='grading-exam')

urlpatterns = [
    path('items/', item_list, name='item_list'),
    path('reservations/', ReservationListView.as_view(), name='reservation-list'),
    path('reservations/update_status/', update_reservation_status, name='update-reservation-status'),
    # path('', ReservationView.as_view(), name='reservation'),
]

urlpatterns += router.urls
