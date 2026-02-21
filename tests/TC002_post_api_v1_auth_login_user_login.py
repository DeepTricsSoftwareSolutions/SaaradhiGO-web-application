import requests
import time
from TC001_post_api_v1_auth_otp_request_otp import test_post_api_v1_auth_otp_request_otp
BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS_JSON = {"Content-Type": "application/json"}

def post_api_v1_auth_login_user_login():
    phone_number = "+917396918971"  # Use a valid test phone number here

    # Step 1: Request OTP
    otp_code = test_post_api_v1_auth_otp_request_otp()
    # Step 2: Login with valid OTP
    login_url = f"{BASE_URL}/api/v1/auth/login/"
    login_payload_valid = {"phone_number": phone_number, "otp": otp_code}
    login_resp_valid = requests.post(login_url, json=login_payload_valid, headers=HEADERS_JSON, timeout=TIMEOUT)
    try:
        assert login_resp_valid.status_code == 200, f"Expected 200 OK from login with valid OTP, got {login_resp_valid.status_code}. Response: {login_resp_valid.text}"
        try:
            login_json = login_resp_valid.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for login_json. Exception: {e}. Response: {login_resp_valid.text}")
        assert login_json.get("status") == "success", f"Expected status=success in login response, got {login_json.get('status')}"
        data = login_json.get("data")
        assert data is not None, "No data object in login response"
        token = data.get("token")
        user = data.get("user")
        assert isinstance(token, str) and token, "Token missing or empty in login response"
        assert isinstance(user, dict), "User object missing or invalid in login response"
        # Optionally check presence of user role
        assert "role" in user, "User role missing in user object"
    except Exception as e:
        raise AssertionError(f"Login with valid OTP failed or response invalid: {e}")

    # Step 3: Login with invalid OTP
    invalid_otp = "000000"
    if invalid_otp == otp_code:
        # just in case generated otp is 000000, change invalid otp
        invalid_otp = "111111"
    login_payload_invalid = {"phone_number": phone_number, "otp": invalid_otp}
    login_resp_invalid = requests.post(login_url, json=login_payload_invalid, headers=HEADERS_JSON, timeout=TIMEOUT)
    try:
        assert login_resp_invalid.status_code == 400, f"Expected 400 Bad Request from login with invalid OTP, got {login_resp_invalid.status_code}. Response: {login_resp_invalid.text}"
        try:
            err_json = login_resp_invalid.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for err_json. Exception: {e}. Response: {login_resp_invalid.text}")
        assert err_json.get("status") == "error", f"Expected status=error for invalid OTP login, got {err_json.get('status')}"
        error_obj = err_json.get("error")
        assert error_obj is not None, "Error object missing in invalid OTP login response"
        assert "message" in error_obj and error_obj["message"], "Error message missing in invalid OTP login response"
    except Exception as e:
        raise AssertionError(f"Login with invalid OTP did not fail as expected or response invalid: {e}")
    return token
post_api_v1_auth_login_user_login()