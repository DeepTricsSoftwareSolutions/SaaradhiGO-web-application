import logging
from django.core.exceptions import ValidationError
from base.utils import success_response, error_response
from servers.redis_client import add_driver_location,remove_driver
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import DriverProfileSerializer
from .utils import update_driver_location
from .permissions import IsDriver
from .models import Vehicle
from base.media import EMPTY_FILE_VALUES, resolve_file_input
logger = logging.getLogger(__name__)



# @api_view(['POST'])
# @permission_classes([IsDriver])
# def add_driver(request):
#     """
#     Add or update driver location.
    
#     Expected request data:
#     {
#         "lng": float,
#         "lat": float
#     }
#     """
#     try:
#         driver_id = request.user.driver.id
#         lng = request.data.get('lng')
#         lat = request.data.get('lat')
        
#         # Validate required fields
#         if lng is None or lat is None:
#             logger.warning(f"Missing coordinates for driver {driver_id}")
#             return error_response(
#                 code='MISSING_FIELDS',
#                 message='Longitude and latitude are required',
#                 field='coordinates',
#                 issue='lng and lat must be provided',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Dual-write: geo (spatial index) + stream (event log)
#         result = add_driver_location(driver_id,lat=lat,lng=lng)
#         if result.get('success'):
#             return success_response(
#                 {'message': result.get('message')},
#                 status.HTTP_200_OK
#             )
#         else:
#             logger.error(f"Failed to add driver location: {result.get('error')}")
#             return error_response(
#                 code='LOCATION_ERROR',
#                 message=result.get('error', 'Failed to add location'),
#                 field='coordinates',
#                 issue='Could not save driver location to cache',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
    
#     except AttributeError as e:
#         logger.error(f"Driver profile error: {str(e)}")
#         return error_response(
#             code='PROFILE_ERROR',
#             message='Driver profile not found',
#             field='user',
#             issue='User does not have a driver profile',
#             status=status.HTTP_400_BAD_REQUEST
#         )
#     except Exception as e:
#         logger.error(f"Unexpected error adding driver location: {str(e)}")
#         return error_response(
#             code='INTERNAL_ERROR',
#             message='An unexpected error occurred',
#             field='general',
#             issue=str(e),
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# @api_view(['POST'])
# @permission_classes([IsDriver])
# def update_location(request):
#     """
#     Update driver location.
    
#     Expected request data:
#     {
#         "lng": float,
#         "lat": float
#     }
#     """
#     try:
#         driver_id = request.user.driver.id
#         lng = request.data.get('lng')
#         lat = request.data.get('lat')
        
#         # Validate required fields
#         if lng is None or lat is None:
#             logger.warning(f"Missing coordinates for driver {driver_id}")
#             return error_response(
#                 code='MISSING_FIELDS',
#                 message='Longitude and latitude are required',
#                 field='coordinates',
#                 issue='lng and lat must be provided',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Call Redis function
#         result = update_driver_location(driver_id, lng=lng, lat=lat)
#         return success_response(
#             {'message': 'Driver location updated successfully'},
#             status.HTTP_200_OK
#         )
        
    
#     except AttributeError as e:
#         logger.error(f"Driver profile error: {str(e)}")
#         return error_response(
#             code='PROFILE_ERROR',
#             message='Driver profile not found',
#             field='user',
#             issue='User does not have a driver profile',
#             status=status.HTTP_400_BAD_REQUEST
#         )
#     except Exception as e:
#         logger.error(f"Unexpected error adding driver location: {str(e)}")
#         return error_response(
#             code='INTERNAL_ERROR',
#             message='An unexpected error occurred',
#             field='general',
#             issue=str(e),
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
# @api_view(['DELETE'])
# @permission_classes([IsDriver])
# def remove_driver_view(request):
#     try:
#         driver_id = request.user.driver.id
#         result = remove_driver(driver_id)
#         return success_response(
#             {'message': 'Driver location removed successfully'},
#             status.HTTP_200_OK
#         )
#     except Exception as e:
#         logger.error(f"Unexpected error removing driver location: {str(e)}")
#         return error_response(
#             code='INTERNAL_ERROR',
#             message='An unexpected error occurred',
#             field='general',
#             issue=str(e),
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# ── Driver Earnings ────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDriver])
def driver_earnings(request):
    """
    Paginated list of driver earnings.

    Query params:
        ?page=1         - Page number
        ?page_size=10   - Items per page (max 50)
    """
    from .models import DriverEarning
    from .serializers import DriverEarningSerializer
    from rest_framework.pagination import PageNumberPagination

    driver = request.user.driver
    earnings = DriverEarning.objects.filter(driver_id=driver).select_related('trip_id').order_by('-id')

    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 50
    page = paginator.paginate_queryset(earnings, request)
    serializer = DriverEarningSerializer(page, many=True)
    logger.info(f"Driver earnings: {serializer.data}")
    return success_response(paginator.get_paginated_response(serializer.data).data, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsDriver])
