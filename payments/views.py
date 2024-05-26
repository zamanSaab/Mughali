# payments/views.py
import stripe
import json
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

stripe.api_key = settings.STRIPE_SECRET_KEY

@method_decorator(csrf_exempt, name='dispatch')
class CreatePaymentIntentView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        # import pdb; pdb.set_trace()
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(data['amount']) * 100,
                currency='eur',
            )
            return JsonResponse({
                'clientSecret': intent['client_secret']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=403)


# views.py
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
                return redirect(checkout_session.url)
            except:
                return Response(
                    {'error': 'Something went wrong when creating stripe checkout session'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
