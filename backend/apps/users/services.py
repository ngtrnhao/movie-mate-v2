from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailVerificationToken

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
