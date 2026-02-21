import requests
import time
from TC003_get_api_v1_rider_nearby_get_nearby_drivers import request_otp, login

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

TEST_PHONE_NUMBER = "+917893378551"  # Replace with a valid test phone number
VEHICLE_TYPE = "sedan"  # Assuming "sedan" is a valid vehicle type


def test_post_api_v1_ride_estimate_fare():
    # Authenticate: get OTP and login to obtain token
    otp = request_otp(TEST_PHONE_NUMBER)
    token = login(TEST_PHONE_NUMBER, otp)
    headers = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/ride/estimate-fare/"
    valid_payload = {
        "pickup_lat": 12.9716,
        "pickup_long": 77.5946,
        "destination_lat": 12.9352,
        "destination_long": 77.6245,
        "distance_km": 5.0,
        "duration_min": 15.0,
        "vehicle_type": VEHICLE_TYPE
    }
    # Test valid request
    try:
        response = requests.post(url, json=valid_payload, headers=headers, timeout=TIMEOUT)
    except Exception as e:
        raise Exception(f"Error in valid fare estimate request: {e}")
    assert response.status_code == 200, f"Expected response.status_code == 200 but got {response.status_code}. Response: {response.text}"
    try:
        resp_json = response.json()
    except Exception as e:
        raise AssertionError(f"Failed to parse JSON for resp_json. Exception: {e}. Response: {response.text}")
    assert resp_json.get("status") == "success"
    data = resp_json.get("data")
    # print(data)
    assert data is not None
    # fare_estimate expected keys: min, max, estimated_time
    for key in ("estimated_fare","duration_min","distance_km"):
        assert key in data
        val = data[key]
        assert (isinstance(val, (int, float,str))), f"Invalid {key} value: {val}"

    # Test malformed payloads - missing fields or bad coordinates
    malformed_payloads = [
        {},  # empty
        {"pickup_lat": 12.9716, "pickup_long": 77.5946},
        {"pickup_lat": "not_a_float", "pickup_long": 77.5946, "destination_lat": 12.9352, "destination_long": 77.6245, "distance_km": 5.0, "duration_min": 15, "vehicle_type": VEHICLE_TYPE},
        {"pickup_lat": 12.9716, "pickup_long": 77.5946, "destination_lat": 12.9352, "destination_long": None, "distance_km": 5.0, "duration_min": 15, "vehicle_type": VEHICLE_TYPE},
    ]
    for payload in malformed_payloads:
        try:
            resp_err = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        except Exception as e:
            raise Exception(f"Error in malformed payload request: {e}")
        assert resp_err.status_code == 400, f"Expected 400 for payload {payload} but got {resp_err.status_code}. Response: {resp_err.text}"
        try:
            err_json = resp_err.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for err_json. Exception: {e}. Response: {resp_err.text}")
        assert err_json.get("status") == "error"
        error = err_json.get("error")
        assert error is not None and "code" in error and "message" in error

test_post_api_v1_ride_estimate_fare()
