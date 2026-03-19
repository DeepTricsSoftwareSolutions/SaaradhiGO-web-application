# VahanGo API Documentation

## 1. Overview
The VahanGo API provides backend services for a ride-hailing platform, facilitating functionalities for Riders, Drivers, Ride Matching, and Payment processing.

**Base URL**: `https://dev.api.saaradhigo.in/api/v1/`

---

## 2. Authentication & Security
The authentication system utilizes Phone Number validation via OTP (One-Time Passwords). Successful authentication yields JWT tokens used for authorizing subsequent requests. 

**Role Management:** The `role` field on a `User` specifies access rights (`rider` or `driver`).

**Security Headers:**
- **Authorization**: `Bearer <Access_Token>`

---

## 3. Endpoints

### 3.1 Authentication (`/auth/`)

#### **`POST /otp/`**: Request an OTP
- **Description:** Generates an OTP and sends it via SMS (AWS SNS). Stores session in cache for 10 minutes.
- **Request Parameters (JSON):**
```json
{
  "phone_number": "+919876543210",
  "role": "rider"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "OTP sent successfully",
    "task_id": "uuid-celery-task",
    "otp": "123456",
    "expires_in": 600
  }
}
```

#### **`POST /login/`**: Verify OTP & Login
- **Description:** Verifies OTP. Creates user and role-specific profile (Rider/Driver) if not existing.
- **Request Parameters (JSON):**
```json
{
  "phone_number": "+919876543210",
  "otp": "123456",
  "device_token": "fcm_token_string",
  "password": "optional_password"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "token": "access_token_jwt",
    "refresh_token": "refresh_token_jwt",
    "user": {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "gender": "male",
      "dob": "1990-01-01",
      "phone_number": "+919876543210",
      "avatar": "https://s3.amazonaws.com/bucket/avatar.jpg",
      "house_no": "123",
      "street": "Main St",
      "city": "Hyderabad",
      "zip_code": "500001",
      "emergency_contact": "9876543211",
      "role": "rider"
    }
  }
}
```

#### **`POST /refresh/`**: Refresh JWT Token
- **Request Parameters (JSON):**
```json
{ 
  "refresh_token": "token_string" 
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "token": "new_access_token",
    "refresh_token": "new_refresh_token"
  }
}
```

#### **`PATCH /update/`**: Update User Profile
- **Description:** Updates the profile of the currently authenticated user.
- **Auth Required:** Yes
- **Content-Type:** `multipart/form-data`
- **Request Body (All Optional):**
  - `full_name`: string
  - `email`: string
  - `gender`: string
  - `dob`: string (YYYY-MM-DD)
  - `house_no`: string
  - `street`: string
  - `city`: string
  - `zip_code`: string
  - `emergency_contact`: string
  - `avatar`: File
- **Full Update Example Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "full_name": "John Doe Updated",
    "email": "john@example.com",
    "gender": "male",
    "dob": "1990-01-01",
    "phone_number": "+919876543210",
    "avatar": "https://s3.amazonaws.com/bucket/avatar_new.jpg",
    "house_no": "456",
    "street": "Second St",
    "city": "Hyderabad",
    "zip_code": "500100",
    "emergency_contact": "9876543211",
    "role": "rider"
  }
}
```

#### **`GET /profile/`**: Get Profile Info
- **Auth Required:** Yes
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "full_name": "John Doe",
    "email": "john@example.com",
    "gender": "male",
    "dob": "1990-01-01",
    "phone_number": "+919876543210",
    "avatar": "https://s3.amazonaws.com/bucket/avatar.jpg",
    "house_no": "123",
    "street": "Main St",
    "city": "Hyderabad",
    "zip_code": "500001",
    "emergency_contact": "9876543211",
    "role": "rider"
  }
}
```

---

### 3.2 Rider (`/rider/`)

#### **`POST /locations/`**: Save Favorite Location
- **Request Parameters (JSON):**
```json
{
  "address_text": "Work Office",
  "latitude": 17.4400,
  "longitude": 78.3489
}
```
- **Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": 5,
    "address_text": "Work Office",
    "latitude": 17.4400,
    "longitude": 78.3489,
    "user_id": 1
  }
}
```

#### **`GET /locations/all/`**: List Favorite Locations
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "address_text": "Home",
      "latitude": 17.3850,
      "longitude": 78.4867,
      "user_id": 1
    },
    {
      "id": 5,
      "address_text": "Work Office",
      "latitude": 17.4400,
      "longitude": 78.3489,
      "user_id": 1
    }
  ]
}
```