def driver_earnings_summary(request):
    """
    Aggregate earnings for the driver.

    Returns: total_earned, total_commission, total_trips, today_earned, today_trips
    """
    from .models import DriverEarning
    from django.db.models import Sum, Count
    from django.utils import timezone

    driver = request.user.driver
    today = timezone.now().date()

    total = DriverEarning.objects.filter(driver_id=driver).aggregate(
        total_earned=Sum('net_amount'),
        total_commission=Sum('commission'),
        total_trips=Count('id'),
    )

    today_qs = DriverEarning.objects.filter(
        driver_id=driver,
        trip_id__completed_at__date=today,
    ).aggregate(
        today_earned=Sum('net_amount'),
        today_trips=Count('id'),
    )

    from django.conf import settings

    return success_response({
        'total_earned': str(total['total_earned'] or 0),
        'total_commission': str(total['total_commission'] or 0),
        'total_trips': total['total_trips'] or 0,
        'today_earned': str(today_qs['today_earned'] or 0),
        'today_trips': today_qs['today_trips'] or 0,
        'commission_percent': settings.PLATFORM_COMMISSION_PERCENT,
    }, status.HTTP_200_OK)


# ── Vehicle CRUD ────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsDriver])
def list_vehicles(request):
    """List all vehicles belonging to the authenticated driver."""
    from .models import Vehicle
    from .serializers import VehicleSerializer

    driver = request.user.driver
    vehicles = Vehicle.objects.filter(driver_id=driver).select_related('vehicle_type_id')
    serializer = VehicleSerializer(vehicles, many=True)
    return success_response(serializer.data, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsDriver])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_vehicle(request):
    """
    Add a new vehicle for the driver.

    Expected: {
        "vehicle_number": str,
        "vehicle_type": str (e.g. "sedan"),
        "brand": str (optional),
        "model": str (optional),
        "color": str (optional),
        "year": int (optional),
        "capacity": int (optional, default 1)
    }
    """
    from .models import Vehicle, VehicleType
    from .serializers import VehicleCreateSerializer, VehicleSerializer

    serializer = VehicleCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            code='VALIDATION_ERROR',
            message='Invalid vehicle data',
            field=list(serializer.errors.keys())[0],
            issue=str(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )

    data = serializer.validated_data
    driver = request.user.driver
    vt = VehicleType.objects.get(type=data['vehicle_type'])

    try:
        vehicle = Vehicle(
            driver_id=driver,
            vehicle_type_id=vt,
            vehicle_number=data['vehicle_number'],
            brand=data.get('brand', ''),
            model=data.get('model', ''),
            color=data.get('color', ''),
            year=data.get('year'),
            capacity=data.get('capacity', 1),
            rc_doc=data.get('rc_doc'),
            vehicle_pic=data.get('vehicle_pic'),
        )
        vehicle.full_clean()
        vehicle.save()
    except ValidationError as e:
        return error_response(
            code='VALIDATION_ERROR',
            message='Invalid vehicle data',
            field='vehicle',
            issue=str(e.message_dict if hasattr(e, 'message_dict') else e.messages),
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code='CREATE_ERROR',
            message='Failed to create vehicle',
            field='vehicle',
            issue=str(e),
            status=status.HTTP_400_BAD_REQUEST
        )

    return success_response(
        VehicleSerializer(vehicle).data,
        status.HTTP_201_CREATED
    )


