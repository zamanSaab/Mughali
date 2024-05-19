from django.urls import path, include
# from django.conf.urls import url
# from rest_framework.routers import DefaultRouter

from .views import RestaurantDetail, RestaurantConfigurationDetailView, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView

# router = DefaultRouter()
# router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view(), name='register'),

    path('about/', RestaurantDetail.as_view(), name='about-restaurant'),
    path('configuration/<str:title>/', RestaurantConfigurationDetailView.as_view(), name='configuration-detail'),
    # path('login/', login_view, name="login"),
    # path('', index, name='home'),
    
]
