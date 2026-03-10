import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from base.utils import success_response, error_response
from servers.auth_user.permissions import IsAdmin
from servers.driver.models import Driver
from servers.driver.serializers import DriverAdminListSerializer, DriverAdminDetailSerializer, KYCApprovalSerializer
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def list_drivers_admin(request):
    """
    List all drivers. Can be filtered by 'approved' and 'status'.
    """
    drivers = Driver.objects.all().select_related('user_id').order_by('-id')
    
    # Filter configuration
    approved = request.query_params.get('approved')
    driver_status = request.query_params.get('status')
    
    if approved is not None:
        approved_bool = approved.lower() in ['true', '1', 't', 'y', 'yes']
        drivers = drivers.filter(approved=approved_bool)
        
    if driver_status:
        drivers = drivers.filter(status=driver_status)

    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 50
    page = paginator.paginate_queryset(drivers, request)
    
    serializer = DriverAdminListSerializer(page, many=True)
    return success_response(paginator.get_paginated_response(serializer.data).data, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def retrieve_driver_admin(request, driver_id):
    """
    Retrieve details of a single driver by its ID (along with user profile and vehicles).
    """
    try:
        driver = Driver.objects.prefetch_related('user_id', 'vehicle_set').get(id=driver_id)
        serializer = DriverAdminDetailSerializer(driver)
        return success_response(serializer.data, status.HTTP_200_OK)
    except Driver.DoesNotExist:
        return error_response(
            code="NOT_FOUND",
            message="Driver not found",
            field="driver_id",
            issue=f"No driver matches id {driver_id}",
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
def update_kyc_status_admin(request, driver_id):
    """
    Approve or reject KYC for a driver (updates 'approved' and/or 'status').
    """
    try:
        driver = Driver.objects.get(id=driver_id)
        
        serializer = KYCApprovalSerializer(driver, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, status.HTTP_200_OK)
            
        return error_response(
            code="VALIDATION_ERROR",
            message="Invalid update data",
            field=list(serializer.errors.keys())[0],
            issue=str(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )
    except Driver.DoesNotExist:
        return error_response(
            code="NOT_FOUND",
            message="Driver not found",
            field="driver_id",
            issue=f"No driver matches id {driver_id}",
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def delete_driver_admin(request, driver_id):
    """
    Delete a driver profile and their associated objects.
    """
    try:
        driver = Driver.objects.get(id=driver_id)
        driver.delete()
        return success_response({"message": "Driver deleted successfully"}, status.HTTP_200_OK)
    except Driver.DoesNotExist:
        return error_response(
            code="NOT_FOUND",
            message="Driver not found",
            field="driver_id",
            issue=f"No driver matches id {driver_id}",
            status=status.HTTP_404_NOT_FOUND
        )
