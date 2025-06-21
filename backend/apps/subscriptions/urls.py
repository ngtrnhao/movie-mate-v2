from django.urls import path
from .views import PayPalWebhookView, PaymentTransactionView

urlpatterns = [
    path('paypal/webhook/', PayPalWebhookView.as_view(), name='paypal-webhook'),
    path('payment-transaction/<int:user_id>/', PaymentTransactionView.as_view(), name='payment-transaction'),
]
