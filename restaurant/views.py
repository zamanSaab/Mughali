from decimal import Decimal
from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.views import APIView
from .models import Category, Order, PaymentMethods
from .serializers import CategorySerializer, OrderSerializer




# Create your views here.
class GenerateMenuAPIView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    pagination_class = None
    # queryset = SummerSchoolLevel.objects.all()
    def get_queryset(self):
        # import pdb; pdb.set_trace()
        return Category.objects.all().prefetch_related(
            'items__required_items__item__menu_item',
            'items', 'items__item', 'items__required_items',
            'items__required_items__item', 'items__optional_items'
        )
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
from django.http import HttpResponseRedirect
import json

@method_decorator(csrf_exempt, name='dispatch')
class CreateCheckoutSessionView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    authentication_classes = (JWTAuthentication, )
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        import pdb; pdb.set_trace()
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            discount_per = 0
            apply_discount = False
            discount_config = RestaurantConfiguration.objects.get(title='DiscountConfig', is_active=True)
            if discount_config:
                discount_obj = json.loads(discount_config.value)
                discount_obj['amount']
                if order.total_amount >= discount_obj['amount']:
                    discount_per = discount_obj['discount']
                    order.discount_amount = (order.total_amount * Decimal(discount_per/100))
                    apply_discount = True

            if order.payment_method == PaymentMethods.COD:
                order.save()
                return Response({'message': 'Order placed successfully'}, status=status.HTTP_200_OK)

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
                session_data = dict(
                    metadata={
                        "order_id": order.id
                    },
                    line_items=items,
                    payment_method_types=['card',],
                    mode='payment',
                    success_url=settings.SITE_URL + '?success=true&session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=settings.SITE_URL + '?canceled=true',
                )
                
                if apply_discount:
                    coupon = stripe.Coupon.create(
                        percent_off=discount_per,
                        duration="once"
                    )
                    session_data["discounts"] = [{"coupon": coupon.id}]
                
                checkout_session = stripe.checkout.Session.create(**session_data)
                order.stripe_session_id = checkout_session.id
                order.save()
                return Response(checkout_session.url)
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

        session = stripe.checkout.Session.retrieve(order.stripe_session_id)

        # Check payment status
        payment_status = session['payment_status']
        if payment_status == 'paid' and order.order_status == OrderStatus.PENDING:
            order.order_status = OrderStatus.PAID
            order.save()
            return Response({
                'message': f'Your order will be deliver in next {self._get_min_delivery_time()} minutes'
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Your payment is pending'}, status=status.HTTP_400_BAD_REQUEST)



import stripe
from django.conf import settings
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Set your secret key
stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = 'whsec_a553b8a8fafb36f1c217c53c9d143610f18f7770e00d756465b072423f74cc1d'  # Add this to your settings

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_checkout_session(session)

        # Handle other event types as needed

        return JsonResponse({'status': 'success'})

def handle_checkout_session(session):
    # Fulfill the purchase...
    print("Payment was successful.")
    print(session)
    # You can update your order or perform any action you need
    order_id = session.get("client_reference_id")
    try:
        order = Order.objects.get(id=order_id)
        order.order_status = OrderStatus.PAID
        order.save()
    except Order.DoesNotExist:
        pass


# Using Django
from django.http import HttpResponse

# @csrf_exempt
# def stripe_webhook(request):
#   payload = request.body

#   # For now, you only need to print out the webhook payload so you can see
#   # the structure.
#   print(payload)

#   return HttpResponse(status=200)

import json
import stripe
from django.core.mail import send_mail
from django.conf import settings
# from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.views import View
# from .models import Product

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # print(session)

        # customer_email = session["customer_details"]["email"]
        order_id = session["metadata"]["order_id"]

        order = Order.objects.get(id=order_id)
        order.order_status = OrderStatus.PAID
        order.save()

        # send_mail(
        #     subject="Here is your order",
        #     message=f"Thanks for your purchase. Here is the order you ordered. The URL is {order.address}",
        #     recipient_list=[customer_email],
        #     from_email="matt@test.com"
        # )

    return HttpResponse(status=200)
