# 📘 VahanGoBase API Documentation (v1)

---

## 🏗 Project Overview
VahanGoBase is a comprehensive ride-hailing backend service built with **Django** and **Django REST Framework (DRF)**. Real-time features are powered by **Django Channels**, utilizing **Redis** as a channel layer. Background tasks (e.g., OTP dispatch, ride expiration) are potentially handled through Redis/Celery. The payments domain integrates with **Razorpay**. 

## 🗺 Architecture Summary
- **Framework**: Django & DRF
- **Database**: PostgreSQL (Production)
- **WebSockets**: Django Channels (Redis ASGI backend)
- **Authentication**: JWT (SimpleJWT)
- **Models / Roles**: Generic User model with Profile segregations (Rider, Driver, Admin).
- **Background Tasks**: Redis Queue / Celery (OTP, Auto-cancel trip).
- **External Integrations**: 
  - **AWS SNS**: For sending OTPs.
  - **Razorpay**: For trip payment processing.
  - **FCM**: For Push Notifications.

---

## 🔐 Authentication & Security

- **Mechanism**: JWT (JSON Web Tokens). Most endpoints require passing the token as a Bearer token in the `Authorization` header.
- **Header Format**: `Authorization: Bearer <access_token>`
- **Token Generation**: Uses OTP verification to grant an Access and Refresh token.
- **WebSocket Auth**: Uses standard Django user sessions or query params token (`ws://.../?token=<jwt>`), though currently implemented logic directly checks `self.scope.get('user')` which often implies middleware parsing.
- **Rate Limiting**: Custom limits are not explicitly configured but standard DRF throttling can be applied. OTP throttling is handled logically (max 5 attempts per 10 mins).
- **Security Check**: CSRF trusted origins include Render deployments (`https://*.onrender.com`). CORS allows all origins natively in dev/prod.

---

## 🌐 Base URL
- **Local**: `https://vahango-web-application.onrender.com/api/v1/`
- **WS Local**: `ws://vahango-web-application.onrender.com/`

---

## 🚀 API Endpoints

### 👤 1. Auth & User Management (`/auth/`)

#### Request OTP
* **Endpoint**: `POST /api/v1/auth/otp/`
* **Description**: Request an OTP to verify phone number for login/signup.
* **Auth Required**: No
* **Sample Request**:
  ```json
  {
      "phone_number": "+919876543210",
      "role": "rider"  // or "driver"
  }
  ```
* **Sample Response**:
  ```json
  {
      "success": true,
      "data": {
          "message": "OTP sent successfully",
          "task_id": "uuid",
          "otp": "123456",
          "expires_in": 600
      }
  }
  ```

#### Verify OTP & Login
* **Endpoint**: `POST /api/v1/auth/login/`
* **Description**: Complete authentication using OTP. Generates JWT tokens and user profiles on first login.
* **Auth Required**: No
* **Sample Request**:
  ```json
  {
      "phone_number": "+919876543210",
      "otp": "123456",
      "device_token": "fcm_token_optional"
  }
  ```
* **Sample Response**:
  ```json
  {
      "success": true,
      "data": {
          "token": "access_token_jwt",
          "refresh_token": "refresh_token_jwt",
          "user": {
              "id": 1,
              "full_name": null,
              "phone_number": "+919876543210",
              "role": "rider"
          }
      }
  }
  ```

#### Refresh Token
* **Endpoint**: `POST /api/v1/auth/refresh/`
* **Description**: Exchanges a valid refresh token for a new access token.
* **Auth Required**: No
* **Request**: `{"refresh_token": "jwt_refresh"}`
* **Response**: `{"token": "new_access_token", "refresh_token": "new_refresh_token"}`

#### Update Profile
* **Endpoint**: `PATCH /api/v1/auth/update/`
* **Description**: Updates authenticated user info (name, email, address, etc).
* **Auth Required**: Yes
* **Sample Request**:
  ```json
  {
      "full_name": "John Doe",
      "email": "johndoe@example.com",
      "gender": "male",
      "dob": "1990-01-01",
      "house_no": "123",
      "street": "Main Street",
      "city": "Hyderabad",
      "zip_code": "500001",
      "emergency_contact": "+919876543211",
      "avatar": "url_to_image"
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "id": 1,
          "username": "",
          "full_name": "John Doe",
          "phone_number": "+919876543210",
          "email": "johndoe@example.com",
          "gender": "male",
          "dob": "1990-01-01",
          "house_no": "123",
          "street": "Main Street",
          "city": "Hyderabad",
          "zip_code": "500001",
          "emergency_contact": "+919876543211",
          "role": "rider",
          "avatar": "url_to_image",
          "fcm_token": "token",
          "updated_at": "2023-10-01T12:00:00Z",
          "created_at": "2023-01-01T12:00:00Z"
      }
  }
  ```

