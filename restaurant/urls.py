from django.urls import path, include
# from django.conf.urls import url
# from rest_framework.routers import DefaultRouter

from .views import GenerateMenuAPIView, CreateCheckoutSessionView, UpdateOrderStatusView


# router = DefaultRouter()
# router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('menu/', GenerateMenuAPIView.as_view(), name='restaurant-menu'),
    path('publish-order/', CreateCheckoutSessionView.as_view()),
    path('update-order-status/', UpdateOrderStatusView.as_view(), name='update_order_status'),
    
]
