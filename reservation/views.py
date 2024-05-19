
from rest_framework.response import Response
from rest_framework import status
from .models import Reservation, ReservationStatus
from .serializers import ReservationSerializer
from rest_framework import permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication
from .utils import get_max_seats_count, get_reserved_seats

from rest_framework.viewsets import GenericViewSet
class ReservationViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, GenericViewSet
):
    authentication_classes = (SessionAuthentication, )
    serializer_class = ReservationSerializer

    def get_permissions(self):
        self.permission_classes = [permissions.IsAuthenticated]
        if self.request.method not in ['POST', 'GET']:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        return Reservation.objects.filter(
        status__in=[
            ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.IN_PROGRESS
        ]
    )

    @action(detail=False, methods=['get'], url_path='available-seats')
    def available_seats(self, request):
        date = request.query_params.get('date')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        if not all([date, start_time, end_time]):
            return Response(
                {'error': 'date, start_time, and end_time are required parameters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        max_seats = get_max_seats_count()
        reserved_seates = get_reserved_seats(date, start_time)

        return Response({'total_available_seats': (max_seats - reserved_seates) or 0})


from django.shortcuts import render

def item_list(request):
    items = Reservation.objects.all()
    return render(request, 'item_list.html', {'items': items})

from django.views.generic import ListView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.utils.decorators import method_decorator
from .models import Reservation

class ReservationListView(ListView):
    model = Reservation
    template_name = 'home/login.html'#'reservations/reservation_list.html'
    context_object_name = 'reservations'


    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by('-date', '-start_time')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ReservationStatus.choices
        context['update_status_url'] = reverse('update-reservation-status')
        return context

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Reservation

# @csrf_exempt
# @require_POST
# def update_reservation_status(request):
#     # import pdb; pdb.set_trace()
#     reservation_id = request.POST.get('reservation_id')
#     new_status = request.POST.get('status')

#     try:
#         reservation = Reservation.objects.get(id=reservation_id)
#         reservation.status = new_status
#         reservation.save()
#         return JsonResponse({'success': True})
#     except Reservation.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'Reservation not found'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)
@csrf_exempt
def update_reservation_status(request):
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        new_status = request.POST.get('status')

        try:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.status = new_status
            reservation.save()
            return JsonResponse({'success': True})
        except Reservation.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reservation does not exist'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})