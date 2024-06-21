from django.urls import path, include
# from django.conf.urls import url
# from rest_framework.routers import DefaultRouter

from .views import GenerateMenuAPIView, CreateCheckoutSessionView, UpdateOrderStatusView, StripeWebhookView, stripe_webhook, OrderAPIView, RequestReimbursementView


# router = DefaultRouter()
# router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('menu/', GenerateMenuAPIView.as_view(), name='restaurant-menu'),
    # path('reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    path('publish-order/', CreateCheckoutSessionView.as_view()),
    path('update-order-status/', UpdateOrderStatusView.as_view(),
         name='update_order_status'),
    # path('update-order-status/<str:session_key>/', UpdateOrderStatusView.as_view(),
    #      name='update_order_details'),
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),

    path('request-reimbursement/<int:order_id>/',
         RequestReimbursementView.as_view(), name='request-reimbursement'),
    # path('initiate-reimbursement/<int:order_id>/',
    #      InitiateReimbursementView.as_view(), name='initiate-reimbursement'),
    path('orders/', OrderAPIView.as_view()),
    
]
