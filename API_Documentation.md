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

#### **`GET /profile/`**: Get User Profile
- **Description:** Retrieves the profile of the currently authenticated user.
- **Auth Required:** Yes
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "phone_number": "+919876543210",
    "role": "rider",
    "full_name": "John Doe",
    "email": "john@example.com",
    "gender": "male",
    "dob": "1990-01-01"
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

#### **`PATCH /notifications/<id>/read/`**: Mark Notification as Read
- **Auth Required:** Yes
- **Success Response (200 OK):** `{ "status": "success", "data": { "message": "Marked as read" } }`

#### **`POST /notifications/read-all/`**: Mark All Notifications as Read
- **Auth Required:** Yes
- **Success Response (200 OK):** `{ "status": "success", "data": { "message": "All notifications marked as read" } }`

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

#### **`GET /earnings/`**: Earnings List
- **Description:** Paginated list of driver earnings.
- **Auth Required:** Yes (Driver role)
- **Query Params:** `?page=1&page_size=10`
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "count": 10,
    "next": "...",
    "previous": null,
    "results": [
      {
        "id": 1,
        "trip_id": 123,
        "amount": "150.00",
        "commission": "15.00",
        "net_amount": "135.00",
        "created_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

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

#### **`GET /vehicles/`**: List Driver Vehicles
- **Auth Required:** Yes (Driver role)
- **Success Response (200 OK):** Array of Vehicle objects.

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

#### **`PATCH /vehicles/<int:vehicle_id>/`**: Update Vehicle
- **Auth Required:** Yes (Driver role)
- **Request Body:** (Fields optional: brand, model, color, year, capacity, vehicle_pic, vehicle_number)
- **Success Response (200 OK):** Updated Vehicle object.

#### **`DELETE /vehicles/<int:vehicle_id>/delete/`**: Delete Vehicle
- **Auth Required:** Yes (Driver role)
- **Success Response (200 OK):** `{ "status": "success", "data": { "message": "Vehicle deleted successfully" } }`

---

### 3.4 Ride (`/ride/`)

#### **`GET /ride-history/`**: Rider Trip History
- **Auth Required:** Yes (Rider role)
- **Query Params:** `?page=1&status=completed`
- **Success Response (200 OK):** Paginated list of Trip objects.

#### **`GET /driver-history/`**: Driver Trip History
- **Auth Required:** Yes (Driver role)
- **Query Params:** `?page=1&status=completed`
- **Success Response (200 OK):** Paginated list of Trip objects.

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

#### **`POST /webhook/`**: Razorpay Webhook
- **Description:** Endpoint for Razorpay to send payment notifications (e.g., `payment.captured`).
- **Auth Required:** No (Verified via `X-Razorpay-Signature` header)
- **Success Response (200 OK):** `{ "status": "ok" }`

#### **`GET /history/`**: Payment History
- **Auth Required:** Yes
- **Query Params:** `?page=1&status=completed`
- **Success Response (200 OK):** Paginated list of payment records.

#### **`POST /refund/`**: Refund Payment
- **Description:** Initiates a refund for a cancelled trip if the payment was made online.
- **Auth Required:** Yes
- **Request Body:** `{ "trip_id": 1 }`
- **Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Refund initiated successfully",
    "refund_id": "rfnd_...",
    "amount": "260.00",
    "trip_id": 1
  }
}
```

---

## 4. WebSocket Connections (Real-Time)

All Real-time WebSockets operate at endpoint: `ws://<domain-or-host>:8000/ws/`
Connections require authentication via Query Parameters: `?token=<access_token>`

### 4.0 Connection Handshake
Upon successful connection, the server sends:
```json
{
  "type": "connection_established",
  "message": "Connected successfully"
}
```

**Common Error Codes (Close Codes):**
- `4001`: Unauthorized (Missing or invalid token)
- `4003`: Invalid Profile (e.g., user is not a driver)
- `4004`: Driver Not Approved

