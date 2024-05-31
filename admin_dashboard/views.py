

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
from restaurant.models import Order, OrderStatus, PaymentMethods

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
def dashboard(request):
    return render(request, "home/map.html")

# from django.contrib.auth.models import User
@login_required(login_url="/admin-dashboard/login/")
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
def reservation_view(request, id=None):
    if id:
        reservation = get_object_or_404(Reservation, pk=id)
    else:
        reservation = None
    if request.method == 'POST':
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
def order_view(request, id=None):
    if id:
        order = get_object_or_404(Order, pk=id)
    else:
        order = None
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order_status = form.cleaned_data.get('order_status')
            if order_status:
                order.order_status = order_status
                order.save(update_fields=['order_status'])
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = OrderForm(instance=order)

    return render(
        request, 'home/order.html',
        {'form': form, 'order_id': order.id, 'order_items': order.order_items.all()}
    )


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
        notifications = Notification.objects.filter(is_read=False).order_by('-created_at')
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


from django.core.mail import send_mail
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@login_required(login_url="/admin-dashboard/login/")
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
            {'sr': 1, 'name': 'Mexican Wrap | Serves 1', 'rate': '550', 'qty': 1, 'total': '550'},
            {'sr': 2, 'name': 'Loaded Fries | Small', 'rate': '350', 'qty': 1, 'total': '350'},
            {'sr': 3, 'name': 'Cold drinks | Cola | 345 ml', 'rate': '70', 'qty': 1, 'total': '70'}
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
        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        return HttpResponse("Receipt emailed successfully")
    except Exception as e:
        return HttpResponse(f"Error sending email: {e}")


from django.shortcuts import render
from django.utils import timezone

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
            'rate': item.amount,
            'qty': item.quantity,
            'total': item.amount * item.quantity
        } for index, item in enumerate(order.order_items.all())],
        'payment_method': order.get_payment_method_display(),
        'sub_total': order.total_amount,
        'discount': order.discount_amount,
        'billed_amt': order.total_amount-order.discount_amount
    }
    
    return render(request, 'receipt.html', {'receipt': receipt_data})






from django.shortcuts import render

def index(request):
    return render(request, 'frontend.html')
