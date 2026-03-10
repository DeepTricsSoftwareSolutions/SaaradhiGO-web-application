# VahanGo API Documentation

## 1. Overview
The VahanGo API provides backend services for a ride-hailing platform, facilitating functionalities for Riders, Drivers, Ride Matching, and Payment processing.

**Base URL**: `https://vahango-web-application.onrender.com/api/v1/`

---

## 2. Authentication & Security
The authentication system utilizes Phone Number validation via OTP (One-Time Passwords). Successful authentication yields JWT tokens used for authorizing subsequent requests. 

**Role Management:** The `role` field on a `User` specifies access rights (`rider` or `driver`).

**Security Headers:**
- **Authorization**: `Bearer <Access_Token>`

---

## 3. Endpoints

### 3.1 Authentication (`/auth/`)

#### **`POST /otp/`**: Request an OTP to login/signup
- **Description:** Generates an OTP and sends it via SMS. Creates an unauthenticated session tied to the phone number.
- **Request Body:**
```json
{
  "phone_number": "+919876543210",
  "role": "rider" // "rider" or "driver"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "OTP sent successfully",
    "task_id": "uuid-celery-task",
    "expires_in": 600
  }
}
```
- **Error Response (400 Bad Request):** Returns missing fields or invalid format issues.

#### **`POST /login/`**: Verify OTP & Login
- **Description:** Verifies the OTP. If the user doesn't exist, it creates a new user profile based on the requested role.
- **Request Body:**
```json
{
  "phone_number": "+919876543210",
  "otp": "123456",
  "device_token": "fcm_device_token_string" // Optional
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1...",
    "refresh_token": "eyJhbGciOiJIUzI1...",
    "user": {
      "id": 1,
      "phone_number": "+919876543210",
      "role": "rider",
      "full_name": null,
      "email": null,
      // ... other profile fields ...
    }
  }
}
```

#### **`POST /refresh/`**: Refresh JWT Token
- **Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1..."
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "token": "new_access_token_string",
    "refresh_token": "new_refresh_token_string"
  }
}
```

#### **`PATCH /update/`**: Update User Info
- **Description:** Updates the profile of the currently authenticated user.
- **Auth Required:** Yes
- **Request Body:** (All fields optional)
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "gender": "male",
  "dob": "1990-01-01"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "phone_number": "+919876543210",
    "role": "rider",
    "full_name": "John Doe",
    "email": "john@example.com"
  }
}
```

---

### 3.2 Rider (`/rider/`)

#### **`POST /locations/`**: Save Favorite Location
- **Auth Required:** Yes
- **Request Body:**
```json
{
  "address_text": "Home Base",
  "latitude": 17.3850,
  "longitude": 78.4867
}
```
- **Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "location": {
      "id": 1,
      "address_text": "Home Base",
      "latitude": 17.3850,
      "longitude": 78.4867
    }
  }
}
```

#### **`GET /locations/all/`**: List Favorite Locations
- **Auth Required:** Yes
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "address_text": "Home Base",
      "latitude": 17.3850,
      "longitude": 78.4867
    }
  ]
}
```

#### **`GET /nearby/`**: Get Nearby Drivers
- **Description:** Queries Redis geospatial index to find nearby drivers.
- **Auth Required:** Yes
- **Query Params:** `?lat=17.385&lng=78.4867&radius=1000` (Defaults: `radius=1000`, `count=10`)
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "driver_id": "12",
      "distance": 450.5
    }
  ]
}
```

#### **`GET /notifications/`**: List Notifications
- **Auth Required:** Yes
- **Success Response (200 OK):** (Paginated)
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Welcome",
      "message": "Welcome to VahanGo!",
      "is_read": false,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

---

### 3.3 Driver (`/driver/`)

#### **`PATCH /driver/`**: Update Driver Profile
- **Description:** Used to set active vehicle or other driver specifics.
- **Auth Required:** Yes (Driver role)
- **Request Body:**
```json
{
  "active_vehicle": 1
}
```
- **Success Response (200 OK):** Current driver profile info.

#### **`GET /earnings/summary/`**: Earnings Summary
- **Auth Required:** Yes (Driver role)
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "total_earned": "1500.00",
    "total_commission": "150.00",
    "total_trips": 10,
    "today_earned": "300.00",
    "today_trips": 2,
    "commission_percent": 10.0
  }
}
```

