from email import message
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from reservation.models import Reservation, ReservationStatus
from .models import Order, OrderStatus, OrderTypes

# @receiver(post_save, sender=Order)
# def send_email_on_paid_status(sender, instance, **kwargs):
#     # import pdb; pdb.set_trace()
#     if instance.order_status == OrderStatus.PAID:
#         subject = 'Your Order is Paid'
#         message = f'Dear {instance.user.username},\n\nYour order with total amount {instance.total_amount}€ has been marked as Paid.\n\nThank you for shopping with us!'
#         from_email = settings.EMAIL_HOST_USER
#         recipient_list = ['zaman.chaudhary@arbisoft.com']
        
#         send_mail(subject, message, from_email, recipient_list)
#         # send_mail('Test Subject', 'Test message.', 'zchaudhary09@gmail.com', ['zaman.chaudhary@arbisoft.com'], fail_silently=False)


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from admin_dashboard.models import Notification
# from .middleware import get_current_request

@receiver(post_save, sender=Order)
def send_email_on_paid_status(sender, instance, **kwargs):
    # import pdb; pdb.set_trace()
    # settings.MEDIA_URL
    if instance.order_status == OrderStatus.PAID:
        # Notification.objects.create(
        #     message=f"{instance.user.username} placed an order for {instance.get_order_type_display()}",
        #     redirect_url=f"{settings.BACKEND_URL}order/{instance.id}/",
        #     notification_type='order'
        # )

        subject = 'Your Order is Paid'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.user.email]

        # Create the HTML content
        html_content = render_to_string('email_template.html', {
            'title':  "Order confirmed",
            'username': instance.user.username,
            'message': f'Your order with a total amount of { instance.total_amount }€ has been marked as Paid.\n\nYour order will be deliver in next 45 minutes',
            # 'logo_url': 'https://yourwebsite.com/path-to-your-logo.png'
        })
        text_content = strip_tags(html_content)  # Strip the HTML tags for the plain text version

        # Create the email
        email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")

        # Send the email
        # email.send()


@receiver(post_save, sender=Reservation)
def send_email_on_confirm_booking(sender, instance, **kwargs):
    # import pdb; pdb.set_trace()
    # settings.MEDIA_URL
    if instance.status == ReservationStatus.PENDING:
        Notification.objects.create(
            message=f"{instance.user.username} requests a booking on {instance.date}",
            redirect_url=f"{settings.BACKEND_URL}reservation/{instance.id}/",
            notification_type='booking'
        )
    elif instance.status in [ReservationStatus.CANCELLED, ReservationStatus.CONFIRMED]:
        
        subject = f'Your Booking in Mughali restaurant is {instance.get_status_display}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.user.email]

        # Create the HTML content
        html_content = render_to_string('email_template.html', {
            'title':  "Mughali restaurant booking",
            'username': instance.user.username,
            'message': f'Your booking for Mughali restaurant has been {instance.get_status_display} from {instance.start_time} to {instance.end_time} on {instance.date}.'
            # 'logo_url': 'https://yourwebsite.com/path-to-your-logo.png'
        })
        text_content = strip_tags(html_content)  # Strip the HTML tags for the plain text version

        # Create the email
        email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")

        # # Send the email
        # # email.send()