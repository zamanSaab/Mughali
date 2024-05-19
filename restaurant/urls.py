from django.urls import path, include
# from django.conf.urls import url
# from rest_framework.routers import DefaultRouter

from .views import GenerateMenuAPIView, OrderAPIView


# router = DefaultRouter()
# router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('menu/', GenerateMenuAPIView.as_view(), name='restaurant-menu'),
    path('publish-order/', OrderAPIView.as_view()),
    
]
