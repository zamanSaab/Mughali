from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.views import APIView
from .models import Category, Order
from .serializers import CategorySerializer, OrderSerializer




# Create your views here.
class GenerateMenuAPIView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    pagination_class = None
    # queryset = SummerSchoolLevel.objects.all()
    def get_queryset(self):
        # import pdb; pdb.set_trace()
        return Category.objects.all().prefetch_related('items')
    serializer_class = CategorySerializer



from rest_framework import permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication
class OrderAPIView(CreateAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    authentication_classes = (JWTAuthentication, )
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

