"""
Stripe payment service for subscription management
"""
import os
import stripe
from typing import Optional, Dict

# Environment-driven configuration (with safe fallbacks)
_ENV_STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
_ENV_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Set Stripe key only if provided to avoid accidental live calls with placeholders
stripe.api_key = _ENV_STRIPE_KEY or ""
STRIPE_WEBHOOK_SECRET = _ENV_WEBHOOK_SECRET or ""

class PaymentService:
    PLANS = {
        "pro": {
            "price_id": os.getenv("STRIPE_PRICE_ID_PRO_MONTHLY", "price_1SOE2YENa3zBKoIjGn0yD5mN"),
            "amount": 4900,  # $49.00 in cents
            "interval": "month"
        },
        "pro_annual": {
            "price_id": os.getenv("STRIPE_PRICE_ID_PRO_ANNUAL", "price_1SOE2YENa3zBKoIjVmHFP2GX"),
            "amount": 46800,  # $468.00 in cents (20% discount)
            "interval": "year"
        }
    }

    @staticmethod
    def is_configured(require_webhook: bool = False) -> bool:
        """Return True if Stripe is configured.
        For basic checkout we only need a secret key; webhook secret optional.
        Pass require_webhook=True when verifying webhook operations.
        """
        key = _ENV_STRIPE_KEY or ""
        wh = _ENV_WEBHOOK_SECRET or ""
        key_ok = bool(key) and not key.startswith("sk_test_your") and not key.startswith("sk_live_your")
        if require_webhook:
            wh_ok = bool(wh) and len(wh) > 20
            return key_ok and wh_ok
        return key_ok

    @staticmethod
    def create_customer(email: str, name: str) -> Optional[str]:
        """Create a Stripe customer"""
        if not PaymentService.is_configured():
            print("Stripe not configured: skipping create_customer")
            return None
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"source": "estimategenie"}
            )
            return customer.id
        except Exception as e:
            print(f"Error creating Stripe customer: {e}")
            return None

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        plan: str,
        success_url: str,
        cancel_url: str,
        user_id: str
    ) -> Optional[Dict]:
        """Create a Stripe Checkout session"""
        if not PaymentService.is_configured():
            print("Stripe not configured: skipping create_checkout_session")
            return None
        try:
            plan_info = PaymentService.PLANS.get(plan)
            if not plan_info:
                return None

            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": plan_info["price_id"],
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "plan": plan
                }
            )
            
            return {
                "session_id": session.id,
                "url": session.url
            }
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None

    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> Optional[str]:
        """Create a Stripe billing portal session"""
        if not PaymentService.is_configured():
            print("Stripe not configured: skipping create_portal_session")
            return None
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except Exception as e:
            print(f"Error creating portal session: {e}")
            return None

    @staticmethod
    def cancel_subscription(subscription_id: str) -> bool:
        """Cancel a subscription"""
        if not PaymentService.is_configured():
            print("Stripe not configured: skipping cancel_subscription")
            return False
        try:
            stripe.Subscription.delete(subscription_id)
            return True
        except Exception as e:
            print(f"Error canceling subscription: {e}")
            return False

    @staticmethod
    def get_subscription(subscription_id: str) -> Optional[Dict]:
        """Get subscription details"""
        if not PaymentService.is_configured():
            print("Stripe not configured: skipping get_subscription")
            return None
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "plan": subscription.items.data[0].price.id if subscription.items.data else None
            }
        except Exception as e:
            print(f"Error getting subscription: {e}")
            return None

    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Optional[Dict]:
        """Verify Stripe webhook signature and return event"""
        if not PaymentService.is_configured():
            print("Stripe not configured: skipping webhook verification")
            return None
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            return event
        except Exception as e:
            print(f"Error verifying webhook: {e}")
            return None

    @staticmethod
    def handle_webhook_event(event: Dict, auth_service) -> bool:
        """Handle Stripe webhook events"""
        try:
            event_type = event["type"]
            
            if event_type == "checkout.session.completed":
                session = event["data"]["object"]
                user_id = session["metadata"].get("user_id")
                customer_id = session["customer"]
                subscription_id = session["subscription"]
                
                # Update user subscription
                auth_service.update_subscription(
                    user_id=user_id,
                    plan="pro",
                    subscription_id=subscription_id,
                    subscription_status="active"
                )
                
                return True
            
            elif event_type == "customer.subscription.updated":
                subscription = event["data"]["object"]
                subscription_id = subscription["id"]
                status = subscription["status"]
                
                # Find user by subscription ID and update status
                # This would require additional database query
                return True
            
            elif event_type == "customer.subscription.deleted":
                subscription = event["data"]["object"]
                subscription_id = subscription["id"]
                
                # Downgrade user to free plan
                # This would require additional database query
                return True
            
            elif event_type == "invoice.payment_failed":
                invoice = event["data"]["object"]
                customer_id = invoice["customer"]
                
                # Handle failed payment - send email, update status
                return True
            
            return True
            
        except Exception as e:
            print(f"Error handling webhook event: {e}")
            return False