### 4.1 Drivers Location Tracking
**URL:** `ws://localhost:8000/ws/driver/location/?token={{access_token}}`
- **Action (Client -> Server):** Send current location.
```json
{
  "lng": 78.486,
  "lat": 17.385
}
```
- **Server Action:** Updates geospatial bounds in Redis. If the driver is on an active trip, broadcasts to `trip_<id>` group.

### 4.2 Rider Ride Requests
**URL:** `ws://localhost:8000/ws/ride/request/?token={{access_token}}`
- **Action (Rider -> Server):** Initiates searching for nearby drivers.
```json
{
  "pickup_lat": 17.385,
  "pickup_lng": 78.486,
  "destination_lat": 17.440,
  "destination_lng": 78.348,
  "pickup_address": "Point A",
  "destination_address": "Point B",
  "distance_km": 15.5,
  "duration_min": 35,
  "vehicle_type": "car"
}
```
- **Retry Action (Rider -> Server):**
```json
{
  "action": "retry",
  "trip_id": 1,
  "radius": 5000 // optional, in meters
}
```
- **Server Notifications (to Rider):**
    - `trip_created`: `{ "type": "trip_created", "trip_id": 1, ... }`
    - `drivers_notified`: `{ "type": "drivers_notified", "trip_id": 1, "drivers_notified": 5 }`

- **Server Action (Broadcast to `Driver`):**
```json
{
  "type": "ride_request",
  "trip_id": 1,
  "rider_name": "John Doe",
  "pickup_lat": "17.385",
  "pickup_lng": "78.486",
  "destination_lat": "17.440",
  "destination_lng": "78.348",
  "pickup_address": "Point A",
  "destination_address": "Point B",
  "estimated_fare": "250.00"
}
```

### 4.3 Trip Status Updates
**URL:** `ws://localhost:8000/ws/ride/trip/<trip_id>/?token={{access_token}}`
- **Description:** Dedicated channel for a single trip. Both Rider and Driver connect here.
- **Action (Driver -> Server):** Update ride state
```json
{
  "action": "accept" // "accept", "start", "complete", "cancel"
}
```
- **Action (Server -> Client Broadcast):**
```json
{
  "type": "trip_status_update",
  "trip_id": 1,
  "status": "accept", // "accept", "start", "complete", "cancel"
  "message": "Trip accepted",
  "driver_id": 12,
  "otp": "123456", // sent on 'accept'
  "driver_info": { ... }, // sent on 'accept'
  "vehicle_info": { ... } // sent on 'accept'
}
```
- **Driver Location Update (Server -> Rider):**
```json
{
  "type": "driver_location_update",
  "lng": 78.486,
  "lat": 17.385,
  "driver_id": 12
}
```

---

### 3.6 Admin APIs 

Admin APIs are secured and require the authenticated user to hold an `admin` role and have `is_superuser` privileges.

#### **`GET /auth/admin/users/`**: List Users
- **Description:** List all users across the platform with pagination.
- **Auth Required:** Yes (Admin role)
- **Query Params:** 
  - `role`: string (`rider`, `driver`, `admin`)
  - `is_active`: boolean (`true`, `false`)
  - `page`: integer
  - `page_size`: integer
- **Success Response (200 OK):** Paginated list of User objects.

#### **`GET /driver/admin/`**: List Drivers
- **Description:** List all drivers on the platform with filtering and pagination.
- **Auth Required:** Yes (Admin role)
- **Query Params:**
  - `approved`: boolean (`true`, `false`)
  - `status`: string
  - `page`: integer
  - `page_size`: integer
- **Success Response (200 OK):** Paginated list of Driver objects.

#### **`GET /driver/admin/<id>/`**: Retrieve Driver Details
- **Description:** Get detailed information for a single driver, including their user profile and registered vehicles.
- **Auth Required:** Yes (Admin role)
- **Success Response (200 OK):** Detailed Driver object.

#### **`PATCH /driver/admin/<id>/update-kyc/`**: Update KYC Status
- **Description:** Approve or reject KYC for a given driver.
- **Auth Required:** Yes (Admin role)
- **Request Body:**
```json
{
  "approved": true,
  "status": "active"
}
```
- **Success Response (200 OK):** Updated Driver object.

