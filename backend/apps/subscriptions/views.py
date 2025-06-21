from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import PaymentTransaction
from django.utils import timezone
from datetime import timedelta
import json
import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

User = get_user_model()
logger = logging.getLogger(__name__)

class PaymentTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Get latest active payment transaction for user"""
        try:
            # Check if user exists
            user = User.objects.get(id=user_id)

            # Get latest active payment transaction
            latest_transaction = PaymentTransaction.objects.filter(
                user=user,
                status='COMPLETED',
                end_date__gte=timezone.now()
            ).order_by('-end_date').first()

            if latest_transaction:
                return Response({
                    'has_active_subscription': True,
                    'subscription_start_date': latest_transaction.start_date,
                    'subscription_end_date': latest_transaction.end_date,
                    'plan': latest_transaction.plan,
                    'amount': str(latest_transaction.amount),
                    'user_type': user.user_type
                })
            else:
                return Response({
                    'has_active_subscription': False,
                    'user_type': user.user_type
                })

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting payment transaction: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        logger.info(f"Custom ID received from PayPal: '{custom_id}'")

        # Validate required fields
        if not custom_id:
            logger.error("Custom ID is missing from PayPal webhook")
            return Response({'error': 'Custom ID is required'}, status=400)

        if not order_id:
            logger.error("Order ID is missing from PayPal webhook")
            return Response({'error': 'Order ID is required'}, status=400)

        if not plan:
            logger.error("Plan is missing from PayPal webhook")
            return Response({'error': 'Plan is required'}, status=400)

        custom_field = resource.get('purchase_units', [{}])[0].get('custom')
        duration = 1
        if custom_field:
            try:
                duration = int(json.loads(custom_field).get('duration', 1))
            except Exception as e:
                logger.warning(f"Failed to parse custom field duration: {e}")
                duration = 1

        # Find user by custom_id (user ID)
        try:
            user = User.objects.get(id=custom_id)
            logger.info(f"Processing for user: {user.email} (ID: {user.id})")
        except User.DoesNotExist:
            logger.error(f"User with custom_id {custom_id} not found!")
            return Response({'error': 'User not found'}, status=400)
        except ValueError:
            logger.error(f"Invalid custom_id format: {custom_id}")
            return Response({'error': 'Invalid custom ID format'}, status=400)

        # Calculate subscription dates
        now = timezone.now()
        last_tx = PaymentTransaction.objects.filter(
            user=user,
            status='COMPLETED',
            end_date__gte=now
        ).order_by('-end_date').first()

        start_date = last_tx.end_date if last_tx else now
        end_date = start_date + timedelta(days=30 * duration)

        # Create or update payment transaction
        try:
            payment_transaction, created = PaymentTransaction.objects.update_or_create(
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
            logger.info(f"Payment transaction {'created' if created else 'updated'}: {payment_transaction.id}")
        except Exception as e:
            logger.error(f"Failed to create/update payment transaction: {e}")
            return Response({'error': 'Failed to process payment'}, status=500)

        # Update user type if payment is successful
        if status_paypal.upper() in ['COMPLETED', 'APPROVED']:
            logger.info(f"Status is '{status_paypal}'. Entering user_type update logic...")
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
                try:
                    logger.info("Attempting to save user...")
                    user.save()
                    logger.info(f"User {user.email} saved successfully with new type: {user.user_type}!")
                except Exception as e:
                    logger.error(f"Failed to save user: {e}")
                    return Response({'error': 'Failed to update user type'}, status=500)
            else:
                logger.warning(f"No plan matched for '{plan_code}'. User_type not updated.")
        else:
            logger.warning(f"Status is '{status_paypal}', not one of ['COMPLETED', 'APPROVED']. Skipping user_type update.")

        logger.info("====== PAYPAL WEBHOOK PROCESSING FINISHED ======")
        return Response({'status': 'ok'})