---

### 🛵 2. Rider Operations (`/rider/`)

#### Save Favorite Location
* **Endpoint**: `POST /api/v1/rider/locations/`
* **Auth Required**: Yes
* **Sample Request**:
  ```json
  {
      "address_text": "Home",
      "latitude": 17.3850,
      "longitude": 78.4867
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "location": {
              "id": 1,
              "address_text": "Home",
              "latitude": "17.385000",
              "longitude": "78.486700",
              "created_at": "2023-10-01T12:00:00Z"
          }
      }
  }
  ```

#### Get Favorite Locations
* **Endpoint**: `GET /api/v1/rider/locations/all/`
* **Auth Required**: Yes
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": [
          {
              "id": 1,
              "address_text": "Home",
              "latitude": "17.385000",
              "longitude": "78.486700",
              "created_at": "2023-10-01T12:00:00Z"
          }
      ]
  }
  ```

#### Get Nearby Drivers
* **Endpoint**: `GET /api/v1/rider/nearby/?lng=78.48&lat=17.38&radius=1000&count=10`
* **Auth Required**: Yes
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": [
          {
              "driver_id": "2",
              "location": {
                  "latitude": 17.3851,
                  "longitude": 78.4868
              },
              "distance": 0.1234
          }
      ]
  }
  ```

#### Notifications
* **Endpoints**: 
  - `GET /api/v1/rider/notifications/` - List notifications (Paginated)
  - `PATCH /api/v1/rider/notifications/<id>/read/` - Mark single as read
  - `POST /api/v1/rider/notifications/read-all/` - Mark all as read
* **Sample Response (GET)**:
  ```json
  {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
          {
              "id": 1,
              "title": "Ride Accepted",
              "message": "Driver is on the way.",
              "is_read": false,
              "created_at": "2023-10-01T12:00:00Z"
          }
      ]
  }
  ```
* **Sample Response (PATCH / POST)**:
  ```json
  {
      "success": true,
      "data": {
          "message": "Marked as read"
      }
  }
  ```

---

### 🚗 3. Driver Operations (`/driver/`)

#### Driver Earnings
* **Endpoints**: 
  - `GET /api/v1/driver/earnings/?page=1&page_size=10` (Paginated list of trips earnings)
  - `GET /api/v1/driver/earnings/summary/` (Aggregate earnings summary)
* **Auth Required**: Yes (Must be driver)
* **Sample Response (`/earnings/`)**:
  ```json
  {
      "success": true,
      "data": {
          "count": 50,
          "next": "http://.../?page=2",
          "previous": null,
          "results": [
              {
                  "trip_id": 101,
                  "amount": "150.00",
                  "date": "2023-10-01"
              }
          ]
      }
  }
  ```
* **Sample Response (`/summary/`)**:
  ```json
  {
      "success": true,
      "data": {
          "total_earned": "5000.00",
          "total_commission": "1000.00",
          "total_trips": 50,
          "today_earned": "500.00",
          "today_trips": 5,
          "commission_percent": "20"
      }
  }
  ```

#### Vehicle Management
* **List Vehicles**: `GET /api/v1/driver/vehicles/`
* **Add Vehicle**: `POST /api/v1/driver/vehicles/add/`
* **Update Vehicle**: `PATCH /api/v1/driver/vehicles/<id>/`
* **Delete Vehicle**: `DELETE /api/v1/driver/vehicles/<id>/delete/`
* **Auth Required**: Yes
* **Sample Request (Add/Update)**:
  ```json
  {
      "vehicle_number": "TS09ET1234",
      "vehicle_type": "sedan",
      "brand": "Maruti",
      "model": "Dzire",
      "color": "White",
      "year": 2022,
      "capacity": 4
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "id": 1,
          "vehicle_number": "TS09ET1234",
          "vehicle_type": "sedan",
          "brand": "Maruti",
          "model": "Dzire",
          "color": "White",
          "year": 2022,
          "capacity": 4
      }
  }
  ```

---

### 🚖 4. Ride Orchestration (`/ride/`)

#### Estimate Fare
* **Endpoint**: `POST /api/v1/ride/estimate-fare/`
* **Auth Required**: Yes
* **Sample Request**:
  ```json
  {
      "pickup_lat": 17.3850, "pickup_long": 78.4867,
      "destination_lat": 17.4400, "destination_long": 78.3480,
      "distance_km": 12.5, "duration_min": 35,
      "vehicle_type": "sedan"
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "estimated_fare": "150.00",
          "fare_breakdown": {
              "base_fare": "50.00",
              "distance_fare": "80.00",
              "time_fare": "20.00",
              "surge_multiplier": "1.0",
              "min_fare_applied": false
          },
          "vehicle_type": "sedan",
          "pricing_source": "database",
          "distance_km": 12.5,
          "duration_min": 35,
          "straight_line_km": 10.2
      }
  }
  ```

