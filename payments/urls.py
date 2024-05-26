from django.urls import path
from .views import CreatePaymentIntentView, CreateCheckoutSessionView

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('create-payment-session/', CreateCheckoutSessionView.as_view(), name='create-payment-session'),
]