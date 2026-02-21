import requests
import time
from TC003_get_api_v1_rider_nearby_get_nearby_drivers import request_otp, login
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def create_ride_request(token):
    url = f"{BASE_URL}/api/v1/ride/ride-request/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "pickup_lat": 28.6139,
        "pickup_long": 77.209,
        "destination_lat": 28.7041,
        "destination_long": 77.1025,
        "distance_km": 5.0,
        "duration_min": 15.0,
        "vehicle_type": "sedan"
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    assert resp.status_code == 201, f"Expected resp.status_code == 201 but got {resp.status_code}. Response: {resp.text}"
    try:
        json_resp = resp.json()
    except Exception as e:
        raise AssertionError(f"Failed to parse JSON for json_resp. Exception: {e}. Response: {resp.text}")
    assert json_resp.get("status") == "success"
    trip_id = json_resp.get("data", {}).get("trip_id")
    assert trip_id is not None, "trip_id missing"
    return trip_id

def manually_complete_trip(trip_id):
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(__file__), "..", "db.sqlite3")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ride_tripstatus WHERE status_code = 'completed' LIMIT 1")
        status_row = cursor.fetchone()
        if status_row:
            status_id = status_row[0]
            cursor.execute("UPDATE ride_trip SET status_id_id = ? WHERE id = ?", (status_id, trip_id))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to update trip {trip_id} in sqlite3: {e}")

def test_post_api_v1_payments_create_order_create_payment_order():
    # Setup: authenticate with OTP and login to get token
    rider_phone = "+7396918970"
    otp = request_otp(rider_phone)
    token = login(rider_phone, otp)
    headers = {"Authorization": f"Bearer {token}"}

    # Create ride request to get a valid trip_id
    trip_id = None
    try:
        trip_id = create_ride_request(token)
        manually_complete_trip(trip_id)

        # 1. Valid payment order creation
        url_create_order = f"{BASE_URL}/api/v1/payments/create-order/"
        payload_valid = {
            "trip_id": trip_id
        }
        response_valid = requests.post(url_create_order, json=payload_valid, headers=headers, timeout=TIMEOUT)
        assert response_valid.status_code in [201, 502], f"Expected 201 Created or 502 Bad Gateway (if Razorpay env missing) but got {response_valid.status_code}. Response: {response_valid.text}"
        
        try:
            json_valid = response_valid.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON. Exception: {e}. Response: {response_valid.text}")
        
        if response_valid.status_code == 201:
            assert json_valid.get("status") == "success"
            data = json_valid.get("data", {})
            assert data.get("razorpay_order_id"), "Missing razorpay_order_id in 201 response"
        elif response_valid.status_code == 502:
            assert json_valid.get("status") == "error"
            error_data = json_valid.get("error", {})
            assert error_data.get("code") == "PAYMENT_GATEWAY_ERROR"

        # 2. Invalid Trip ID returns 404 Not Found
        payload_unsupported = {
            "trip_id": 999999
        }
        response_unsup = requests.post(url_create_order, json=payload_unsupported, headers=headers, timeout=TIMEOUT)
        assert response_unsup.status_code == 404, f"Expected response.status_code == 404 but got {response_unsup.status_code}. Response: {response_unsup.text}"
        try:
            json_unsup = response_unsup.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON. Exception: {e}. Response: {response_unsup.text}")
        error_message = json_unsup.get("error", {})
        if isinstance(error_message, dict):
            error_message = error_message.get("message", "")
        assert "not found" in error_message.lower()

        # 3. Missing Authorization header returns 401 Unauthorized
        payload_no_auth = {
            "trip_id": trip_id
        }
        response_no_auth = requests.post(url_create_order, json=payload_no_auth, timeout=TIMEOUT)
        assert response_no_auth.status_code == 401, f"Expected response_no_auth.status_code == 401 but got {response_no_auth.status_code}. Response: {response_no_auth.text}"
        try:
            json_no_auth = response_no_auth.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON for json_no_auth. Exception: {e}. Response: {response_no_auth.text}")
        error_message_no_auth = json_no_auth.get("detail") or ""
        assert any(keyword in error_message_no_auth.lower() for keyword in ["unauthorized", "authentication"])

    finally:
        pass

test_post_api_v1_payments_create_order_create_payment_order()