@api_view(['PATCH'])
@permission_classes([IsDriver])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_vehicle(request, vehicle_id):
    """Update a vehicle belonging to the driver."""
    from .models import Vehicle
    from .serializers import VehicleSerializer

    driver = request.user.driver
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id, driver_id=driver)
    except Vehicle.DoesNotExist:
        return error_response(
            code='NOT_FOUND',
            message='Vehicle not found',
            field='vehicle_id',
            issue=f'Vehicle {vehicle_id} not found or does not belong to you',
            status=status.HTTP_404_NOT_FOUND
        )

    for field_name in ('rc_doc', 'vehicle_pic'):
        field_provided, field_value, field_error = resolve_file_input(request, field_name)
        if field_error:
            return error_response(
                code='UPLOAD_FAILED',
                message=field_error,
                field=field_name,
                issue=field_error,
                status=status.HTTP_400_BAD_REQUEST
            )
        if field_provided:
            setattr(vehicle, field_name, field_value)

    allowed_fields = ['brand', 'model', 'color', 'year', 'capacity', 'vehicle_number']
    for field in allowed_fields:
        if field in request.data:
            setattr(vehicle, field, request.data[field])

    try:
        vehicle.full_clean()
        vehicle.save()
    except ValidationError as e:
        return error_response(
            code='VALIDATION_ERROR',
            message='Invalid vehicle data',
            field='vehicle',
            issue=str(e.message_dict if hasattr(e, 'message_dict') else e.messages),
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code='UPDATE_ERROR',
            message='Failed to update vehicle',
            field='vehicle',
            issue=str(e),
            status=status.HTTP_400_BAD_REQUEST
        )

    return success_response(VehicleSerializer(vehicle).data, status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsDriver])
def delete_vehicle(request, vehicle_id):
    """Delete a vehicle belonging to the driver."""
    from .models import Vehicle

    driver = request.user.driver
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id, driver_id=driver)
    except Vehicle.DoesNotExist:
        return error_response(
            code='NOT_FOUND',
            message='Vehicle not found',
            field='vehicle_id',
            issue=f'Vehicle {vehicle_id} not found or does not belong to you',
            status=status.HTTP_404_NOT_FOUND
        )

    vehicle.delete()
    return success_response({'message': 'Vehicle deleted successfully'}, status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsDriver])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_driver_profile(request):
    """Update a driver profile.
    sample request: {
        "active_vehicle": int
    }

    """
    driver = request.user.driver
    update_data = {}

    license_provided, license_value, license_error = resolve_file_input(request, 'license_doc')
    if license_error:
        return error_response(
            code='UPLOAD_FAILED',
            message=license_error,
            field='license_doc',
            issue=license_error,
            status=status.HTTP_400_BAD_REQUEST
        )
    if license_provided:
        update_data['license_doc'] = license_value

    if 'license_expiry' in request.data:
        license_expiry = request.data.get('license_expiry')
        update_data['license_expiry'] = None if license_expiry in EMPTY_FILE_VALUES else license_expiry

    if 'active_vehicle' in request.data:
        vehicle_id = request.data.get('active_vehicle')
        if vehicle_id in EMPTY_FILE_VALUES or vehicle_id is None:
            update_data['active_vehicle'] = None
        else:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, driver_id=driver)
                update_data['active_vehicle'] = vehicle.id
            except Vehicle.DoesNotExist:
                return error_response(
                    code='NOT_FOUND',
                    message='Vehicle not found',
                    field='active_vehicle',
                    issue=f'Vehicle {vehicle_id} not found or does not belong to you',
                    status=status.HTTP_404_NOT_FOUND
                )

    if not update_data:
        return error_response(
            code='VALIDATION_ERROR',
            message='No driver profile data provided',
            field='data',
            issue='Provide at least one of active_vehicle, license_doc, or license_expiry',
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = DriverProfileSerializer(driver, data=update_data, partial=True)
    if not serializer.is_valid():
        return error_response(
            code='VALIDATION_ERROR',
            message='Invalid driver profile data',
            field=list(serializer.errors.keys())[0],
            issue=str(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer.save()
    return success_response(serializer.data, status.HTTP_200_OK)
