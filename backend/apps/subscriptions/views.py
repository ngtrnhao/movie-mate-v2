from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import PaymentTransaction
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()

class PayPalWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        event = request.data
        resource = event.get('resource', {})
        order_id = resource.get('id')
        status_paypal = resource.get('status')
        amount = resource.get('purchase_units', [{}])[0].get('amount', {}).get('value')
        custom_id = resource.get('purchase_units', [{}])[0].get('custom_id')
        plan = resource.get('purchase_units', [{}])[0].get('description')
        custom_field = resource.get('purchase_units', [{}])[0].get('custom')
        duration = 1
        if custom_field:
            try:
                duration = int(json.loads(custom_field).get('duration', 1))
            except Exception:
                duration = 1

        try:
            user = User.objects.get(id=custom_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=400)

        now = timezone.now()
        last_tx = PaymentTransaction.objects.filter(user=user, status='COMPLETED', end_date__gte=now).order_by('-end_date').first()
        start_date = last_tx.end_date if last_tx else now
        end_date = start_date + timedelta(days=30 * duration)

        PaymentTransaction.objects.update_or_create(
            paypal_order_id=order_id,
            defaults={
                'user': user,
                'plan': plan,
                'amount': amount,
                'status': status_paypal,
                'raw_data': event,
                'start_date': start_date,
                'end_date': end_date,
            }
        )

        if status_paypal == 'COMPLETED':
            plan_code = plan.lower()
            if plan_code == 'basic':
                user.user_type = 'prenium_basic'
            elif plan_code == 'standard':
                user.user_type = 'prenium_standard'
            elif plan_code == 'vip':
                user.user_type = 'prenium_vip'
            user.save()

        return Response({'status': 'ok'})