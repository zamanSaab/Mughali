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



import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect

stripe.api_key = settings.STRIPE_SECRET_KEY
from restaurant.serializers import OrderSerializer
from restaurant.models import Order

from rest_framework import permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication

@method_decorator(csrf_exempt, name='dispatch')
class CreateCheckoutSessionView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    authentication_classes = (JWTAuthentication, )
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            items = [{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': item.menu_item.item.name,
                        'description': item.menu_item.description or 'product description',
                    },
                    'unit_amount': int(item.amount * 100),
                },
                'quantity': item.quantity,
            } for item in order.order_items.all()]
            try:
                checkout_session = stripe.checkout.Session.create(
                    line_items=items,
                    payment_method_types=['card',],
                    mode='payment',
                    success_url=settings.SITE_URL + '/?success=true&session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=settings.SITE_URL + '/?canceled=true',
                )
                order.stripe_session_id = checkout_session.id
                order.save()
                return redirect(checkout_session.url)
            except:
                return Response(
                    {'error': 'Something went wrong when creating stripe checkout session'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from restaurant_info.models import RestaurantConfiguration
from .models import Order, OrderStatus

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (JWTAuthentication, )

    def _get_min_delivery_time(self):
        min_delivery_time = 45
        delivery_time_in_min =  RestaurantConfiguration.objects.filter(
            title='DeliveryConfig', key='delivery_time_in_min'
        ).first()
        if delivery_time_in_min:
            return delivery_time_in_min.value or min_delivery_time
        return min_delivery_time

    def post(self, request):
        session_key = request.data.get('session_key')
        if not session_key:
            return Response({'error': 'session_key is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(stripe_session_id=session_key)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.order_status == OrderStatus.PENDING:
            order.order_status = OrderStatus.PAID
            order.save()
            return Response({
                'message': f'Your order will be deliver in next {self._get_min_delivery_time()} minutes'
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Order is in preparation'}, status=status.HTTP_400_BAD_REQUEST)
