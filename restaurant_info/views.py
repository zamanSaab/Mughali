from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Restaurant, RestaurantConfiguration
from .serializers import (RestaurantConfigurationSerializer,
                          RestaurantSerializer)


class RestaurantDetail(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset.first())
        return Response(serializer.data)


from rest_framework import permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication


class RestaurantConfigurationDetailView(APIView):
    # permission_classes = (permissions.IsAuthenticated, )
    # authentication_classes = (JWTAuthentication, )
    def get(self, request, title):
        try:
            config = RestaurantConfiguration.objects.get(title=title, is_active=True)
            serializer = RestaurantConfigurationSerializer(config)
            return Response({serializer.data['key']: serializer.data['value']}, status=status.HTTP_200_OK)
        except RestaurantConfiguration.DoesNotExist:
            return Response({'error': 'Configuration not found or not active'}, status=status.HTTP_404_NOT_FOUND)


from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# views.py

