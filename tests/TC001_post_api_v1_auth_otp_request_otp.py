import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_post_api_v1_auth_otp_request_otp():
    url = f"{BASE_URL}/api/v1/auth/otp/"
    headers = {
        "Content-Type": "application/json"
    }
    # Use a valid E.164 phone number format
    payload = {
        "phone_number": "+917396918971"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status 200 but got {response.status_code}. Response: {response.text}"
        try:
            json_resp = response.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {response.text}")
        assert "status" in json_resp, "Response missing 'status'"
        assert json_resp["status"] == "success", f"Expected status 'success' but got {json_resp.get('status')}"
        assert "data" in json_resp, "Response missing 'data'"
        data = json_resp["data"]
        assert "message" in data, "Response data missing 'message'"
        assert data["message"] == "OTP sent successfully", f"Unexpected message: {data['message']}"
        assert "otp" in data, "Response data missing 'otp'"
        assert isinstance(data["otp"], str) and data["otp"].isdigit() and len(data["otp"]) > 0, "Invalid OTP format"
        assert "expires_in" in data, "Response data missing 'expires_in'"
        assert isinstance(data["expires_in"], int) and data["expires_in"] > 0, "Invalid expires_in value"
        return data["otp"]
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
        return None
