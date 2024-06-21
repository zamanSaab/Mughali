from django.contrib.auth.forms import SetPasswordForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from reservation.models import Reservation, ReservationStatus
from restaurant.models import Order


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))


class ReservationForm(forms.ModelForm):
    common_attrs = {'class': 'form-control'}

    fields_config = {
        'name': {'max_length': 100, 'placeholder': 'Enter your name'},
        'no_of_person': {'placeholder': 'Enter No. of person'},
        'note': {'placeholder': 'Enter any note'},
        'phone': {'type': 'tel', 'placeholder': 'Enter phone number'}
    }

    status = forms.ChoiceField(
        choices=ReservationStatus.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'Enter Date'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'type': 'time', 'class': 'form-control', 'placeholder': 'Enter start time'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'type': 'time', 'class': 'form-control', 'placeholder': 'Enter end time'})
    )

    class Meta:
        model = Reservation
        fields = ['no_of_person', 'date', 'start_time',
                  'end_time', 'note', 'name', 'status', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, config in self.fields_config.items():
            field = self.fields.get(field_name)
            if field:
                widget = field.widget
                if 'type' in config:
                    widget.attrs['type'] = config['type']
                widget.attrs.update(self.common_attrs)
                if 'placeholder' in config:
                    widget.attrs['placeholder'] = config['placeholder']
                if 'disabled' in config:
                    field.disabled = config['disabled']


class OrderForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Order
        fields = [
            'user', 'order_type', 'order_status', 'address',
            'zip_code', 'phone', 'timestamp', 'total_amount', 'payment_method'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'order_type': forms.Select(attrs={'class': 'form-control'}),
            'order_status': forms.Select(attrs={
                'class': 'form-control', 'style': 'border-color: #ca52e3 !important;'
            }),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'timestamp': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local',
                       'style': 'color: white !important;'}
            ),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['name'].initial = f"{self.instance.user.first_name} {self.instance.user.last_name}"
        # Initialize the timestamp field with a formatted date if not already set
        self.fields['timestamp'].initial = self.instance.timestamp.strftime(
            '%Y-%m-%dT%H:%M')

        # Set all fields except order_status to read-only or disabled
        for field in self.fields:
            if field != 'order_status':
                self.fields[field].required = False
                self.fields[field].widget.attrs['readonly'] = True
                self.fields[field].widget.attrs['disabled'] = True
                self.fields[field].widget.attrs['style'] = 'color: white;'


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update(
            {'class': 'form-control col-md-12 px-md-1'})
        self.fields['new_password2'].widget.attrs.update(
            {'class': 'form-control col-md-12 px-md-1'})

        # # Assigning form-control class to error messages
        # for field_name, field in self.fields.items():
        #     if field.errors:
        #         field.widget.attrs['class'] += ' alert alert-danger mt-2'
