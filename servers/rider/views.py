import copy
import logging
from rest_framework import status
from base.utils import success_response, error_response
from rest_framework.decorators import api_view, permission_classes
from .serializers import FavoritePlaceSerializer
from rest_framework.permissions import IsAuthenticated
from .models import FavoritePlace
from ..redis_client import nearby_drivers

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_favorite_locations(request):
    """
    Save a favorite location for the user.
    
    Expected request data:
    {
        "address_text": str,
        "latitude": float,
        "longitude": float
    }
    """
    try:
        request.data['latitude']=request.data['latitude'][:12]
        request.data['longitude']=request.data['longitude'][:12]
        instance = FavoritePlaceSerializer(data=request.data)
        if instance.is_valid():
            instance.save(user_id=request.user)
            return success_response(
                {"location": instance.data},
                status.HTTP_201_CREATED
            )
        else:
            logger.warning(f"Validation errors: {instance.errors}")
            return error_response(
                code='VALIDATION_ERROR',
                message='Failed to save favorite location',
                field='location',
                issue=str(instance.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
    except AttributeError as e:
        logger.error(f"Profile error: {str(e)}")
        return error_response(
            code='PROFILE_ERROR',
            message='User profile not found',
            field='user',
            issue='User profile issue',
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Unexpected error saving favorite location: {str(e)}")
        return error_response(
            code='INTERNAL_ERROR',
            message='An unexpected error occurred',
            field='general',
            issue=str(e),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorite_locations(request):
    """
    Retrieve all favorite locations for the authenticated user.
    """
    try:
        query_set = FavoritePlace.objects.filter(user_id=request.user.id)
        data = FavoritePlaceSerializer(query_set, many=True)
        return success_response(data.data, status.HTTP_200_OK)
    except AttributeError as e:
        logger.error(f"Profile error: {str(e)}")
        return error_response(
            code='PROFILE_ERROR',
            message='User profile not found',
            field='user',
            issue='User profile issue',
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching favorite locations: {str(e)}")
        return error_response(
            code='INTERNAL_ERROR',
            message='An unexpected error occurred',
            field='general',
            issue=str(e),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_favorite_location(request, location_id):
    """
    Delete a specific favorite location for the authenticated user.
    
    URL parameters:
    - location_id: ID of the favorite location to delete (int)
    """
    try:
        # Get the favorite location instance
        location = FavoritePlace.objects.get(id=location_id, user_id=request.user)
        
        # Delete the location
        location.delete()
        
        return success_response(
            {"message": "Favorite location deleted successfully"},
            status.HTTP_200_OK
        )
    except FavoritePlace.DoesNotExist:
        logger.warning(f"Favorite location not found for user {request.user.id}: {location_id}")
        return error_response(
            code='NOT_FOUND',
            message='Favorite location not found',
            field='location',
            issue=f'No favorite location found with ID {location_id}',
            status=status.HTTP_404_NOT_FOUND
        )
    except AttributeError as e:
        logger.error(f"Profile error: {str(e)}")
        return error_response(
            code='PROFILE_ERROR',
            message='User profile not found',
            field='user',
            issue='User profile issue',
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting favorite location: {str(e)}")
        return error_response(
            code='INTERNAL_ERROR',
            message='An unexpected error occurred',
            field='general',
            issue=str(e),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nearby_drivers(request):
    """
    Get nearby drivers for the rider.
    
    Query parameters:
    - lng: Longitude (float)
    - lat: Latitude (float)
    - radius: Search radius in meters (int, optional, default: 1000)
    - count: Maximum number of results (int, optional, default: 10)
    """
    try:
        # Get parameters from query_params for GET request
        lng = request.query_params.get('lng')
        lat = request.query_params.get('lat')
        radius = request.query_params.get('radius', 1000)
        count = request.query_params.get('count', 10)
        
        # Validate required fields
        if lng is None or lat is None:
            logger.warning("Missing coordinates in nearby drivers request")
            return error_response(
                code='MISSING_FIELDS',
                message='Longitude and latitude are required',
                field='coordinates',
                issue='lng and lat query parameters must be provided',
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to convert to proper types
        try:
            lng = float(lng)
            lat = float(lat)
            radius = int(radius)
            count = int(count)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid parameter types: {str(e)}")
            return error_response(
                code='INVALID_TYPE',
                message='Invalid parameter types',
                field='coordinates',
                issue='lng and lat must be floats, radius and count must be integers',
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Call Redis function
        drivers = nearby_drivers(lng=lng, lat=lat, radius=radius, count=count)
        
        if drivers is None:
            logger.error("Redis operation failed for nearby drivers")
            return error_response(
                code='REDIS_ERROR',
                message='Failed to retrieve nearby drivers',
                field='general',
                issue='Database query failed',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return success_response(drivers, status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Unexpected error getting nearby drivers: {str(e)}")
        return error_response(
            code='INTERNAL_ERROR',
            message='An unexpected error occurred',
            field='general',
            issue=str(e),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ── Notifications ────────────────────────────────────────
# FCM
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    """
    List notifications for the user.
    """
    from .models import Notification
    from .serializers import NotificationSerializer
    from rest_framework.pagination import PageNumberPagination

    notifs = Notification.objects.filter(user_id=request.user).order_by('-id')
    
    paginator = PageNumberPagination()
    paginator.page_size = 20
    result_page = paginator.paginate_queryset(notifs, request)
    serializer = NotificationSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notif_id):
    """Mark a specific notification as read."""
    from .models import Notification
    
    try:
        notif = Notification.objects.get(id=notif_id, user_id=request.user)
        notif.is_read = True
        notif.save()
        return success_response({'message': 'Marked as read'}, status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return error_response(
            code='NOT_FOUND',
            message='Notification not found',
            field='notif_id',
            issue=f'Notification {notif_id} not found',
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications for the user as read."""
    from .models import Notification
    
    Notification.objects.filter(user_id=request.user, is_read=False).update(is_read=True)
    return success_response({'message': 'All notifications marked as read'}, status.HTTP_200_OK)


# ── Wallet ────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """Get current wallet balance."""
    from .models import Wallet
    
    try:
        wallet = Wallet.objects.get(user_id=request.user)
        return success_response({'balance': str(wallet.balance)}, status.HTTP_200_OK)
    except Wallet.DoesNotExist:
        # Create wallet if not exists
        wallet = Wallet.objects.create(user_id=request.user, balance=0)
        return success_response({'balance': '0.00'}, status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_wallet_order(request):
    """
    Create a Razorpay order for a wallet top-up.
    
    Expected: { "amount": "500.00" }
    """
    from .models import WalletTransaction
    from servers.payments.razorpay_utils import create_razorpay_order
    
    amount = request.data.get('amount')
    if not amount:
        return error_response(
            code='MISSING_FIELDS',
            message='amount is required',
            field='amount',
            issue='Provide the amount to add to wallet',
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        return error_response(
            code='INVALID_AMOUNT',
            message='Invalid amount provided',
            field='amount',
            issue='Amount must be a positive number',
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create Razorpay order
    # Passing currency='INR', receipt='wallet_topup_{user_id}' but receipt limit is 40 chars
    # Wait, create_razorpay_order in razorpay_utils uses:
    # order_data = {'amount': amount_paise, 'currency': currency, 'receipt': f'trip_{trip_id}'}
    # It hardcodes 'trip_id'. So we should modify razorpay_utils.py or override here.
    # We can use the existing razorpay SDK directly here if we don't want to modify razorpay_utils.py.
    # Actually, modifying razorpay_utils.py create_razorpay_order to accept receipt is better.
    # For now, I will use get_razorpay_client from razorpay_utils.
    from servers.payments.razorpay_utils import get_razorpay_client
    client = get_razorpay_client()
    if not client:
        return error_response(
            code='PAYMENT_GATEWAY_ERROR',
            message='Payment gateway not configured',
            field='razorpay',
            issue='Client init failed',
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    try:
        amount_paise = int(amount_val * 100)
        order_data = {
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': f'wallet_{request.user.id}',
            'payment_capture': 1,
        }
        order = client.order.create(data=order_data)
        logger.info(f"Razorpay wallet order created for user {request.user.id}: {order['id']}")
        
        # Create WalletTransaction
        txn = WalletTransaction.objects.create(
            user_id=request.user,
            amount=amount_val,
            txn_type='credit',
            status='pending',
            razorpay_order_id=order['id']
        )
        
        return success_response({
            'transaction_id': txn.id,
            'razorpay_order_id': order['id'],
            'amount': str(amount_val),
            'amount_paise': order['amount'],
            'currency': order['currency'],
            'description': 'Wallet Top-up',
            'prefill': {
                'name': request.user.full_name or '',
                'contact': request.user.phone_number or '',
                'email': request.user.email or '',
            }
        }, status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Failed to create wallet order: {e}")
        return error_response(
            code='PAYMENT_GATEWAY_ERROR',
            message='Failed to create payment order. Please try again.',
            field='razorpay',
            issue=str(e),
            status=status.HTTP_502_BAD_GATEWAY
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_wallet_payment(request):
    """
    Verify a wallet top-up payment.
    
    Expected: {
        "razorpay_order_id": str,
        "razorpay_payment_id": str,
        "razorpay_signature": str
    }
    """
    from .models import WalletTransaction, Wallet
    from servers.payments.razorpay_utils import verify_payment_signature
    from django.db import transaction

    order_id = request.data.get('razorpay_order_id')
    payment_id = request.data.get('razorpay_payment_id')
    signature = request.data.get('razorpay_signature')

    if not all([order_id, payment_id, signature]):
        return error_response(
            code='MISSING_FIELDS',
            message='razorpay_order_id, razorpay_payment_id, and razorpay_signature are required',
            field='request_body',
            issue='Missing signature fields',
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        txn = WalletTransaction.objects.get(
            razorpay_order_id=order_id,
            user_id=request.user
        )
    except WalletTransaction.DoesNotExist:
        return error_response(
            code='NOT_FOUND',
            message='Transaction not found',
            field='razorpay_order_id',
            issue='No transaction matches this order',
            status=status.HTTP_404_NOT_FOUND
        )

    if txn.status == 'completed':
        return success_response({
            'message': 'Payment already verified',
            'transaction_id': txn.id,
            'status': 'completed',
        }, status.HTTP_200_OK)

    # Verify signature
    is_valid = verify_payment_signature(order_id, payment_id, signature)
    if not is_valid:
        txn.status = 'failed'
        txn.razorpay_payment_id = payment_id
        txn.save()
        return error_response(
            code='SIGNATURE_INVALID',
            message='Payment verification failed',
            field='razorpay_signature',
            issue='Signature check failed',
            status=status.HTTP_400_BAD_REQUEST
        )

    # Apply to wallet
    with transaction.atomic():
        txn.status = 'completed'
        txn.razorpay_payment_id = payment_id
        txn.razorpay_signature = signature
        txn.save()

        wallet, _ = Wallet.objects.get_or_create(user_id=request.user)
        wallet.balance = float(wallet.balance) + float(txn.amount) # Add money
        wallet.save()

    logger.info(f"Wallet Top-up verified for user {request.user.id}: added {txn.amount}")
    return success_response({
        'message': 'Payment verified successfully',
        'transaction_id': txn.id,
        'status': 'completed',
        'new_balance': str(wallet.balance)
    }, status.HTTP_200_OK)