#### **`DELETE /driver/admin/<id>/delete/`**: Delete Driver
- **Description:** Delete a driver profile and associated vehicles.
- **Auth Required:** Yes (Admin role)
- **Success Response (200 OK):** `{ "status": "success", "data": { "message": "Driver deleted successfully" } }`

#### **`GET /ride/admin/trips/`**: List Trips
- **Description:** List all trips across the platform with filtering and pagination.
- **Auth Required:** Yes (Admin role)
- **Query Params:**
  - `status`: string (`pending` | `accepted` | `arriving` | `in_progress` | `completed` | `cancelled`)
  - `driver_id`: integer
  - `user_id`: integer (rider)
  - `page`: integer
  - `page_size`: integer
- **Success Response (200 OK):** Paginated list of Trip objects.

#### **`GET /ride/admin/live-locations/`**: Live Locations
- **Description:** Fetch real-time active locations for all online drivers and riders from the Redis cache.
- **Auth Required:** Yes (Admin role)
- **Success Response (200 OK):** 
```json
{
  "status": "success",
  "data": {
    "drivers": [...],
    "riders": [...]
  }
}
```

#### **`GET /payments/admin/payments/`**: List Payments
- **Description:** List all payments on the platform.
- **Auth Required:** Yes (Admin role)
- **Query Params:**
  - `status`: string
  - `method`: string
  - `page`: integer
  - `page_size`: integer
- **Success Response (200 OK):** Paginated list of Payment objects.

#### **`GET /payments/admin/transactions/`**: List Transactions
- **Description:** List all transaction history logs.
- **Auth Required:** Yes (Admin role)
- **Query Params:**
  - `status`: string
  - `page`: integer
  - `page_size`: integer
- **Success Response (200 OK):** Paginated list of TransactionHistory objects.

---

## 5. Data Models (ER Overview)

### 5.1 Auth (`customUser`)
- `phone_number` (Unique, E.164)
- `role` (rider, driver, admin)
- `full_name`, `email`, `gender`, `dob`
- `house_no`, `street`, `city`, `zip_code`
- `fcm_token`

### 5.2 Rider
- `user_id` (OneToOne -> customUser)
- `rating` (Decimal, default 5.0)
- **FavoritePlace**: `user_id`, `address_text`, `latitude`, `longitude`
- **Wallet**: `user_id`, `balance`
- **Notification**: `user_id`, `title`, `message`, `is_read`

### 5.3 Driver
- `user_id` (OneToOne -> customUser)
- `status` (online, off, active, on ride, blocked)
- `ratings` (Decimal)
- `approved` (Boolean)
- `active_vehicle` (ForeignKey -> Vehicle)
- **Vehicle**: `driver_id`, `vehicle_type_id`, `brand`, `model`, `vehicle_number`, `status`
- **VehicleType**: `type`, `description`
- **DriverEarning**: `driver_id`, `trip_id`, `commission`, `net_amount`

### 5.4 Ride
- **Trip**: 
    - `user_id` (Rider)
    - `driver_id` (Assigned Driver)
    - `status_id` (ForeignKey -> TripStatus)
    - `pickup_lat`, `pickup_long`, `destination_lat`, `destination_long`
    - `estimated_fare`, `final_fare`
    - `otp` (6-digit)
- **FarePricing**: Detailed breakdown for each Trip.
- **Rating**: `trip_id`, `rater_id` (User), `score` (1-5), `comments`.

---

## 6. Architecture Summary
- **Framework**: Django 5.x with Django Rest Framework (DRF).
- **Real-time**: Django Channels with WebSockets.
- **Cache/Geo**: Redis used for real-time driver location indexing (`GEOADD`) and WebSocket channel layers.
- **Database**: PostgreSQL (Primary) + Redis (Cache).
- **Background Tasks**: Celery with Redis as broker for OTP SMS and auto-cancellation logic.
- **External Services**: 
    - Razorpay (Payments & Refunds)
    - AWS SNS (Transactional SMS)
    - OpenStreetMap (Routing & Geocoding)
