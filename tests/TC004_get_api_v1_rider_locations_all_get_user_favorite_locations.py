import requests
import time
from TC003_get_api_v1_rider_nearby_get_nearby_drivers import request_otp, login
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

TEST_PHONE_NUMBER = "+917396918971"  # Replace with a valid test rider phone number


def test_get_rider_locations_all():
    # Step 1: Authenticate user and get token
    otp = request_otp(TEST_PHONE_NUMBER)
    token = login(TEST_PHONE_NUMBER, otp)

    # Step 2: Call GET /api/v1/rider/locations/all/ with Authorization header
    url = f"{BASE_URL}/api/v1/rider/locations/all/"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise RuntimeError(f"Request to get rider locations failed: {e}")

    # Validate status code 200 OK
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}. Response: {resp.text}"

    # Validate response JSON structure and content
    try:
        try:
            j = resp.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for j. Exception: {e}. Response: {resp.text}")
    except Exception as e:
        raise AssertionError(f"Response is not valid JSON: {e}")

    assert j.get("status") == "success", f"Expected status 'success', got {j.get('status')}"
    assert "data" in j, "Response JSON missing 'data' field"

    locations = j["data"]
    # The data is expected to be an array (likely list) of favorite locations
    assert isinstance(locations, list), f"Expected data to be a list, got {type(locations)}"

    # Optional: each location should be a dict (based on domain knowledge)
    for loc in locations:
        assert isinstance(loc, dict), "Each location should be an object/dict"

    # Also test unauthorized access returns 401 Unauthorized (no token)
    try:
        resp_unauth = requests.get(url, timeout=TIMEOUT)
        assert resp_unauth.status_code == 401, f"Expected 401 Unauthorized without auth. Response: {resp_unauth.text}"
    except requests.RequestException:
        # If request fails, that's still a failure for the test
        raise RuntimeError("Failed requesting without auth to validate 401 Unauthorized")

    # Also test with invalid token returns 401 Unauthorized
    invalid_headers = {"Authorization": "Bearer invalidtoken123"}
    try:
        resp_invalid = requests.get(url, headers=invalid_headers, timeout=TIMEOUT)
        assert resp_invalid.status_code == 401, f"Expected 401 Unauthorized with invalid token. Response: {resp_invalid.text}"
    except requests.RequestException:
        raise RuntimeError("Failed requesting with invalid token to validate 401 Unauthorized")

test_get_rider_locations_all()