import requests
import time
from datetime import datetime, timezone
from TC003_get_api_v1_rider_nearby_get_nearby_drivers import request_otp, login

BASE_URL = "http://localhost:8000"
OTP_ENDPOINT = "/api/v1/auth/otp/"
LOGIN_ENDPOINT = "/api/v1/auth/login/"
UPDATE_LOCATION_ENDPOINT = "/api/v1/driver/update_location/"

PHONE_NUMBER = "+917893378551"
TIMEOUT = 30



def test_post_api_v1_driver_update_location_update_driver_location():
    # Authenticate driver user and obtain JWT token
    otp = request_otp(PHONE_NUMBER)
    token = login(PHONE_NUMBER, otp)
    headers = {"Authorization": f"Bearer {token}"}

    # Test valid location update
    url = BASE_URL + UPDATE_LOCATION_ENDPOINT
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    valid_payload = {
        "lat": 12.9715987,
        "lng": 77.594566,
        "timestamp": timestamp_iso,
    }
    response = requests.post(url, json=valid_payload, headers=headers, timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected response.status_code == 200 but got {response.status_code}. Response: {response.text}"
    try:
        resp_json = response.json()
    except Exception as e:
        raise AssertionError(f"Failed to parse JSON for resp_json. Exception: {e}. Response: {response.text}")
    # We expect some success acknowledgement
    assert isinstance(resp_json, dict)

    # Test missing lat returns 400 Bad Request
    payload_missing_lat = {
        # "lat": 12.9715987,
        "lng": 77.594566,
        "timestamp": timestamp_iso,
    }
    response_missing_lat = requests.post(url, json=payload_missing_lat, headers=headers, timeout=TIMEOUT)
    assert response_missing_lat.status_code == 400, f"Expected response_missing_lat.status_code == 400 but got {response_missing_lat.status_code}. Response: {response_missing_lat.text}"
    try:
        resp_json_missing_lat = response_missing_lat.json()
    except Exception as e:
        raise AssertionError(f"Failed to parse JSON for resp_json_missing_lat. Exception: {e}. Response: {response_missing_lat.text}")
    # Error check may vary but must contain indication of missing lat
    err_msg = resp_json_missing_lat.get("error", {}).get("message", "") if isinstance(resp_json_missing_lat.get("error", {}), dict) else str(resp_json_missing_lat.get("error", ""))
    assert "lat" in err_msg.lower() or "lat" in str(resp_json_missing_lat).lower()

    # Test missing lng returns 400 Bad Request
    payload_missing_lng = {
        "lat": 12.9715987,
        # "lng": 77.594566,
        "timestamp": timestamp_iso,
    }
    response_missing_lng = requests.post(url, json=payload_missing_lng, headers=headers, timeout=TIMEOUT)
    assert response_missing_lng.status_code == 400, f"Expected response_missing_lng.status_code == 400 but got {response_missing_lng.status_code}. Response: {response_missing_lng.text}"
    try:
        resp_json_missing_lng = response_missing_lng.json()
    except Exception as e:
        raise AssertionError(f"Failed to parse JSON for resp_json_missing_lng. Exception: {e}. Response: {response_missing_lng.text}")
    err_msg = resp_json_missing_lng.get("error", {}).get("message", "") if isinstance(resp_json_missing_lng.get("error", {}), dict) else str(resp_json_missing_lng.get("error", ""))
    assert "lng" in err_msg.lower() or "lng" in str(resp_json_missing_lng).lower()


test_post_api_v1_driver_update_location_update_driver_location()
