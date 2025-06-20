from django.db import models
from django.conf import settings
# Create your models here.

class PaymentTransaction(models.Model):
    PLANS_CHOICES = [
        ('basic','Basic'),
        ('standard','Standard'),
        ('vip','VIP')
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLANS_CHOICES)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paypal_order_id = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=32)
    raw_data = models.JSONField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
