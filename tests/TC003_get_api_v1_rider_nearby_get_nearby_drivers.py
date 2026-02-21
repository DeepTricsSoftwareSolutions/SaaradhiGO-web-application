import requests
import time

BASE_URL = "http://localhost:8000"
OTP_ENDPOINT = "/api/v1/auth/otp/"
LOGIN_ENDPOINT = "/api/v1/auth/login/"
NEARBY_DRIVERS_ENDPOINT = "/api/v1/rider/nearby/"

TEST_PHONE_NUMBER = "+917396918971"  # Replace with a valid test rider phone number
TIMEOUT = 30

def request_otp(phone_number):
    url = BASE_URL + OTP_ENDPOINT
    payload = {"phone_number": phone_number}
    otp=None
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        # resp.raise_for_status()
        try:
            json_resp = resp.json()
            otp=json_resp['data']['otp']
            print(otp)
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {resp.text}")
        # OTP request returns 200 OK with OTP_SENT confirmation (message in text or status), no otp in response
        # Check some confirmation message or status in response
        confirmation = json_resp.get("data").get("message",'')
        assert "OTP sent" in confirmation, f"Unexpected OTP response: {json_resp}"
        # Cannot get OTP from response, so return None or raise error to indicate manual/alternative OTP
        return otp
    except Exception as e:
        raise RuntimeError(f"OTP request failed: {e}")


def login(phone_number, otp):
    url = BASE_URL + LOGIN_ENDPOINT
    payload = {"phone_number": phone_number, "otp": otp}
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        # resp.raise_for_status()
        # print(resp.status_code)
        try:
            json_resp = resp.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {resp.text}")
        # Login returns 200 OK with JWT/access token and user role
        # No 'status' or 'data' wrapper specified, so check for 'token' and 'role' directly
        token = json_resp.get("data").get("token") or json_resp.get("data").get("access_token")
        user_role = json_resp.get("data").get("user").get("role")
        assert token and isinstance(token, str) and len(token) > 0, f"Invalid or missing token in login response: {json_resp}"
        assert user_role and isinstance(user_role, str), f"Invalid or missing role in login response: {json_resp}"
        return token
    except requests.exceptions.HTTPError as http_err:
        if resp.status_code == 400:
            try:
                json_resp = resp.json()
            except Exception as e:
                raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {resp.text}")
            error_message = json_resp.get("error") or json_resp.get("detail") or ""
            assert "invalid otp" in error_message.lower(), f"Expected invalid OTP error, got: {json_resp}"
            raise AssertionError(f"Login failed due to invalid OTP: {error_message}")
        else:
            raise RuntimeError(f"Login failed: {http_err}")
    except Exception as e:
        raise RuntimeError(f"Login failed: {e}")


def test_get_nearby_drivers():
    # Step 1: Authenticate rider and get token
    otp = request_otp(TEST_PHONE_NUMBER)
    print(otp)
    try:
        token = login(TEST_PHONE_NUMBER, otp)
    except AssertionError as e:
        raise AssertionError(f"Cannot login with provided OTP: {e}")

    # Step 2: Make GET request to nearby drivers endpoint with valid lat/lng and Authorization header
    headers = {"Authorization": f"Bearer {token}"}
    params = {"lat": "12.9715987", "lng": "77.5945627"}  # Coordinates for Bangalore, India

    try:
        resp = requests.get(BASE_URL + NEARBY_DRIVERS_ENDPOINT, headers=headers, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        try:
            json_resp = resp.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {resp.text}")
        # Response format for success assumed to be list of drivers
        # Validate returned data is a list
        data = json_resp
        if isinstance(json_resp, dict) and "data" in json_resp:
            data = json_resp["data"]
        assert isinstance(data, list), f"Expected data to be list, got: {type(data)}"
        # Each item should be [member, distance, [lng, lat]]
        for driver in data:
            assert isinstance(driver, list), f"Expected driver to be a list, got: {type(driver)}"
            assert len(driver) == 3, f"Expected 3 elements [member, distance, coords], got: {len(driver)}"
            assert isinstance(driver[0], str) and "driver:" in driver[0], f"Invalid or missing id in driver: {driver}"
            assert isinstance(driver[1], (int, float)), f"Invalid or missing distance in driver: {driver}"
            assert isinstance(driver[2], list) and len(driver[2]) == 2, f"Invalid or missing coordinates in driver: {driver}"
    except requests.HTTPError as e:
        raise AssertionError(f"HTTP error during get nearby drivers: {e}")
    except Exception as e:
        raise AssertionError(f"Error during get nearby drivers: {e}")

    # Step 3: Negative Tests
    # 3a: Without Authorization header -> 401 Unauthorized
    try:
        resp_no_auth = requests.get(BASE_URL + NEARBY_DRIVERS_ENDPOINT, params=params, timeout=TIMEOUT)
        assert resp_no_auth.status_code == 401, f"Expected 401 Unauthorized without auth header, got {resp_no_auth.status_code}. Response: {resp_no_auth.text}"
        try:
            json_resp = resp_no_auth.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {resp_no_auth.text}")
        # Check response indicates error
        if isinstance(json_resp, dict):
            assert "error" in json_resp or "detail" in json_resp, f"Unexpected error response without auth: {json_resp}"
    except Exception as e:
        raise AssertionError(f"Error testing unauthorized access: {e}")

    # 3b: With invalid lat/lng and valid Authorization -> 400 Bad Request or 422 Unprocessable Entity
    invalid_params = {"lat": "invalid_lat", "lng": "invalid_lng"}
    try:
        resp_invalid_coords = requests.get(BASE_URL + NEARBY_DRIVERS_ENDPOINT, headers=headers, params=invalid_params, timeout=TIMEOUT)
        assert resp_invalid_coords.status_code in (400, 422), \
            f"Expected 400 or 422 for invalid coords, got {resp_invalid_coords.status_code}"
        try:
            json_resp = resp_invalid_coords.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {resp_invalid_coords.text}")
        if isinstance(json_resp, dict):
            assert "error" in json_resp or "detail" in json_resp, f"Unexpected error response for invalid coords: {json_resp}"
    except Exception as e:
        raise AssertionError(f"Error testing invalid coordinates: {e}")


test_get_nearby_drivers()
