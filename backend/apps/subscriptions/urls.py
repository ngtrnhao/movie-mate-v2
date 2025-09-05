from django.urls import path
from .views import PayPalWebhookView, PaymentTransactionView, CreatePaymentView

urlpatterns = [
    path('paypal/webhook/', PayPalWebhookView.as_view(), name='paypal-webhook'),
    path('payment-transaction/<int:user_id>/', PaymentTransactionView.as_view(), name='payment-transaction'),
    path('create-payment/', CreatePaymentView.as_view(), name='create-payment'),
]
