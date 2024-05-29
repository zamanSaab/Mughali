from django.urls import path
from .views import login_view,index, update_reservation_status, reservation_view, order, order_view, NotificationList, MarkAsRead, dashboard

urlpatterns = [
    path('login/', login_view, name="login"),
    path('update_reservation_status/', update_reservation_status, name='update_reservation_status'),
    path('reservation/<int:id>/', reservation_view, name='reservation_detail'),
    path('order/<int:id>/', order_view, name='order_detail'),
    path('bookings/', index, name='home'),
    path('orders/', order, name='orders'),
    path('', dashboard, name='dasboard'),
    path('notifications/get-notifications/', NotificationList.as_view(), name='get-notifications'),
    path('notifications/mark-as-read/<int:pk>/', MarkAsRead.as_view(), name='mark-as-read'),
]

