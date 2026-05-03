"""
Cashfree Payment Gateway Implementation

Implements the BasePaymentGateway interface for Cashfree APIs.
Uses the SDK for Payment Gateway (PG) and direct REST API for Payouts (v2024-01-01).
"""

import logging
import time
import hashlib
import hmac
import json
import requests
import base64
from typing import Optional, Dict, Any
from django.conf import settings

from .base_gateway import BasePaymentGateway

logger = logging.getLogger(__name__)

# Cashfree PG SDK (v3.2.12)
try:
    import cashfree_pg
    from cashfree_pg.api_client import Cashfree
    from cashfree_pg.models.create_order_request import CreateOrderRequest
    from cashfree_pg.models.customer_details import CustomerDetails
    from cashfree_pg.models.order_meta import OrderMeta
    
    CASHFREE_PG_AVAILABLE = True
except ImportError:
    logger.warning("Cashfree PG SDK not installed. Install with: pip install cashfree-pg==3.2.12")
    CASHFREE_PG_AVAILABLE = False


class CashfreeGateway(BasePaymentGateway):
    """Cashfree payment gateway implementation."""
    
    def __init__(self):
        # PG SDK Initialization
        if CASHFREE_PG_AVAILABLE:
            Cashfree.XClientId = settings.CASHFREE_APP_ID
            Cashfree.XClientSecret = settings.CASHFREE_SECRET_KEY
            Cashfree.XEnvironment = (
                Cashfree.SANDBOX if "sandbox" in settings.CASHFREE_PG_BASE_URL.lower() 
                else Cashfree.PRODUCTION
            )
            self.pg_client = Cashfree()
        else:
            self.pg_client = None


    
    def get_name(self) -> str:
        return 'cashfree'



    def create_order(self, amount: float, trip_id: int, currency: str = 'INR') -> Optional[Dict[str, Any]]:
        """Create a Cashfree order using PG SDK."""
        if not self.pg_client:
            logger.error("Cashfree PG SDK not available")
            return None
            
        try:
            order_id = f"trip_{trip_id}_{int(time.time())}"
            customer_details = CustomerDetails(
                customer_id=str(trip_id),
                customer_phone="9999999999",
                customer_email="user@example.com"
            )
            order_meta = OrderMeta(
                return_url=f"{settings.FRONTEND_URL}/payment/callback?order_id={order_id}",
                notify_url=f"{settings.BACKEND_URL}/api/payments/webhook/"
            )
            order_request = CreateOrderRequest(
                order_amount=float(amount),
                order_currency=currency,
                order_id=order_id,
                customer_details=customer_details,
                order_meta=order_meta
            )
            
            # v3.x SDK style
            response = self.pg_client.PGCreateOrder(order_request, "2023-08-01")
            
            if response and hasattr(response, 'data'):
                return {
                    'gateway': 'cashfree',
                    'gateway_order_id': order_id,
                    'order_id': order_id,
                    'payment_session_id': getattr(response.data, 'payment_session_id', None),
                    'order_amount': float(amount),
                    'payment_link': getattr(response.data, 'payment_link', None),
                    'cf_order_id': getattr(response.data, 'cf_order_id', None),
                }
            return None
        except Exception as e:
            logger.error(f"CashfreeGateway.create_order failed: {e}")
            return None

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verify payment via order status API."""
        order_status = self.get_order_status(order_id)
        return order_status.get('payment_status') == 'SUCCESS' if order_status else False

    def verify_webhook_signature(self, body: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """Verify Cashfree webhook signature (V2/V3)."""
        if not getattr(settings, 'CASHFREE_WEBHOOK_SECRET', None):
            return True # Dev fallback
        
        try:
            body_str = body.decode('utf-8') if isinstance(body, bytes) else str(body)
            secret = settings.CASHFREE_WEBHOOK_SECRET.encode('utf-8')
            
            if timestamp:
                message = timestamp + body_str
                computed = base64.b64encode(hmac.new(secret, message.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
            else:
                computed = hmac.new(secret, body_str.encode('utf-8'), hashlib.sha256).hexdigest()
            
            return hmac.compare_digest(computed, signature)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False

    def create_refund(self, payment_id: str, amount: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Create a Cashfree refund using PG SDK."""
        if not self.pg_client: return None
        try:
            refund_id = f"refund_{payment_id}_{int(time.time())}"
            response = self.pg_client.PGOrderCreateRefund(
                payment_id, refund_id, str(float(amount)) if amount else None, "Trip cancellation", "2023-08-01"
            )
            if response and hasattr(response, 'data'):
                return {
                    'gateway': 'cashfree',
                    'refund_id': refund_id,
                    'status': getattr(response.data, 'status', 'PENDING'),
                    'cf_refund_id': getattr(response.data, 'cf_refund_id', None),
                }
            return None
        except Exception as e:
            logger.error(f"Refund failed: {e}")
            return None



    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status using PG SDK."""
        if not self.pg_client: return None
        try:
            response = self.pg_client.PGFetchOrder(order_id, "2023-08-01")
            if response and hasattr(response, 'data'):
                return {
                    'gateway': 'cashfree',
                    'order_id': order_id,
                    'order_status': getattr(response.data, 'order_status', None),
                    'payment_status': getattr(response.data, 'payment_status', None),
                }
            return None
        except Exception as e:
            logger.error(f"Fetch order failed: {e}")
            return None




