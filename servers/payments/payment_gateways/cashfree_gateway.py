"""
Cashfree Payment Gateway Implementation

Implements the BasePaymentGateway interface for Cashfree APIs.
"""

import logging
import time
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from django.conf import settings

from .base_gateway import BasePaymentGateway

logger = logging.getLogger(__name__)

try:
    import cashfree_pg
    from cashfree_pg.api_client import Cashfree
    from cashfree_pg.api.payments_api import PaymentsApi
    from cashfree_pg.api.orders_api import OrdersApi
    from cashfree_pg.api.refunds_api import RefundsApi
    from cashfree_pg.models.create_order_request import CreateOrderRequest
    from cashfree_pg.models.customer_details import CustomerDetails
    from cashfree_pg.models.order_meta import OrderMeta
    
    import cashfree_payouts
    from cashfree_payouts.api_client import Payouts
    from cashfree_payouts.api.transfers_api import TransfersApi
    from cashfree_payouts.api.beneficiary_api import BeneficiaryApi
    from cashfree_payouts.models.transfer_request import TransferRequest
    from cashfree_payouts.models.beneficiary_details import BeneficiaryDetails
    from cashfree_payouts.models.beneficiary_details_beneficiary_instrument_details import BeneficiaryDetailsBeneficiaryInstrumentDetails
    from cashfree_payouts.models.beneficiary_details_beneficiary_instrument_details_bank_account import BeneficiaryDetailsBeneficiaryInstrumentDetailsBankAccount
    from cashfree_payouts.models.beneficiary_details_beneficiary_instrument_details_vpa import BeneficiaryDetailsBeneficiaryInstrumentDetailsVpa
    
    CASHFREE_AVAILABLE = True
except ImportError:
    logger.warning("Cashfree SDK not installed. Install with: pip install cashfree-pg cashfree-payouts")
    CASHFREE_AVAILABLE = False


