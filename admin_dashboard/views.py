

from django.db import transaction
import json
# from .models import Order, OrderMeal, MenuItem
from unicodedata import category
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
import subprocess
import webbrowser
import cups
import os
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.mail import send_mail
from .forms import CustomSetPasswordForm
from django_rest_passwordreset.models import ResetPasswordToken
import stripe
# from .models import Order, OrderReimbursement
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from stripe.api_resources import payment_method
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from reservation.models import Reservation, ReservationStatus
from restaurant.models import Category, MenuItem, Order, OrderStatus, PaymentMethods, OrderReimbursement, OrderMeal, OrderTypes

from .forms import LoginForm, OrderForm, ReservationForm
from .models import Notification
from .serializers import NotificationSerializer
from django.db.models import Q


def login_view(request):
    logout(request)
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                return redirect("/admin-dashboard/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def bookings(request):
    reservations = Reservation.objects.filter(
        status__in=[
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.IN_PROGRESS,
        ]
    )
    status_choices = ReservationStatus.choices
    context = {
        'reservations': reservations,
        'status_choices': status_choices
    }
    return render(request, 'home/index.html', context)


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def dashboard(request):
    return render(request, "home/map.html")

# from django.contrib.auth.models import User


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def order(request):
    orders = Order.objects.filter(
        Q(payment_method=PaymentMethods.COD, order_status__in=[
            OrderStatus.PENDING, OrderStatus.IN_PROGRESS, OrderStatus.OUT_FOR_DELIVERY
        ]) |
        Q(order_status__in=[
            OrderStatus.PAID, OrderStatus.IN_PROGRESS, OrderStatus.OUT_FOR_DELIVERY
        ])
    )
    return render(request, "home/tables.html", {"orders": orders})


# @csrf_exempt
@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def update_reservation_status(request):
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        new_status = request.POST.get('status')

        reservation = get_object_or_404(Reservation, id=reservation_id)
        reservation.status = new_status
        reservation.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def reservation_view(request, id=None):
    if id:
        reservation = get_object_or_404(Reservation, pk=id)
    else:
        reservation = None
    if request.method == 'POST':
        # import pdb
        # pdb.set_trace()
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = ReservationForm(instance=reservation)

    return render(request, 'home/reservation.html', {'form': form})


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def order_view(request, id=None):
    refund_request_id = request.GET.get('refund_request_id', None)
    if id:
        order = get_object_or_404(Order, pk=id)
    else:
        order = None
    if request.method == 'POST':
        # import pdb
        # pdb.set_trace()
        refund_request_id = request.POST.get('refund_request_id')
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order_status = form.cleaned_data.get('order_status')
            if refund_request_id:
                try:
                    # import pdb
                    # pdb.set_trace()
                    order_reimbursement = OrderReimbursement.objects.filter(
                        is_reimbursed=False, is_rejected=False, id=refund_request_id, is_refund_requested=True
                    ).first()
                    session = stripe.checkout.Session.retrieve(
                        order_reimbursement.order.stripe_session_id
                    )
                    if session['payment_status'] == 'paid':
                        payment_intent_id = order_reimbursement.order.payment_intent
                        payment_intent = stripe.PaymentIntent.retrieve(
                            payment_intent_id
                        )
                        refund = stripe.Refund.create(
                            payment_intent=payment_intent.id
                        )
                        order_reimbursement.is_reimbursed = True
                        order_reimbursement.save()
                        order.order_status = OrderStatus.REIMBURSED
                        order.save(update_fields=['order_status'])
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")
                return redirect('refund')

            if order_status:
                order.order_status = order_status
                order.save(update_fields=['order_status'])
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = OrderForm(instance=order)

    return render(
        request, 'home/order.html', {
            'form': form, 'order_id': order.id,
            'order_items': order.order_items.all(),
            'refund_request_id': refund_request_id
        }
    )


# order_reimbursement = get_object_or_404(
#     OrderReimbursement,
#     is_reimbursed=False, is_rejected=False,
#     id=order_reimbursement_id, is_refund_requested=True
# )
#    try:
#         session = stripe.checkout.Session.retrieve(
#             order_reimbursement.order.stripe_session_id
#         )
#         if session['payment_status'] == 'paid':
#             payment_intent_id = order_reimbursement.order.payment_intent
#             payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
#             refund = stripe.Refund.create(
#                 payment_intent=payment_intent.id
#             )
#             order_reimbursement.is_reimbursed = True
#             order_reimbursement.save()

#         return Response({'message': 'Reimbursement initiated', 'refund': refund}, status=status.HTTP_200_OK)
#     except stripe.error.StripeError as e:
#         return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# class ReservationCreateView(View):
#     def get(self, request):
#         form = ReservationForm()
#         return render(request, 'home/user.html', {'form': form})

#     def post(self, request):
#         form = ReservationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('success_url')  # Redirect to a success page
#         return render(request, 'your_template.html', {'form': form})


class NotificationList(APIView):
    def get(self, request, format=None):
        notifications = Notification.objects.filter(
            is_read=False).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class MarkAsRead(APIView):
    def post(self, request, pk, format=None):
        try:
            notification = Notification.objects.get(pk=pk)
            notification.is_read = True
            notification.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def send_receipt(request):
    receipt_data = {
        'date': '22-05-2024',
        'time': '01:58:30 AM',
        'order_id': '642162',
        'ntn': '3520233811629',
        'customer_name': 'zaman',
        'contact_no': '03554643485',
        'address': 'house 148, st 1 malmo k satyh gli',
        'area': 'Bilal Colony, Opposite Izmir Town',
        'items': [
            {'sr': 1, 'name': 'Mexican Wrap | Serves 1',
                'rate': '550', 'qty': 1, 'total': '550'},
            {'sr': 2, 'name': 'Loaded Fries | Small',
                'rate': '350', 'qty': 1, 'total': '350'},
            {'sr': 3, 'name': 'Cold drinks | Cola | 345 ml',
                'rate': '70', 'qty': 1, 'total': '70'}
        ],
        'payment_method': 'CASH',
        'sub_total': '970',
        'gst': '0',
        'discount': '0',
        'delivery_fee': '50',
        'billed_amt': '1020'
    }

    subject = 'Your Purchase Receipt'
    html_message = render_to_string('receipt.html', {'receipt': receipt_data})
    plain_message = strip_tags(html_message)
    from_email = 'your_email@gmail.com'
    to_email = 'user@example.com'  # Replace with the user's email address

    try:
        send_mail(subject, plain_message, from_email, [
                  to_email], html_message=html_message)
        return HttpResponse("Receipt emailed successfully")
    except Exception as e:
        return HttpResponse(f"Error sending email: {e}")


# from .models import Receipt
# from weasyprint import HTML
# import subprocess


def view_receipt(request, order_id):
    current_datetime = timezone.now()
    order = Order.objects.get(id=order_id)
    receipt_data = {
        'date': current_datetime.strftime('%d-%m-%Y'),
        'time': current_datetime.strftime('%I:%M:%S %p'),
        'order_id': order.id,
        'customer_name': order.user.first_name + ' ' + order.user.last_name,
        'contact_no': order.phone,
        'address': order.address,
        'order_type': order.get_order_type_display(),
        'items': [{
            'sr': index + 1,  # Adding 1 to index to start sr_no from 1
            'name': item.menu_item.item.name,
            'rate': round(item.amount) if order.order_type == OrderTypes.IN_HOUSE else item.amount,
            'qty': item.quantity,
            'total': item.amount * item.quantity
        } for index, item in enumerate(order.order_items.all())],
        'payment_method': order.get_payment_method_display(),
        'sub_total': order.total_amount,
        'discount': order.discount_amount,
        'billed_amt': order.total_amount-order.discount_amount
    }
    # # html_string = render_to_string('receipt.html', {'receipt': receipt})
    # # html = HTML(string=html_string)
    # # pdf = html.write_pdf()
    # html_string = render_to_string('receipt.html', {'receipt': receipt_data})
    # html = HTML(string=html_string)
    # pdf = html.write_pdf()
    # response = HttpResponse(pdf, content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename=receipt_zaman.pdf'
    # return response

    print_order_receipt(order)
    return render(request, 'receipt.html', {'receipt': receipt_data})


def index(request):
    return render(request, 'frontend.html')


# utils.py


def generate_receipt_content(order):

    current_datetime = timezone.now()
    context = {
        'receipt': {
            'date': current_datetime.strftime('%d-%m-%Y'),
            'time': current_datetime.strftime('%I:%M:%S %p'),
            'order_id': order.id,
            'customer_name': order.user.first_name + ' ' + order.user.last_name,
            'contact_no': order.phone,
            'address': order.address,
            'order_type': order.get_order_type_display(),
            'items': [{
                'sr': index + 1,  # Adding 1 to index to start sr_no from 1
                'name': item.menu_item.item.name,
                'rate': item.amount,
                'qty': item.quantity,
                'total': item.amount * item.quantity
            } for index, item in enumerate(order.order_items.all())],
            'payment_method': order.get_payment_method_display(),
            'sub_total': order.total_amount,
            'discount': order.discount_amount,
            'billed_amt': order.total_amount-order.discount_amount
        }
    }
    return render_to_string('receipt.html', context)


def save_receipt_to_file(receipt_content):
    receipt_path = '/tmp/receipt.html'
    with open(receipt_path, 'w') as f:
        f.write(receipt_content)
    return receipt_path


def print_order_receipt(order):
    receipt_content = generate_receipt_content(order)
    receipt_file = save_receipt_to_file(receipt_content)

    # conn = cups.Connection()
    # default_printer = conn.getDefault()
    # import pdb; pdb.set_trace()
    # if default_printer:
    #     conn.printFile(default_printer, receipt_file, "Order Receipt", {})
    # else:
    #     raise Exception("No default printer found")

    # # Mock the printing process
    # with open(receipt_file, 'r') as f:
    #     print(f.read())  # Print the content to the console
    # print(f"Receipt saved to: {receipt_file}")

    # # Open the HTML file in the default web browser
    # webbrowser.open(f'file://{receipt_file}')
    # print(f"Receipt saved to: {receipt_file}")

    # Open the system print dialog
    if os.name == 'posix':  # macOS
        subprocess.run(['open', '-a', 'Preview', receipt_file])
    elif os.name == 'nt':   # Windows
        subprocess.run(['print', receipt_file], shell=True)
    else:
        raise Exception("Unsupported operating system")

    print(f"Receipt saved to: {receipt_file}")  # Log the file path


def password_reset_confirm(request, uidb64=None, token=None):
    # import pdb; pdb.set_trace()
    if uidb64 is not None and token is not None:
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        reset_token = ResetPasswordToken.objects.filter(key=token, user_id=uid)
        if user is not None and reset_token.exists():
            if request.method == 'POST':
                form = CustomSetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Your password has been set.')
                    reset_token.delete()
                    return render(request, 'home/reset_password_complete.html', {'message': 'password reset successfully'})
                    # return redirect('home/reset_password.html')
            else:
                form = CustomSetPasswordForm(user)
            return render(request, 'home/reset_password.html', {'form': form})
        else:
            return render(request, 'home/reset_password_complete.html', {'message': 'The password reset link was invalid.'})
    else:
        # messages.error(request, 'The password reset link was invalid.')
        return render(request, 'home/reset_password_complete.html', {'message': 'The password reset link was invalid.'})

        # return redirect('password_reset')


# from django.shortcuts import render, redirect
# from django.contrib.auth.forms import SetPasswordForm
# from django.contrib import messages
# # from django_rest_passwordreset.tokens import get_token_generator

# is_refund_requested = models.BooleanField(default=False)
# is_reimbursed = models.BooleanField(default=False)
# is_rejected = models.BooleanField(default=False)
@api_view(['POST'])
@permission_classes([IsAdminUser])
@login_required(login_url="/admin-dashboard/login/")
def initiate_reimbursement(request, order_reimbursement_id):
    # import pdb
    # pdb.set_trace()
    order_reimbursement = get_object_or_404(
        OrderReimbursement,
        is_reimbursed=False, is_rejected=False,
        id=order_reimbursement_id, is_refund_requested=True
    )
    try:
        session = stripe.checkout.Session.retrieve(
            order_reimbursement.order.stripe_session_id
        )
        if session['payment_status'] == 'paid':
            payment_intent_id = order_reimbursement.order.payment_intent
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            refund = stripe.Refund.create(
                payment_intent=payment_intent.id
            )
            order_reimbursement.is_reimbursed = True
            order_reimbursement.save()

        return Response({'message': 'Reimbursement initiated', 'refund': refund}, status=status.HTTP_200_OK)
    except stripe.error.StripeError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def refunds(request):
    refund_requests = OrderReimbursement.objects.filter(
        is_reimbursed=False, is_rejected=False, is_refund_requested=True
    )

    return render(request, 'home/refunds.html', {'refund_requests': refund_requests})


@login_required(login_url="/admin-dashboard/login/")
@permission_classes([IsAdminUser])
def menu(request):
    menu_items = MenuItem.objects.all()
    categories = Category.objects.all()
    # reservations = Reservation.objects.filter(
    #     status__in=[
    #         ReservationStatus.PENDING,
    #         ReservationStatus.CONFIRMED,
    #         ReservationStatus.IN_PROGRESS,
    #     ]
    # )
    # status_choices = ReservationStatus.choices
    # context = {
    #     'reservations': reservations,
    #     'status_choices': status_choices
    # }
    # abc = {'zaman': 'chaudhary', 'chaudhary': 'khan'}
    return render(
        request, 'home/menu.html', {
            'menu_items': menu_items, 'categories': categories, 'Backend_URL': settings.BACKEND_URL
        }
    )


@login_required
@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        with transaction.atomic():
            data = json.loads(request.body)
            cart = data.get('cart', [])
            customer_name = data.get('customer_name', None)
            total_amount = sum(float(item['price'])
                               * int(item['quantity']) for item in cart)

            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                address='In House Order',
                city='Athlone',
                zip_code='00000',
                phone='0899600867',
                stripe_session_id='',
                payment_method=0,
                order_type=2,
                order_status=4,
            )
            for item in cart:
                OrderMeal.objects.create(
                    order=order, menu_item_id=item['id'],
                    amount=item['price'], quantity=item['quantity']
                )

            current_datetime = timezone.now()
            # import pdb
            # pdb.set_trace()
            receipt_data = {
                'date': current_datetime.strftime('%d-%m-%Y'),
                'time': current_datetime.strftime('%I:%M:%S %p'),
                'order_id': order.id,
                'customer_name': customer_name or order.user.first_name + ' ' + order.user.last_name,
                'contact_no': order.phone,
                'address': order.address,
                'order_type': order.get_order_type_display(),
                'items': [{
                    'sr': index + 1,  # Adding 1 to index to start sr_no from 1
                    'name': item['name'],
                    'rate': float(item['price']),
                    'qty': item['quantity'],
                    'total': float(item['price']) * int(item['quantity'])
                } for index, item in enumerate(cart)],
                'payment_method': order.get_payment_method_display(),
                'sub_total': total_amount,
                'discount': order.discount_amount,
                'billed_amt': order.total_amount-order.discount_amount
            }
            return render(request, 'receipt.html', {'receipt': receipt_data})
    # receipt_html = generate_receipt_content(order)
            # return JsonResponse({'message': 'Order created successfully!', 'page': 'receipt.html', 'receipt': receipt_data}, status=201)
        # return JsonResponse({'message': 'Order created successfully!'}, status=201)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# class OrderMeal(models.Model):
#     note = models.TextField(null=True, blank=True)
#     order = models.ForeignKey(
#         Order, on_delete=models.CASCADE, related_name='order_items')
#     serving = models.SmallIntegerField(
#         null=True, blank=True, choices=MealServing.choices)
#     menu_item = models.ForeignKey(
#         MenuItem, on_delete=models.CASCADE, blank=False
#     )
#     amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
#     quantity = models.PositiveSmallIntegerField(default=1)

#     required_items = models.ManyToManyField(
#         Item, blank=True, related_name='required_in')
#     additional_items = models.ManyToManyField(
#         Item, blank=True, related_name='optional_in')

#     def __str__(self):
#         return self.menu_item.item.name
