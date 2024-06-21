from django.urls import path
from .views import login_view, index, create_order, update_reservation_status, reservation_view, order, order_view, NotificationList, MarkAsRead, dashboard, send_receipt, view_receipt, bookings, password_reset_confirm, initiate_reimbursement, refunds, menu

urlpatterns = [
    path('login/', login_view, name="login"),
    path('reset/<uidb64>/<token>/', password_reset_confirm,
         name='password_reset_confirm'),
    path('update_reservation_status/', update_reservation_status,
         name='update_reservation_status'),
    path('reservation/<int:id>/', reservation_view, name='reservation_detail'),
    path('order/<int:id>/', order_view, name='order_detail'),
    path('bookings/', bookings, name='home'),
    path('orders/', order, name='orders'),
    path('', dashboard, name='dasboard'),
    path('notifications/get-notifications/',
         NotificationList.as_view(), name='get-notifications'),
    path('notifications/mark-as-read/<int:pk>/',
         MarkAsRead.as_view(), name='mark-as-read'),
    path('send-receipt/', send_receipt, name='send_receipt'),
    path('view-receipt/<int:order_id>/', view_receipt, name='receipt_view'),

    path('initiate-reimbursement/<int:order_reimbursement_id>/',
         initiate_reimbursement, name='initiate_reimbursement'
         ),
    path('refunds/', refunds, name='refund'),
    path('menu/', menu, name='menu'),
    path('create_order/', create_order, name='create_order'),
]