#### **`POST /vehicles/add/`**: Add a Vehicle
- **Auth Required:** Yes (Driver role)
- **Request Body:**
```json
{
  "vehicle_number": "TS09AB1234",
  "vehicle_type": "car",
  "brand": "Maruti",
  "model": "Swift",
  "color": "White",
  "year": 2022,
  "capacity": 4
}
```
- **Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "vehicle_number": "TS09AB1234",
    "vehicle_type": "car",
    "brand": "Maruti"
  }
}
```

---

### 3.4 Ride (`/ride/`)

#### **`POST /estimate-fare/`**: Calculate Preliminary Fare
- **Description:** Calculates fare. Computes local micro-surge based on real-time rider demand vs driver supply.
- **Auth Required:** Yes
- **Request Body:**
```json
{
  "pickup_lat": 17.3850,
  "pickup_long": 78.4867,
  "destination_lat": 17.4400,
  "destination_long": 78.3489,
  "distance_km": 15.5,
  "duration_min": 35,
  "vehicle_type": "car"
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
      "distance_fare": "155.00",
      "time_fare": "17.50",
      "surge_multiplier": "1.15",
      "min_fare_applied": false
    },
    "vehicle_type": "car",
    "pricing_source": "db",
    "distance_km": 15.5,
    "duration_min": 35,
    "validated_km": 15.6,
    "validated_min": 36.2
  }
}
```

#### **`GET /trip/<id>/`**: Get Trip Details
- **Auth Required:** Yes
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "pickup_address": "Point A",
    "destination_address": "Point B",
    "status": "completed",
    "estimated_fare": "250.00",
    "final_fare": "260.00",
    "driver": { /* Driver Info */ }
  }
}
```

#### **`POST /rate-trip/`**: Rate a completed trip
- **Auth Required:** Yes
- **Request Body:**
```json
{
  "trip_id": 1,
  "score": 5,
  "comments": "Great ride!"
}
```
- **Success Response (200 OK):** `{ "status": "success", "data": { "message": "Rating submitted" } }`

---

### 3.5 Payments (`/payments/`)

#### **`POST /create-order/`**: Initialize Razorpay Order
- **Auth Required:** Yes
- **Request Body:** `{ "trip_id": 1 }`
- **Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "payment_id": 15,
    "razorpay_order_id": "order_abcd123",
    "razorpay_key_id": "rzp_test_123",
    "amount": "260.00",
    "amount_paise": 26000,
    "currency": "INR",
    "trip_id": 1,
    "description": "Payment for Trip #1",
    "prefill": {
      "name": "John Doe",
      "contact": "+919876543210",
      "email": "john@example.com"
    }
  }
}
```

#### **`POST /verify/`**: Verify Payment Signature
- **Auth Required:** Yes
- **Request Body:**
```json
{
  "razorpay_order_id": "order_abcd123",
  "razorpay_payment_id": "pay_xyz987",
  "razorpay_signature": "sig_hash_string"
}
```
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Payment verified successfully",
    "payment_id": 15,
    "status": "completed",
    "amount": "260.00"
  }
}
```

---

## 4. WebSocket Connections (Real-Time)

All Real-time WebSockets operate at endpoint: `ws://<domain-or-host>:8000/ws/`
Connections require authentication via Query Parameters: `?token=<access_token>`

### 4.1 Drivers Location Tracking
**URL:** `ws://localhost:8000/ws/driver/location/?token={{access_token}}`
- **Action (Client -> Server):** Send current location to update geospatial bounds.
```json
{
  "type": "location_update",
  "latitude": 17.385,
  "longitude": 78.486
}
```
- **Server Action:** No JSON response, but internally caches location to Redis (`drivers:geo`) and maps to personal `driver_<driver_id>` channels group.

### 4.2 Rider Ride Requests
**URL:** `ws://localhost:8000/ws/ride/request/?token={{access_token}}`
- **Action (Rider -> Server):** Initiates searching for nearby drivers to serve the request.
```json
{
  "type": "ride_request",
  "pickup_lat": 17.385,
  "pickup_lng": 78.486,
  "destination_lat": 17.440,
  "destination_lng": 78.348,
  "distance_km": 15.5,
  "duration_min": 35,
  "vehicle_type": "car"
}
```
- **Server Action (Broadcast to `Driver`):**
```json
{
  "type": "ride.request",
  "ride_details": {
    "trip_id": 1,
    "pickup_lat": 17.385,
    "pickup_long": 78.486,
    "distance": "15.50",
    "estimated_fare": "250.00"
  }
}
```

### 4.3 Trip Status Updates
**URL:** `ws://localhost:8000/ws/ride/trip/<trip_id>/?token={{access_token}}`
- **Description:** Dedicated channel room for a single trip. Both Rider and Driver connect here once a trip is accepted.
- **Action (Driver -> Server):** Update ride state
```json
{
  "action": "accept" 
  // Other valid states: "arrive", "start", "complete", "cancel"
}
```
- **Action (Server -> Client Broadcast):** Server echoes the state mutation to both rider and driver.
```json
{
  "type": "trip_update",
  "status": "accepted", // or arriving, in_progress, completed, cancelled
  "timestamp": "2024-01-01T12:00:00Z"
}
```
