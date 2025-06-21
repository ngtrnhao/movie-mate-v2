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

class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new payment for subscription"""
        try:
            plan = request.data.get('plan')
            duration = request.data.get('duration', 1)
            amount = request.data.get('amount')
            currency = request.data.get('currency', 'USD')

            # Validate required fields
            if not plan:
                return Response(
                    {'error': 'Plan is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not amount:
                return Response(
                    {'error': 'Amount is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user already has an active subscription
            user = request.user
            latest_transaction = PaymentTransaction.objects.filter(
                user=user,
                status='COMPLETED',
                end_date__gte=timezone.now()
            ).order_by('-end_date').first()

            # Check if user is trying to buy the same plan
            if latest_transaction and latest_transaction.plan.lower() == plan.lower():
                days_until_expiry = (latest_transaction.end_date - timezone.now()).days
                if days_until_expiry > 7:  # More than 7 days left
                    return Response({
                        'error': f'You already have an active {plan} subscription valid until {latest_transaction.end_date.strftime("%Y-%m-%d")}. Please wait until it\'s closer to expiry to renew.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Check if user is trying to downgrade too early
            if latest_transaction and latest_transaction.plan.lower() != plan.lower():
                plan_levels = {'basic': 1, 'standard': 2, 'vip': 3}
                current_level = plan_levels.get(latest_transaction.plan.lower(), 0)
                new_level = plan_levels.get(plan.lower(), 0)

                if new_level < current_level:  # Downgrade
                    days_until_expiry = (latest_transaction.end_date - timezone.now()).days
                    if days_until_expiry > 30:  # More than 30 days left
                        return Response({
                            'error': f'You can only downgrade your plan when it\'s within 30 days of expiry. Your current plan expires on {latest_transaction.end_date.strftime("%Y-%m-%d")}.'
                        }, status=status.HTTP_400_BAD_REQUEST)

            # Create PayPal order (this would integrate with PayPal API)
            # For now, we'll return a mock response
            paypal_order_id = f"PAY-{timezone.now().strftime('%Y%m%d%H%M%S')}-{user.id}"

            # Calculate subscription dates
            now = timezone.now()
            start_date = latest_transaction.end_date if latest_transaction else now
            end_date = start_date + timedelta(days=30 * duration)

            # Create payment transaction (pending status)
            payment_transaction = PaymentTransaction.objects.create(
                user=user,
                plan=plan,
                amount=amount,
                status='PENDING',
                paypal_order_id=paypal_order_id,
                start_date=start_date,
                end_date=end_date,
                raw_data={'created_via': 'create_payment_api'}
            )

            # Mock PayPal approval URL (in real implementation, this would come from PayPal API)
            approval_url = f"https://www.paypal.com/checkoutnow?token={paypal_order_id}"

            logger.info(f"Created payment for user {user.email}: plan={plan}, duration={duration}, amount={amount}")

            return Response({
                'success': True,
                'data': {
                    'payment_id': payment_transaction.id,
                    'paypal_order_id': paypal_order_id,
                    'approval_url': approval_url,
                    'plan': plan,
                    'duration': duration,
                    'amount': amount,
                    'currency': currency
                }
            })

        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return Response(
                {'error': 'Failed to create payment'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Get latest active payment transaction for user"""
        try:
            user = User.objects.get(id=user_id)

            # Find the transaction with the absolute latest end date to determine the subscription's expiry
            ultimate_expiry_tx = PaymentTransaction.objects.filter(
                user=user,
                status='COMPLETED',
                end_date__gte=timezone.now()
            ).order_by('-end_date').first()

            if ultimate_expiry_tx:
                # The user has some active subscription.
                # The authoritative plan is from the user model, as it's updated immediately upon successful payment.
                authoritative_plan_name = user.user_type.replace('prenium_', '') if 'prenium_' in user.user_type else user.user_type

                # Try to find a transaction corresponding to the authoritative plan to get the correct amount.
                authoritative_plan_tx = PaymentTransaction.objects.filter(
                    user=user,
                    status='COMPLETED',
                    plan__iexact=authoritative_plan_name
                ).order_by('-created_at').first()

                # Use the amount from the authoritative plan's transaction, or fall back to the expiry one.
                amount = str(authoritative_plan_tx.amount) if authoritative_plan_tx else str(ultimate_expiry_tx.amount)

                # Calculate days remaining based on the ultimate expiry date.
                days_remaining = (ultimate_expiry_tx.end_date - timezone.now()).days

                plan_levels = {'basic': 1, 'standard': 2, 'vip': 3}
                current_level = plan_levels.get(authoritative_plan_name.lower(), 0)

                return Response({
                    'has_active_subscription': True,
                    'subscription_start_date': ultimate_expiry_tx.start_date,
                    'subscription_end_date': ultimate_expiry_tx.end_date,
                    'plan': authoritative_plan_name,
                    'amount': amount,
                    'user_type': user.user_type,
                    'days_remaining': days_remaining,
                    'plan_level': current_level,
                    'can_renew': days_remaining <= 7,
                    'can_downgrade': days_remaining <= 30,
                    'can_upgrade': True
                })
            else:
                # No active subscription found.
                return Response({
                    'has_active_subscription': False,
                    'user_type': user.user_type,
                    'plan_level': 0,
                    'can_renew': False,
                    'can_downgrade': False,
                    'can_upgrade': True
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
        logger.info(f"Custom field received from PayPal: '{custom_field}'")

        if custom_field:
            try:
                custom_data = json.loads(custom_field)
                duration = int(custom_data.get('duration', 1))
                logger.info(f"Successfully parsed duration: {duration} months from custom field")
            except Exception as e:
                logger.warning(f"Failed to parse custom field duration: {e}")
                duration = 1
        else:
            logger.warning("No custom field found, using default duration: 1 month")

        logger.info(f"Final duration to be used: {duration} months")

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

        # Check if user is trying to buy the same plan
        if last_tx and last_tx.plan.lower() == plan.lower():
            days_until_expiry = (last_tx.end_date - now).days
            if days_until_expiry > 7:  # More than 7 days left
                logger.warning(f"User {user.email} trying to buy same plan with {days_until_expiry} days remaining")
                return Response({
                    'error': f'You already have an active {plan} subscription valid until {last_tx.end_date.strftime("%Y-%m-%d")}. Please wait until it\'s closer to expiry to renew.'
                }, status=400)

        # Check if user is trying to downgrade too early
        if last_tx and last_tx.plan.lower() != plan.lower():
            plan_levels = {'basic': 1, 'standard': 2, 'vip': 3}
            current_level = plan_levels.get(last_tx.plan.lower(), 0)
            new_level = plan_levels.get(plan.lower(), 0)

            if new_level < current_level:  # Downgrade
                days_until_expiry = (last_tx.end_date - now).days
                if days_until_expiry > 30:  # More than 30 days left
                    logger.warning(f"User {user.email} trying to downgrade with {days_until_expiry} days remaining")
                    return Response({
                        'error': f'You can only downgrade your plan when it\'s within 30 days of expiry. Your current plan expires on {last_tx.end_date.strftime("%Y-%m-%d")}.'
                    }, status=400)

        # Calculate start and end dates
        start_date = last_tx.end_date if last_tx else now
        end_date = start_date + timedelta(days=30 * duration)

        logger.info(f"Subscription calculation: start_date={start_date}, end_date={end_date}, duration={duration} months")

        # Log upgrade/downgrade info
        if last_tx and last_tx.plan.lower() != plan.lower():
            plan_levels = {'basic': 1, 'standard': 2, 'vip': 3}
            current_level = plan_levels.get(last_tx.plan.lower(), 0)
            new_level = plan_levels.get(plan.lower(), 0)

            if new_level > current_level:
                logger.info(f"User {user.email} is UPGRADING from {last_tx.plan} to {plan}")
            elif new_level < current_level:
                logger.info(f"User {user.email} is DOWNGRADING from {last_tx.plan} to {plan}")
            else:
                logger.info(f"User {user.email} is SWITCHING from {last_tx.plan} to {plan}")
        elif last_tx and last_tx.plan.lower() == plan.lower():
            logger.info(f"User {user.email} is RENEWING {plan} subscription")
        else:
            logger.info(f"User {user.email} is starting NEW {plan} subscription")

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
