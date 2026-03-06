from django.urls import path
from .views import (
    driver_earnings, driver_earnings_summary,
    list_vehicles, create_vehicle, update_vehicle, delete_vehicle, update_driver_profile
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

]