#### Request Ride
* **Endpoint**: `POST /api/v1/ride/ride-request/`
* **Auth Required**: Yes
* **Description**: Creates a new trip entry and estimates fare. Note: drivers are notified via WS from this REST call triggers or WebSockets.
* **Sample Request**:
  ```json
  {
      "pickup_lat": 17.3850, "pickup_long": 78.4867,
      "destination_lat": 17.4400, "destination_long": 78.3480,
      "pickup_address": "Home",
      "destination_address": "Office",
      "distance_km": 12.5,
      "duration_min": 35,
      "vehicle_type": "sedan"
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "trip_id": 101,
          "estimated_fare": "150.00",
          "fare_breakdown": {
              "base_fare": "50.00",
              "distance_fare": "80.00",
              "time_fare": "20.00",
              "surge_multiplier": "1.0"
          },
          "nearby_drivers_count": 3,
          "message": "Ride request created successfully"
      }
  }
  ```

#### Ride History
* **Endpoints**:
  - `GET /api/v1/ride/ride-history/` (Riders)
  - `GET /api/v1/ride/driver-history/` (Drivers)
* **Query Params**: `?status=completed&page=1&page_size=10`
* **Sample Response (Success)**:
  ```json
  {
      "count": 10,
      "next": null,
      "previous": null,
      "results": [
          {
              "id": 101,
              "pickup_address": "Home",
              "destination_address": "Office",
              "status": "completed",
              "estimated_fare": "150.00",
              "requested_at": "2023-10-01T12:00:00Z"
          }
      ]
  }
  ```

#### Trip Details
* **Endpoint**: `GET /api/v1/ride/trip/<trip_id>/`
* **Auth Required**: Yes (Must be participant)
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "id": 101,
          "pickup_lat": "17.385000",
          "pickup_long": "78.486700",
          "destination_lat": "17.440000",
          "destination_long": "78.348000",
          "status": "completed",
          "estimated_fare": "150.00",
          "final_fare": "150.00",
          "fare_breakdown": {
              "base_fare": "50.00",
              "distance_fare": "80.00",
              "time_fare": "20.00"
          },
          "driver": {
              "id": 2,
              "name": "Driver Name",
              "phone": "+919876543211",
              "rating": 4.8
          },
          "vehicle": {
              "number": "TS09ET1234",
              "type": "sedan"
          }
      }
  }
  ```

#### Rate Trip
* **Endpoint**: `POST /api/v1/ride/rate-trip/`
* **Auth Required**: Yes
* **Sample Request**:
  ```json
  {
      "trip_id": 101,
      "score": 5,
      "comments": "Great ride!"
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "rating_id": 1,
          "trip_id": 101,
          "score": 5,
          "comments": "Great ride!",
          "message": "Rating submitted successfully"
      }
  }
  ```

---

### 💳 5. Payments (`/payments/`)

#### Create Order (Razorpay)
* **Endpoint**: `POST /api/v1/payments/create-order/`
* **Auth Required**: Yes
* **Sample Request**:
  ```json
  {
      "trip_id": 101
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "payment_id": 1,
          "razorpay_order_id": "order_xyz123",
          "razorpay_key_id": "rzp_test_abc",
          "amount": "150.00",
          "amount_paise": 15000,
          "currency": "INR",
          "trip_id": 101,
          "description": "Payment for Trip #101",
          "prefill": {
              "name": "John Doe",
              "contact": "+919876543210",
              "email": "johndoe@example.com"
          }
      }
  }
  ```

#### Verify Payment
* **Endpoint**: `POST /api/v1/payments/verify/`
* **Auth Required**: Yes
* **Sample Request**:
  ```json
  {
      "razorpay_order_id": "order_abc",
      "razorpay_payment_id": "pay_def",
      "razorpay_signature": "sig_hex"
  }
  ```
* **Sample Response (Success)**:
  ```json
  {
      "success": true,
      "data": {
          "message": "Payment verified successfully",
          "payment_id": 1,
          "status": "completed",
          "amount": "150.00"
      }
  }
  ```

#### Razorpay Webhook
* **Endpoint**: `POST /api/v1/payments/webhook/`
* **Auth Required**: No (Verified via `X-Razorpay-Signature` header).
* **Description**: Listens to `payment.captured` events to auto-complete payment statuses.

#### Payment History & Refund
* **History**: `GET /api/v1/payments/history/?page=1&page_size=10`
* **Sample Response (History - Success)**:
  ```json
  {
      "count": 5,
      "next": null,
      "previous": null,
      "results": [
          {
              "id": 1,
              "trip_id": 101,
              "amount": "150.00",
              "method": "online",
              "status": "completed",
              "razorpay_order_id": "order_abc",
              "razorpay_payment_id": "pay_def",
              "created_at": "2023-10-01T12:00:00Z"
          }
      ]
  }
  ```
* **Refund**: `POST /api/v1/payments/refund/`
* **Sample Request (Refund)**:
  ```json
  {
      "trip_id": 101
  }
  ```
* **Sample Response (Refund - Success)**:
  ```json
  {
      "success": true,
      "data": {
          "message": "Refund initiated successfully",
          "refund_id": "ref_abc123",
          "amount": "150.00",
          "trip_id": 101
      }
  }
  ```

---

## 📡 WebSocket APIs (Realtime)

### 1. Driver Location Updates
* **Endpoint**: `ws://<host>/ws/driver/location/?token=<jwt>`
* **Direction**: Client (Driver) -> Server
* **Payload**: `{"lng": 78.4867, "lat": 17.3850}`
* **Description**: Continuously streams driver coordinates into Redis Geo-index. Server responds with events and updates trip bounds.