#### **`DELETE /locations/<id>/delete/`**: Delete Favorite Location
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Favorite location deleted successfully"
  }
}
```

#### **`GET /nearby/`**: Get Nearby Drivers
- **Query Params:** `lat`, `lng`, `radius` (default 1000m), `count` (default 10).
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "driver_id": "12",
      "distance": 450.5
    },
    {
      "driver_id": "15",
      "distance": 890.2
    }
  ]
}
```

#### **`GET /notifications/`**: List Notifications
- **Response (Paginated JSON):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 12,
      "title": "Ride Accepted",
      "message": "Driver John is arriving.",
      "is_read": false,
      "created_at": "2024-03-19T10:00:00Z"
    }
  ]
}
```

#### **`PATCH /notifications/<id>/read/`**: Mark as Read
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Marked as read"
  }
}
```

#### **`POST /notifications/read-all/`**: Mark All Read
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "All notifications marked as read"
  }
}
```

#### **`GET /wallet/balance/`**: Get Wallet Balance
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "balance": "150.00"
  }
}
```

---

### 3.3 Driver (`/driver/`)

#### **`PATCH /driver/`**: Update Driver Profile
- **Request Parameters (Multipart/Form-Data):**
```json
{
  "active_vehicle": 1,
  "license_expiry": "2030-12-31"
  // license_doc: <file uploaded as binary>
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "user_id": 1,
    "status": "online",
    "ratings": "4.8",
    "approved": true,
    "active_vehicle": 1,
    "license_doc": "https://s3.amazonaws.com/bucket/license.pdf",
    "license_expiry": "2030-12-31"
  }
}
```

#### **`GET /earnings/`**: Earnings List
- **Query Params:** `page`, `page_size`.
- **Success Response (Paginated JSON):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "trip_id": 101,
      "amount": "200.00",
      "commission": "20.00",
      "net_amount": "180.00",
      "created_at": "2024-03-19T10:00:00Z"
    },
    {
      "id": 2,
      "trip_id": 105,
      "amount": "300.00",
      "commission": "30.00",
      "net_amount": "270.00",
      "created_at": "2024-03-19T14:00:00Z"
    }
  ]
}
```

#### **`GET /earnings/summary/`**: Earnings Summary
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "total_earned": "5000.00",
    "total_trips": 45,
    "today_earned": "450.00",
    "commission_percent": 10
  }
}
```

#### **`GET /vehicles/`**: List Vehicles
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "vehicle_number": "TS09AB1234",
      "vehicle_type_name": "sedan",
      "brand": "Maruti",
      "model": "Ciaz",
      "color": "White",
      "year": 2021,
      "capacity": 4,
      "rc_doc": "https://s3.amazonaws.com/bucket/rc.pdf",
      "vehicle_pic": "https://s3.amazonaws.com/bucket/pic.jpg",
      "status": "active"
    }
  ]
}
```

#### **`POST /vehicles/add/`**: Add Vehicle
- **Request Parameters (Multipart/Form-Data):**
```json
{
  "vehicle_number": "TS09AB1234",
  "vehicle_type": "sedan",
  "brand": "Maruti",
  "model": "Ciaz",
  "year": 2021,
  "capacity": 4
  // rc_doc: <file>
  // vehicle_pic: <file>
}
```
- **Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": 2,
    "vehicle_number": "TS09AB1234",
    "vehicle_type_name": "sedan",
    "brand": "Maruti",
    "model": "Ciaz",
    "status": "pending_approval"
  }
}
```

#### **`PATCH /vehicles/<id>/`**: Update Vehicle
- **Request Parameters (Multipart/Form-Data):**
  - any from `brand`, `model`, `color`, `year`, `capacity`, `vehicle_pic`, `vehicle_number`, `rc_doc`.
- **Success/Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "vehicle_number": "TS09AB1234",
    "color": "Silver",
    "capacity": 5,
    "status": "active"
  }
}
```

#### **`DELETE /vehicles/<id>/delete/`**: Delete Vehicle
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Vehicle deleted successfully"
}
```

---

### 3.4 Ride (`/ride/`)

#### **`POST /estimate-fare/`**: Estimate Fare
- **Request Parameters (JSON):**
```json
{
  "pickup_lat": 17.3850,
  "pickup_long": 78.4867,
  "destination_lat": 17.4400,
  "destination_long": 78.3489,
  "distance_km": 15.5,
  "duration_min": 35,
  "vehicle_type": "sedan"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "estimated_fare": "250.00",
    "fare_breakdown": {
      "base_fare": "50.00",
      "distance_fare": "150.00",
      "time_fare": "50.00",
      "surge_multiplier": "1.0",
      "total_fare": "250.00"
    },
    "vehicle_type": "sedan",
    "distance_km": 15.5,
    "duration_min": 35
  }
}
```

