from django.urls import path
from .views import (
    driver_earnings, driver_earnings_summary,
    list_vehicles, create_vehicle, update_vehicle, delete_vehicle, update_driver_profile
)
from .admin_views import (
    list_drivers_admin, retrieve_driver_admin, update_kyc_status_admin, delete_driver_admin
)

urlpatterns = [
    # path('add/', add_driver),
    # path('update_location/', update_location),
    # path('remove_driver/', remove_driver_view),
    # Driver
    path('driver/',update_driver_profile),
    # Earnings
    path('earnings/', driver_earnings),
    path('earnings/summary/', driver_earnings_summary),
    # Vehicles
    path('vehicles/', list_vehicles),
    path('vehicles/add/', create_vehicle),
    path('vehicles/<int:vehicle_id>/', update_vehicle),
    path('vehicles/<int:vehicle_id>/delete/', delete_vehicle),

    # Admin URLs
    path('admin/', list_drivers_admin),
    path('admin/<int:driver_id>/', retrieve_driver_admin),
    path('admin/<int:driver_id>/update-kyc/', update_kyc_status_admin),
    path('admin/<int:driver_id>/delete/', delete_driver_admin),
]