### 2. Ride Request (Rider)
* **Endpoint**: `ws://<host>/ws/ride/request/?token=<jwt>`
* **Description**: Alternative way to request rides and receive driver match updates.
* **Payload from Client**: `{"pickup_lat": ..., "pickup_lng": ..., "destination_lat": ..., "destination_lng": ...}`
* **Events from Server**: `trip_created`, `drivers_notified`, `trip_update`.

### 3. Trip Status Sync (Driver & Rider)
* **Endpoint**: `ws://<host>/ws/ride/trip/<trip_id>/?token=<jwt>`
* **Description**: Both driver and rider join the room to sync trip events.
* **Payloads from Driver**: `{"action": "accept"}`, `{"action": "start"}`, `{"action": "complete"}`, `{"action": "cancel"}`
* **Events from Server**: Broadcasts state changes (`trip_status_update`) immediately to both parties.

---

## 🏗 Data Models (ER Overview)

### 👤 Identity
- **`customUser`**: Root user identity (Fields: `full_name`, `phone_number`, `email`, `role`, `fcm_token`).
- **`Rider`**: 1-to-1 with User. Tracks `rating`.
- **`Driver`**: 1-to-1 with User. Tracks `license_doc`, `status`, `total_trips`, `ratings`.

### 🚗 Vehicle & Fleet
- **`VehicleType`**: Definition of tiers (e.g., hatchback, sedan, suv, auto).
- **`Vehicle`**: Belongs to `Driver`. References `VehicleType`. Contains `vehicle_number`, `brand`, `model`.

### 🗺 Trip & Fare
- **`Trip`**: Core entity connecting User and Driver. Fields: `status_id`, `pickup_lat/long`, `destination_lat/long`, `estimated_fare`, `final_fare`.
- **`TripStatus`**: Static definitions (`accepted`, `in_progress`, `completed`, `cancelled`).
- **`FarePricing`**: 1-to-1 with `Trip`. Breakdown of base fare, distance fare, time fare, surge.
- **`VehicleFarePricing`**: Global dynamic pricing multiplier configurations.
- **`Rating`**: Review entity mapped to trips and raters.

### 💰 Finance
- **`Payment`**: Trip-bound invoice records linking Razorpay meta-data.
- **`TransactionHistory`**: Accounting log mapped to trip, user, driver.
- **`DriverEarning`**: Ledger for individual driver earnings cut/commission per trip.

---

## 🌍 External Integrations
- **AWS SNS**: Integrated for dispatching raw SMS OTP codes securely.
- **Razorpay**: Handles trip order generation and payment capture validation via Webhooks and HMAC signatures.
- **Firebase/FCM**: Integrated for sending silent push notifications directly to devices mapping to user `fcm_token`.

---

## ⚙ Environment Variables Required
```env
# Essential
SECRET_KEY="..."
DEBUG="False"
ALLOWED_HOSTS="*"

# Database
DB_NAME="..."
DB_USER="..."
DB_PASSWORD="..."
DB_HOST="..."
DB_PORT="5432"

# Redis caching and channels
REDIS_URL="redis://redis:6379"

# External API Keys
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION="..."
AWS_SNS_SENDER_ID="..."
RAZORPAY_KEY_ID="..."
RAZORPAY_KEY_SECRET="..."
RAZORPAY_WEBHOOK_SECRET="..."

# Application Rules
PLATFORM_COMMISSION_PERCENT="20"
TRIP_ACCEPT_TIMEOUT_SECONDS="600"
```

---

_Documentation auto-generated using VahanGo's API Source Schema & Models._