#### **`GET /ride-history/`**: Rider Trip History
- **Success Response (Paginated JSON):**
```json
{
  "count": 50,
  "next": "endpoint/v1/ride/ride-history/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "status": "completed",
      "pickup_address": "Home",
      "destination_address": "Office",
      "estimated_fare": "150.00",
      "final_fare": "150.00",
      "created_at": "2024-03-19T08:00:00Z"
    }
  ]
}
```

#### **`GET /driver-history/`**: Driver Trip History
- **Success Response (Paginated JSON):** Similar to rider history.

#### **`GET /trip/<id>/`**: Get Trip Details
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "user_id": 1,
    "driver_id": 12,
    "status": "completed",
    "pickup_lat": "17.3850",
    "pickup_long": "78.4867",
    "pickup_address": "Home",
    "destination_address": "Office",
    "estimated_fare": "150.00",
    "final_fare": "150.00",
    "fare_details": {
      "base_fare": "40.00",
      "distance_fare": "100.00",
      "time_fare": "10.00",
      "total_fare": "150.00"
    },
    "rating": {
      "score": 5,
      "comments": "Great ride"
    }
  }
}
```

#### **`POST /rate-trip/`**: Rate Completed Trip
- **Request Parameters (JSON):**
```json
{
  "trip_id": 1,
  "score": 5,
  "comments": "Excellent service"
}
```
- **Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "trip_id": 1,
    "rater_id": 1,
    "score": 5,
    "comments": "Excellent service"
  }
}
```

---

### 3.5 Payments (`/payments/`)

#### **`POST /create-order/`**: Initialize Payment
- **Request Parameters (JSON):**
```json
{
  "trip_id": 1
}
```
- **Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "payment_id": 15,
    "razorpay_order_id": "order_ERfabc123",
    "amount": "150.00",
    "currency": "INR",
    "description": "Payment for Trip #1"
  }
}
```

#### **`POST /verify/`**: Verify Payment
- **Request Parameters (JSON):**
```json
{
  "razorpay_order_id": "order_ERfabc123",
  "razorpay_payment_id": "pay_987xyz654",
  "razorpay_signature": "signature_hash_xyz"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Payment verified"
}
```

#### **`GET /history/`**: Payment History
- **Success Response (Paginated JSON):**
```json
{
  "count": 1,
  "results": [
    {
      "id": 15,
      "trip_id": 1,
      "amount": "150.00",
      "status": "completed",
      "method": "online",
      "created_at": "2024-03-19T10:05:00Z"
    }
  ]
}
```

#### **`POST /refund/`**: Refund Payment
- **Request Parameters (JSON):**
```json
{
  "trip_id": 1
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Refund initiated",
  "data": {
    "refund_id": "rfnd_abc123",
    "amount": "150.00"
  }
}
```

---

### 3.6 Admin APIs 

#### **`PATCH /driver/admin/<id>/update-kyc/`**: Approve Driver
- **Request Parameters (JSON):**
```json
{
  "approved": true,
  "status": "active"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "approved": true,
    "status": "active"
  }
}
```

---

## 4. WebSocket APIs (`ws://<host>/ws/`)

### 4.1 Driver Location Tracking
- **Path:** `ws/driver/location/?token=<jwt>`
- **Client -> Server (JSON Action):**
```json
{
  "lng": 78.4867,
  "lat": 17.3850
}
```
- **Server -> Client (JSON Response):**
```json
{
  "type": "location_updated",
  "lng": 78.4867,
  "lat": 17.3850
}
```

### 4.2 Ride Requesting (Rider)
- **Path:** `ws/ride/request/?token=<jwt>`
- **Client -> Server (Action: Request JSON):**
```json
{
  "pickup_lat": 17.385,
  "pickup_lng": 78.486,
  "destination_lat": 17.440,
  "destination_lng": 78.348,
  "pickup_address": "Point A",
  "destination_address": "Point B",
  "vehicle_type": "sedan",
  "distance_km": 15.5,
  "duration_min": 35
}
```
- **Server -> Client (JSON Confirmation):**
```json
{
  "type": "trip_created",
  "trip_id": 105,
  "estimated_fare": "250.00",
  "message": "Searching for nearby drivers..."
}
```

### 4.3 Trip Status (Rider & Driver)
- **Path:** `ws/ride/trip/<trip_id>/?token=<jwt>`
- **Driver -> Server (Action: Accept JSON):**
```json
{
  "action": "accept"
}
```
- **Server -> All Participants (JSON Broadcast):**
```json
{
  "type": "trip_status_update",
  "trip_id": 105,
  "status": "accept",
  "message": "Trip accepted",
  "driver_id": 12,
  "otp": "123456",
  "driver_info": { "name": "Driver John", "phone": "9876543210" },
  "vehicle_info": { "number": "TS09AB1234", "model": "Ciaz" }
}
```
