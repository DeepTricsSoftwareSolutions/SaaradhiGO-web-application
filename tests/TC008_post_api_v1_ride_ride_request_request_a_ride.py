import requests
import time
from TC003_get_api_v1_rider_nearby_get_nearby_drivers import request_otp, login

BASE_URL = "http://localhost:8000"
RIDE_REQUEST_ENDPOINT = "/api/v1/ride/ride-request/"

PHONE_NUMBER = "+7396918970"  # Use a valid test phone number known to test environment


def test_post_api_v1_ride_ride_request_request_a_ride():
    # Authenticate rider and get token
    otp = request_otp(PHONE_NUMBER)
    token = login(PHONE_NUMBER, otp)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Prepare valid ride details payload
    ride_payload = {
        "pickup_lat": 12.9716,
        "pickup_long": 77.5946,
        "destination_lat": 12.9352,
        "destination_long": 77.6245,
        "distance_km": 5.0,
        "duration_min": 15.0,
        "vehicle_type": "sedan",
        "payment_method": "card"
    }
    
    try:
        start_time = time.time()
        resp = requests.post(BASE_URL + RIDE_REQUEST_ENDPOINT, json=ride_payload, headers=headers, timeout=65)
        latency = time.time() - start_time
        
        if resp.status_code == 201:
            # Success scenario: Parse response according to PRD
            try:
                j = resp.json()
            except Exception as e:
                raise AssertionError(f"Failed to parse JSON for j. Exception: {e}. Response: {resp.text}")
            assert j.get("status") == "success"
            data = j.get("data", {})
            trip_id = data.get("trip_id")
            assert trip_id is not None, f"Response missing 'trip_id': {j}"
        elif resp.status_code in (504, 503):
            # Error scenario: no drivers found within 60 seconds
            try:
                j = resp.json()
            except Exception as e:
                raise AssertionError(f"Failed to parse JSON for j. Exception: {e}. Response: {resp.text}")
            assert j.get("status") == "error"
            error = j.get("error")
            assert error is not None
            message = error.get("message", "").lower()
            assert "no drivers found" in message or "timeout" in message
        else:
            resp.raise_for_status()
    except requests.Timeout:
        raise AssertionError("The request timed out unexpectedly.")
    except requests.RequestException as e:
        raise AssertionError(f"Request failed: {e}")

test_post_api_v1_ride_ride_request_request_a_ride()
