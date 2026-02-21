import requests
import time
from TC003_get_api_v1_rider_nearby_get_nearby_drivers import request_otp, login

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

DRIVER_PHONE = "+917893378551"  # Substitute with a valid driver phone number in E.164 format




def test_get_driver_earnings():
    # Step 1: Obtain OTP for valid driver phone
    otp = request_otp(DRIVER_PHONE)
    token = login(DRIVER_PHONE, otp)
    assert token is not None, f"Login failed or invalid OTP: {token}"

    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: GET /api/v1/driver/earnings/ with valid token and required range parameter
    try:
        url = f"{BASE_URL}/api/v1/driver/earnings/"
        # Test with range=daily parameter
        params = {"range": "daily"}
        resp_range = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        # print(resp_range.json())
        assert resp_range.status_code == 200, f"Expected 200 OK with range param, got {resp_range.status_code}. Response: {resp_range.text}"
        try:
            j_range = resp_range.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for j_range. Exception: {e}. Response: {resp_range.text}")
        # print(j_range)
        assert j_range.get("status") == "success", f"Response status not success: {j_range}"
        data_range = j_range.get("data")
        assert isinstance(data_range, dict), "Response data expected to be a dict"
        # Validate earnings summary keys presence
        expected_keys = {"count", "next", "previous", "results"}
        assert expected_keys.issubset(data_range.keys()), f"Missing keys in earnings data: {data_range.keys()}"

        # Step 4: GET /api/v1/driver/earnings/ with invalid token returns 401 Unauthorized
        invalid_headers = {"Authorization": "Bearer invalid.token.value"}
        resp_invalid = requests.get(url, headers=invalid_headers, params=params, timeout=TIMEOUT)
        assert resp_invalid.status_code == 401, f"Expected 401 Unauthorized with invalid token, got {resp_invalid.status_code}. Response: {resp_invalid.text}"

        # Step 5: GET /api/v1/driver/earnings/ with expired token simulation:
        # For simulation purpose we can try a likely expired token (unlikely possible here),
        # So to cover edge, try without Authorization header as well which should also be 401
        resp_no_auth = requests.get(url, params=params, timeout=TIMEOUT)
        assert resp_no_auth.status_code == 401, f"Expected 401 Unauthorized without token, got {resp_no_auth.status_code}. Response: {resp_no_auth.text}"

    except AssertionError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error during driver earnings test: {e}")


test_get_driver_earnings()
