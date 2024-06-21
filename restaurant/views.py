# from .serializers import OrderReimbursementSerializer
from .models import Order, OrderReimbursement
from django.urls import reverse
from django.core.mail import send_mail
from django.http import HttpResponse
from django.http import JsonResponse, HttpResponse
from .models import Order, OrderStatus
from restaurant_info.models import RestaurantConfiguration
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
import json
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import permissions, status
from restaurant.models import Order
from restaurant.serializers import OrderSerializer
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.http import JsonResponse
from django.conf import settings
import stripe
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


stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderAPIView(ListAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    authentication_classes = (JWTAuthentication, )
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-timestamp')


@method_decorator(csrf_exempt, name='dispatch')
class CreateCheckoutSessionView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    authentication_classes = (JWTAuthentication, )
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        # import pdb; pdb.set_trace()
        serializer = OrderSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            discount_per = 0
            apply_discount = False
            discount_config = RestaurantConfiguration.objects.get(
                title='DiscountConfig', is_active=True)
            if discount_config:
                discount_obj = json.loads(discount_config.value)
                discount_obj['amount']
                if order.total_amount >= discount_obj['amount']:
                    discount_per = discount_obj['discount']
                    order.discount_amount = (
                        order.total_amount * Decimal(discount_per/100))
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

                    # success_url=reverse(
                    #     'update_order_details', kwargs={
                    #         'session_key': {CHECKOUT_SESSION_ID}
                    #     }
                    # ),
                    # success_url=settings.BACKEND_URL + \
                    # 'api/mughali/update-order-status/{CHECKOUT_SESSION_ID}/',
                    success_url=settings.SITE_URL +
                    '?success=true&session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=settings.SITE_URL + '?canceled=true',
                )

                if apply_discount:
                    coupon = stripe.Coupon.create(
                        percent_off=discount_per,
                        duration="once"
                    )
                    session_data["discounts"] = [{"coupon": coupon.id}]

                checkout_session = stripe.checkout.Session.create(
                    **session_data)
                order.stripe_session_id = checkout_session.id
                order.save()
                return Response(checkout_session.url)
            except Exception as e:
                return Response(
                    {'error': e},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (JWTAuthentication, )

    def _get_min_delivery_time(self):
        min_delivery_time = 45
        delivery_time_in_min = RestaurantConfiguration.objects.filter(
            title='DeliveryConfig', key='delivery_time_in_min'
        ).first()
        if delivery_time_in_min:
            return delivery_time_in_min.value or min_delivery_time
        return min_delivery_time

    def post(self, request):
        # import pdb
        # pdb.set_trace()
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
            order.payment_intent = session['payment_intent']
            order.order_status = OrderStatus.PAID
            order.save()
            return Response({
                'message': f'Your order will be deliver in next {self._get_min_delivery_time()} minutes'
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Your payment is pending'}, status=status.HTTP_400_BAD_REQUEST)


# Set your secret key
stripe.api_key = settings.STRIPE_SECRET_KEY
# Add this to your settings
endpoint_secret = 'whsec_a553b8a8fafb36f1c217c53c9d143610f18f7770e00d756465b072423f74cc1d'


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

# @csrf_exempt
# def stripe_webhook(request):
#   payload = request.body

#   # For now, you only need to print out the webhook payload so you can see
#   # the structure.
#   print(payload)

#   return HttpResponse(status=200)

# from django.views.generic import TemplateView
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

        try:
            order = Order.objects.get(id=order_id)
            order.order_status = OrderStatus.PAID  # Update to your desired status
            order.save()
        except Order.DoesNotExist:
            return HttpResponse(status=404)

    return JsonResponse({'status': 'success'})


class RequestReimbursementView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    authentication_classes = (JWTAuthentication, )
    # serializer_class = OrderReimbursementSerializer

    def post(self, request, order_id):
        # import pdb
        # pdb.set_trace()
        reason_for_refund = request.data.get('reason_for_refund')
        if not reason_for_refund:
            return Response({'error': 'Reason for Refund is required.'}, status=status.HTTP_400_BAD_REQUEST)
        order = get_object_or_404(
            Order.objects.select_related('reimbursement'), id=order_id, user=request.user
        )
        if hasattr(order, 'reimbursement'):
            if order.reimbursement.is_reimbursed:
                return Response({'error': 'Your amount is already reimbursed. Process will take couple of days.'}, status=status.HTTP_400_BAD_REQUEST)
            elif order.reimbursement.is_rejected:
                return Response({'error': 'Your refund request id rejected'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'error': 'Reimbursement already requested for this order'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = stripe.checkout.Session.retrieve(order.stripe_session_id)
            payment_status = session['payment_status']
            if payment_status == 'paid':
                reimbursement = OrderReimbursement.objects.create(
                    order=order, is_refund_requested=True, reason_for_reimbursed=reason_for_refund
                )
                return Response({
                    'message': 'Your request to reimbursement is recived, We will let you know once it approved.',
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': "Can't reimburse. Your payment is pending"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': "Unable to perform refund request"}, status=status.HTTP_400_BAD_REQUEST)
