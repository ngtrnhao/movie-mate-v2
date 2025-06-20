from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import PaymentTransaction
from django.utils import timezone
from datetime import timedelta
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class PayPalWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        logger.info("====== PAYPAL WEBHOOK RECEIVED ======")
        event = request.data
        resource = event.get('resource', {})
        order_id = resource.get('id')
        status_paypal = resource.get('status')
        amount = resource.get('purchase_units', [{}])[0].get('amount', {}).get('value')
        custom_id = resource.get('purchase_units', [{}])[0].get('custom_id')
        plan = resource.get('purchase_units', [{}])[0].get('description')
        logger.info(f"Plan received from PayPal: '{plan}'")
        logger.info(f"Status received from PayPal: '{status_paypal}'")
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
            logger.error(f"User with custom_id {custom_id} not found!")
            return Response({'error': 'User not found'}, status=400)

        logger.info(f"Processing for user: {user.email}")

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
            logger.info("Status is COMPLETED. Entering user_type update logic...")
            plan_code = plan.lower()
            logger.info(f"Plan converted to lowercase: '{plan_code}'")

            user_type_updated = False
            if plan_code == 'basic':
                user.user_type = 'prenium_basic'
                user_type_updated = True
                logger.info("Matched 'basic'. Set user_type to 'prenium_basic'.")
            elif plan_code == 'standard':
                user.user_type = 'prenium_standard'
                user_type_updated = True
                logger.info("Matched 'standard'. Set user_type to 'prenium_standard'.")
            elif plan_code == 'vip':
                user.user_type = 'prenium_vip'
                user_type_updated = True
                logger.info("Matched 'vip'. Set user_type to 'prenium_vip'.")

            if user_type_updated:
                logger.info("Attempting to save user...")
                user.save()
                logger.info(f"User {user.email} saved successfully!")
            else:
                logger.warning(f"No plan matched for '{plan_code}'. User_type not updated.")
        else:
            logger.warning(f"Status is '{status_paypal}', not 'COMPLETED'. Skipping user_type update.")

        logger.info("====== PAYPAL WEBHOOK PROCESSING FINISHED ======")
        return Response({'status': 'ok'})