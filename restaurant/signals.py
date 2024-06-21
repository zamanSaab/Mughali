
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django_rest_passwordreset.signals import reset_password_token_created
from email import message
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.dispatch import receiver
# from djstripe.signals import webhook_processing
# from djstripe.models import Event

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
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from restaurant_info.models import RestaurantConfiguration


@receiver(pre_save, sender=Order)
def store_original_order_status(sender, instance, **kwargs):
    if instance.pk:
        # Get the original order from the database
        original_order = Order.objects.get(pk=instance.pk)
        # Store the original status in the instance
        instance._original_order_status = original_order.order_status


@receiver(post_save, sender=Order)
def send_email_on_paid_status(sender, instance, **kwargs):
    # Check if the original status exists and if it has changed to PAID
    if hasattr(instance, '_original_order_status') and instance._original_order_status != OrderStatus.PAID and instance.order_status == OrderStatus.PAID:
        Notification.objects.create(
            message=f"{instance.user.username} placed an order for {instance.get_order_type_display()}",
            redirect_url=f"{settings.BACKEND_URL}admin-dashboard/order/{instance.id}/",
            notification_type='order'
        )

        subject = 'Your Order is Paid'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.user.email]

        min_delivery_time = 45
        delivery_time_in_min = RestaurantConfiguration.objects.filter(
            title='DeliveryConfig', key='delivery_time_in_min'
        ).first()
        if delivery_time_in_min:
            min_delivery_time = delivery_time_in_min.value

        # Create the HTML content
        html_content = render_to_string('email_template.html', {
            'title':  "Order confirmed",
            'username': instance.user.username,
            'message': f'Your order has been marked as Paid.\n\nYour order will be delivered in the next {min_delivery_time} minutes',
            # 'logo_url': 'https://yourwebsite.com/path-to-your-logo.png'
        })
        # Strip the HTML tags for the plain text version
        text_content = strip_tags(html_content)

        # Create the email
        email = EmailMultiAlternatives(
            subject, text_content, from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")
        email.send()


@receiver(post_save, sender=Reservation)
def send_email_on_confirm_booking(sender, instance, **kwargs):
    # import pdb; pdb.set_trace()
    # settings.MEDIA_URL
    if instance.status == ReservationStatus.PENDING:
        Notification.objects.create(
            message=f"{instance.user.username} requests a booking on {instance.date}",
            redirect_url=f"{settings.BACKEND_URL}admin-dashboard/reservation/{instance.id}/",
            notification_type='booking'
        )
    elif instance.status in [ReservationStatus.CANCELLED, ReservationStatus.CONFIRMED]:

        subject = f'Your Booking in Mughali restaurant is {instance.get_status_display()}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.user.email]

        # Create the HTML content
        html_content = render_to_string('email_template.html', {
            'title':  "Mughali restaurant booking",
            'username': instance.user.username,
            'message': f'Your booking for Mughali restaurant has been {instance.get_status_display()} from {instance.start_time} to {instance.end_time} on {instance.date}.'
            # 'logo_url': 'https://yourwebsite.com/path-to-your-logo.png'
        })
        # Strip the HTML tags for the plain text version
        text_content = strip_tags(html_content)

        # Create the email
        email = EmailMultiAlternatives(
            subject, text_content, from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")

        # # Send the email
        email.send()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    # email_plaintext_message = f"Your reset token is {reset_password_token.key}"

    # Customize email sending logic here
    user = reset_password_token.user
    subject = "Password Reset for {title}".format(title="Mughali")
    # import pdb; pdb.set_trace()
    uid = urlsafe_base64_encode(force_bytes(user.id))
    html_content = render_to_string('password_reset_email.html', {
                                    'protocol': 'https', 'domain': 'zaman.pythonanywhere.com', 'uid': uid, 'token': reset_password_token})
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        subject, text_content, settings.EMAIL_HOST_USER, [user.email])
    email.attach_alternative(html_content, "text/html")
    email.send()

    #     return Response(serializer.data, status=status.HTTP_200_OK)
    # send_mail(
    #     # title:
    #     "Password Reset for {title}".format(title="Mughali"),
    #     # message:
    #     email_plaintext_message,
    #     # from:
    #     "zchaudhary09@gmail.com",
    #     # to:
    #     [reset_password_token.user.email]
    # )


# @receiver(webhook_processing)
# def handle_webhook_event(sender, event, **kwargs):
#     # Custom logic for handling the webhook event
#     if event.type == "invoice.payment_succeeded":
#         # Handle the event
#         print("Invoice payment succeeded!")
