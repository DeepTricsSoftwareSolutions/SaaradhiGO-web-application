import redis
import logging
from django.conf import settings
from base.utils import success_response, error_response
from rest_framework import status

logger = logging.getLogger(__name__)

# Initialize Redis client with connection pool and error handling
redis_client = None
try:
    if getattr(settings, 'TESTING', False):
        redis_client = None
    else:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL + '/3',
            decode_responses=True,
            socket_connect_timeout=2,
            socket_keepalive=True,
            socket_keepalive_options={} if hasattr(redis, 'SOCKET_KEEPALIVE_OPTIONS') else None
        )
        # Test the connection
        redis_client.ping()
        logger.info("Stream connection established successfully")
except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    redis_client = None

def update_driver_location(driver_id, lng, lat):
    if redis_client is None:
        return error_response(
            code="REDIS_CONNECTION_ERROR",
            message="Failed to connect to Redis",
            field="redis",
            issue="Redis connection error",
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    redis_client.xadd('driver_location_stream', {'driver_id': driver_id, 'lng': lng, 'lat': lat}, maxlen=100000)

    return success_response(
        data={
            'message': "Driver location updated successfully",
            'driver_id': driver_id,
            'lng': lng,
            'lat': lat
        },
        status_code=status.HTTP_200_OK
    )

def create_driver_earning(trip):
    """Calculate and create DriverEarning record."""
    from servers.driver.models import DriverEarning
    from django.conf import settings
    from decimal import Decimal

    if not trip.driver_id:
        return

    # Skip if already exists
    if DriverEarning.objects.filter(trip_id=trip).exists():
        return

    amount = trip.final_fare or trip.estimated_fare or Decimal('0.00')
    commission_rate = getattr(settings, 'PLATFORM_COMMISSION_PERCENT', 20)
    
    commission = (amount * Decimal(commission_rate)) / Decimal(100)
    net_amount = amount - commission

    DriverEarning.objects.create(
        driver_id=trip.driver_id,
        trip_id=trip,
        commission=commission,
        net_amount=net_amount,
    )