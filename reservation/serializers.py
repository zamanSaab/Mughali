from csv import excel
from rest_framework import serializers
from .models import Reservation, ReservationStatus
from .utils import get_max_seats_count, get_reserved_seats


class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Reservation
        fields = '__all__'
        extra_kwargs = {
            'date': {'required': True},
            'start_time': {'required': True},
            'no_of_person': {'required': True},
        }

    def validate_status(self, status):
        request = self.context.get('request')
        if request and request.method == 'POST':
            if status != ReservationStatus.PENDING:
                raise serializers.ValidationError(
                    f"You can not create order in {ReservationStatus.choices[ReservationStatus.PENDING][1]} state."
                )
        return status

    def validate(self, attrs):
        if attrs.get('status') in [ReservationStatus.CANCELLED, ReservationStatus.COMPLETED]:
            return attrs

        date = attrs.get('date')
        start_time = attrs.get('start_time')
        required_seats = attrs.get('no_of_person')
        max_seats = get_max_seats_count()
        reserved_seates = get_reserved_seats(date, start_time)

        if (max_seats - reserved_seates) < required_seats:
            raise serializers.ValidationError("Not enough seats available.")
        return attrs

