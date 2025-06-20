from django.urls import path
from .views import PayPalWebhookView

urlpatterns = [
    path('paypal/webhook/', PayPalWebhookView.as_view(), name='paypal-webhook'),
]