

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from reservation.models import Reservation, ReservationStatus
from restaurant.models import Order, OrderStatus

from .forms import LoginForm, OrderForm, ReservationForm
from .models import Notification
from .serializers import NotificationSerializer


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
                return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


@login_required(login_url="/login/")
def index(request):
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


@login_required(login_url="/login/")
def dashboard(request):
    return render(request, "home/map.html")

# from django.contrib.auth.models import User
@login_required(login_url="/login/")
def order(request):
    # User.objects.all().update(first_name='ZAMAN', last_name='Chaudhary')
    orders = Order.objects.filter(order_status__in=[
        # add paid here
        OrderStatus.PAID, OrderStatus.IN_PROGRESS, OrderStatus.OUT_FOR_DELIVERY
    ])
    return render(request, "home/tables.html", {"orders": orders})


# @csrf_exempt
@login_required(login_url="/login/")
def update_reservation_status(request):
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        new_status = request.POST.get('status')

        reservation = get_object_or_404(Reservation, id=reservation_id)
        reservation.status = new_status
        reservation.save()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required(login_url="/login/")
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


@login_required(login_url="/login/")
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
        request, 'home/order.html', {'form': form, 'order_items': order.order_items.all()}
    )


class ReservationCreateView(View):
    def get(self, request):
        form = ReservationForm()
        return render(request, 'home/user.html', {'form': form})

    def post(self, request):
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success_url')  # Redirect to a success page
        return render(request, 'your_template.html', {'form': form})


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
