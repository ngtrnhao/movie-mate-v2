from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailVerificationToken, PasswordResetToken
from django.utils import timezone
from datetime import timedelta

def send_verification_email(user):

    token = EmailVerificationToken.objects.create(user=user)


    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    context = {
        'user': user,
        'verification_url': verification_url
    }


    html_message = render_to_string('users/email/verification.html', context)
    plain_message = strip_tags(html_message)



    send_mail(
        subject='Verify your email address',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )

    return token

def send_password_reset_email(user):
    token, created = PasswordResetToken.objects.get_or_create(
        user = user,
        defaults = {'expires_at':timezone.now() + timedelta(hours=24)}
    )

    if not created and not token.is_valid():
        token.delete()
        token = PasswordResetToken.objects.create(
            user = user,
            expires_at = timezone.now() + timedelta(hours=24)
        )
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
    context = {
        'user': user,
        'reset_url': reset_url
    }

    html_message = render_to_string('users/email/password_reset.html',context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject = 'Reset your password',
        message = plain_message,
        from_email = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [user.email],
        html_message = html_message
    )
    return token