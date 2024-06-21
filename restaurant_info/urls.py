from django.urls import path, include
# from django.conf.urls import url
# from rest_framework.routers import DefaultRouter

from .views import RestaurantDetail, RestaurantConfigurationDetailView, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm
# router = DefaultRouter()
# router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('password_reset/', include('django_rest_passwordreset.urls',
         namespace='password_reset')),
    path('register/', RegisterView.as_view(), name='register'),

    path('about/', RestaurantDetail.as_view(), name='about-restaurant'),
    path('configuration/<str:title>/', RestaurantConfigurationDetailView.as_view(), name='configuration-detail'),
    # path('login/', login_view, name="login"),
    # path('', index, name='home'),
    
]