class CashfreeGateway(BasePaymentGateway):
    """Cashfree payment gateway implementation."""
    
    def __init__(self):
        if not CASHFREE_AVAILABLE:
            raise ImportError("Cashfree SDK not installed")
        
        # Initialize Cashfree PG client
        self.pg_client = Cashfree(
            x_client_id=settings.CASHFREE_APP_ID,
            x_client_secret=settings.CASHFREE_SECRET_KEY,
            x_api_version="2023-08-01",
            environment=cashfree_pg.Environment.SANDBOX if "sandbox" in settings.CASHFREE_PG_BASE_URL else cashfree_pg.Environment.PRODUCTION
        )
        
        # Initialize Cashfree Payouts client
        self.payouts_client = Payouts(
            x_client_id=settings.CASHFREE_PAYOUTS_CLIENT_ID,
            x_client_secret=settings.CASHFREE_PAYOUTS_CLIENT_SECRET,
            x_api_version="1.0.0",
            environment=cashfree_payouts.Environment.SANDBOX if "sandbox" in settings.CASHFREE_PAYOUTS_BASE_URL else cashfree_payouts.Environment.PRODUCTION
        )
        
        self.pg_api = PaymentsApi(self.pg_client)
        self.orders_api = OrdersApi(self.pg_client)
        self.refunds_api = RefundsApi(self.pg_client)
        self.transfers_api = TransfersApi(self.payouts_client)
        self.beneficiary_api = BeneficiaryApi(self.payouts_client)
    
    def get_name(self) -> str:
        return 'cashfree'
    
    def create_order(self, amount: float, trip_id: int, currency: str = 'INR') -> Optional[Dict[str, Any]]:
        """Create a Cashfree order."""
        try:
            # Generate unique order ID
            timestamp = int(time.time())
            order_id = f"trip_{trip_id}_{timestamp}"
            
            # Create customer details (minimal for now)
            customer_details = CustomerDetails(
                customer_id=str(trip_id),
                customer_phone="9999999999",  # Default, should be updated
                customer_email="user@example.com"  # Default, should be updated
            )
            
            # Create order meta
            order_meta = OrderMeta(
                return_url=f"{settings.FRONTEND_URL}/payment/callback?order_id={order_id}",
                notify_url=f"{settings.BACKEND_URL}/api/payments/webhook/"
            )
            
            # Create order request
            order_request = CreateOrderRequest(
                order_amount=float(amount),
                order_currency=currency,
                order_id=order_id,
                customer_details=customer_details,
                order_meta=order_meta
            )
            
            # Create order
            response = self.orders_api.create_order(order_request)
            
            if response and hasattr(response, 'payment_session_id'):
                return {
                    'gateway': 'cashfree',
                    'gateway_order_id': order_id,
                    'order_id': order_id,
                    'payment_session_id': response.payment_session_id,
                    'order_amount': float(amount),
                    'order_currency': currency,
                    'payment_link': response.payment_link if hasattr(response, 'payment_link') else None,
                    'cf_order_id': response.cf_order_id if hasattr(response, 'cf_order_id') else None,
                }
            return None
            
        except Exception as e:
            logger.error(f"CashfreeGateway.create_order failed: {e}")
            return None
    
    def verify_payment_signature(
        self, 
        order_id: str, 
        payment_id: str, 
        signature: str
    ) -> bool:
        """
        Verify Cashfree payment signature.
        
        Note: Cashfree doesn't provide frontend signature verification like Razorpay.
        Instead, we verify via order status API or webhook signature.
        For frontend, we'll check order status.
        """
        # For Cashfree, we verify by checking order status
        order_status = self.get_order_status(order_id)
        if not order_status:
            return False
        
        # Check if payment is successful
        return order_status.get('payment_status') == 'SUCCESS'
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Verify Cashfree webhook signature."""
        if not hasattr(settings, 'CASHFREE_WEBHOOK_SECRET') or not settings.CASHFREE_WEBHOOK_SECRET:
            logger.warning("Cashfree webhook secret not configured")
            return True  # Allow in dev
        
        try:
            # Convert body to string if bytes
            if isinstance(body, bytes):
                body_str = body.decode('utf-8')
            else:
                body_str = str(body)
            
            # Compute signature
            secret = settings.CASHFREE_WEBHOOK_SECRET.encode('utf-8')
            computed_signature = hmac.new(
                secret,
                body_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(computed_signature, signature)
            
        except Exception as e:
            logger.error(f"CashfreeGateway.verify_webhook_signature failed: {e}")
            return False
    
    def create_refund(self, payment_id: str, amount: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Create a Cashfree refund."""
        try:
            # Generate unique refund ID
            timestamp = int(time.time())
            refund_id = f"refund_{payment_id}_{timestamp}"
            
            # Create refund request
            refund_amount = str(float(amount)) if amount is not None else None
            
            # Note: Cashfree PG SDK refund API might be different
            # This is a simplified implementation
            # In production, use the actual Cashfree refund API
            response = self.refunds_api.create_refund(
                order_id=payment_id,  # Using payment_id as order_id for simplicity
                refund_id=refund_id,
                refund_amount=refund_amount,
                refund_note="Refund for trip cancellation"
            )
            
            if response:
                return {
                    'gateway': 'cashfree',
                    'gateway_refund_id': refund_id,
                    'refund_id': refund_id,
                    'refund_amount': refund_amount,
                    'status': response.status if hasattr(response, 'status') else 'PENDING',
                    'cf_refund_id': response.cf_refund_id if hasattr(response, 'cf_refund_id') else None,
                }
            return None
            
        except Exception as e:
            logger.error(f"CashfreeGateway.create_refund failed: {e}")
            return None
    
    def create_payout(
        self,
        contact_id: str,
        account_number: str,
        ifsc_code: str,
        amount: float,
        purpose: str = "payout",
        currency: str = "INR"
    ) -> Optional[Dict[str, Any]]:
        """Create a Cashfree payout to bank account."""
        try:
            # Generate unique transfer ID
            timestamp = int(time.time())
            transfer_id = f"bank_{contact_id}_{timestamp}"
            
            # Create transfer request
            transfer_request = TransferRequest(
                beneficiary_id=contact_id,
                transfer_id=transfer_id,
                transfer_amount=str(float(amount)),
                transfer_currency=currency,
                transfer_mode="banktransfer",
                transfer_remarks=f"Driver payout - {purpose}"
            )
            
            # Create transfer
            response = self.transfers_api.initiate_transfer(transfer_request)
            
            if response:
                return {
                    'gateway': 'cashfree',
                    'gateway_payout_id': transfer_id,
                    'transfer_id': transfer_id,
                    'transfer_amount': str(float(amount)),
                    'transfer_currency': currency,
                    'status': response.status if hasattr(response, 'status') else 'PENDING',
                    'utr': response.utr if hasattr(response, 'utr') else None,
                    'reference_id': response.reference_id if hasattr(response, 'reference_id') else None,
                }
            return None
            
        except Exception as e:
            logger.error(f"CashfreeGateway.create_payout failed: {e}")
            return None
    
    def create_upi_payout(
        self,
        upi_id: str,
        amount: float,
        purpose: str = "payout",
        currency: str = "INR"
    ) -> Optional[Dict[str, Any]]:
        """Create a Cashfree payout to UPI ID."""
        try:
            # For UPI payout, we need a beneficiary with UPI details
            # First, create or get beneficiary ID
            beneficiary_id = f"upi_{hashlib.md5(upi_id.encode()).hexdigest()[:12]}"
            
            # Generate unique transfer ID
            timestamp = int(time.time())
            transfer_id = f"upi_{beneficiary_id}_{timestamp}"
            
            # Create transfer request for UPI
            transfer_request = TransferRequest(
                beneficiary_id=beneficiary_id,
                transfer_id=transfer_id,
                transfer_amount=str(float(amount)),
                transfer_currency=currency,
                transfer_mode="upi",
                transfer_remarks=f"Driver UPI payout - {purpose}"
            )
            
            # Create transfer
            response = self.transfers_api.initiate_transfer(transfer_request)
            
            if response:
                return {
                    'gateway': 'cashfree',
                    'gateway_payout_id': transfer_id,
                    'transfer_id': transfer_id,
                    'transfer_amount': str(float(amount)),
                    'transfer_currency': currency,
                    'status': response.status if hasattr(response, 'status') else 'PENDING',
                    'utr': response.utr if hasattr(response, 'utr') else None,
                    'reference_id': response.reference_id if hasattr(response, 'reference_id') else None,
                }
            return None
            
        except Exception as e:
            logger.error(f"CashfreeGateway.create_upi_payout failed: {e}")
            return None
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get Cashfree order status."""
        try:
            response = self.orders_api.get_order(order_id)
            
            if response:
                return {
                    'gateway': 'cashfree',
                    'gateway_order_id': order_id,
                    'order_id': order_id,
                    'order_amount': response.order_amount if hasattr(response, 'order_amount') else None,
                    'order_currency': response.order_currency if hasattr(response, 'order_currency') else None,
                    'order_status': response.order_status if hasattr(response, 'order_status') else None,
                    'payment_status': response.payment_status if hasattr(response, 'payment_status') else None,
                    'order_expiry_time': response.order_expiry_time if hasattr(response, 'order_expiry_time') else None,
                    'order_note': response.order_note if hasattr(response, 'order_note') else None,
                    'order_tags': response.order_tags if hasattr(response, 'order_tags') else None,
                    'order_splits': response.order_splits if hasattr(response, 'order_splits') else None,
                }
            return None
            
        except Exception as e:
            logger.error(f"CashfreeGateway.get_order_status failed: {e}")
            return None
    
    def get_payout_status(self, payout_id: str) -> Optional[Dict[str, Any]]:
        """Get Cashfree payout status."""
        try:
            response = self.transfers_api.get_transfer_status(payout_id)
            
            if response:
                return {
                    'gateway': 'cashfree',
                    'gateway_payout_id': payout_id,
                    'transfer_id': payout_id,
                    'transfer_amount': response.transfer_amount if hasattr(response, 'transfer_amount') else None,
                    'transfer_currency': response.transfer_currency if hasattr(response, 'transfer_currency') else None,
                    'transfer_mode': response.transfer_mode if hasattr(response, 'transfer_mode') else None,
                    'status': response.status if hasattr(response, 'status') else None,
                    'utr': response.utr if hasattr(response, 'utr') else None,
                    'acknowledged_at': response.acknowledged_at if hasattr(response, 'acknowledged_at') else None,
                    'transfer_remarks': response.transfer_remarks if hasattr(response, 'transfer_remarks') else None,
                }
            return None
            
        except Exception as e:
            logger.error(f"CashfreeGateway.get_payout_status failed: {e}")
            return None
    
    def create_beneficiary(
        self,
        beneficiary_id: str,
        name: str,
        email: str,
        phone: str,
        bank_account: Optional[Dict] = None,
        upi_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a Cashfree beneficiary (for payouts)."""
        try:
            # Create beneficiary instrument details
            instrument_details = None
            
            if bank_account:
                bank_account_details = BeneficiaryDetailsBeneficiaryInstrumentDetailsBankAccount(
                    bank_account_number=bank_account.get('account_number'),
                    ifsc=bank_account.get('ifsc_code'),
                    account_holder=bank_account.get('account_holder_name', name),
                    bank_name=bank_account.get('bank_name', '')
                )
                instrument_details = BeneficiaryDetailsBeneficiaryInstrumentDetails(
                    bank_account=bank_account_details
                )
            elif upi_id:
                vpa_details = BeneficiaryDetailsBeneficiaryInstrumentDetailsVpa(
                    vpa=upi_id
                )
                instrument_details = BeneficiaryDetailsBeneficiaryInstrumentDetails(
                    vpa=vpa_details
                )
            
            # Create beneficiary details
            beneficiary_details = BeneficiaryDetails(
                beneficiary_id=beneficiary_id,
                beneficiary_name=name,
                beneficiary_email=email,
                beneficiary_phone=phone,
                beneficiary_instrument_details=instrument_details
            )
            
            # Create beneficiary
            response = self.beneficiary_api.create_beneficiary(beneficiary_details)
            
            if response:
                return {
                    'gateway': 'cashfree',
                    'beneficiary_id': beneficiary_id,
                    'status': response.status if hasattr(response, 'status') else 'SUCCESS',
                    'message': response.message if hasattr(response, 'message') else None,
                }
            return None
            
        except Exception as e:
            logger.error(f"CashfreeGateway.create_beneficiary failed: {e}")
            return None