# 📘 VahanGo API Documentation (v2)

This documentation provides a comprehensive guide to the VahanGo ride-hailing backend service built with Django and Django REST Framework (DRF).

---

## 🏗 Architecture Summary
- **Framework**: Django & Django REST Framework
- **Real-Time / WebSockets**: Django Channels (Redis ASGI backend)
- **Database**: PostgreSQL
- **Background Tasks**: Celery / Redis Queue (for OTP, ride lifecycle events, earning calculation)
- **Authentication**: JWT (JSON Web Tokens) via SimpleJWT
- **External Integrations**:
  - **AWS SNS / Twilio**: SMS OTP Dispatch
  - **Razorpay**: Payment Gateway for Trip Fares
  - **Firebase Cloud Messaging (FCM)**: Push Notifications

---

## 🔐 Authentication & Security

- **Type**: Bearer Token (JWT).
- **Header**: `Authorization: Bearer <access_token>`
- **Flow**: Phone Number -> OTP -> JWT (Access & Refresh Tokens).
- **Roles**: Users are created with a specific role (`rider`, `driver`, `admin`).
- **WebSockets Security**: Token passed via query parameters `ws://...?token=<jwt>` and verified in ASGI middleware before accepting connection.

---

## 🌐 Base URLs
- **HTTP**: `https://<domain>/api/v1/`
- **WS**: `ws://<domain>/`

---

## 🚀 REST API Endpoints

### 👤 1. Authentication (`/auth/`)

#### 1.1 Request OTP
Initiates login or signup by sending an OTP to the user's phone number.
- **Endpoint**: `POST /auth/otp/`
- **Auth**: None
- **Request Body**:
  ```json
  {
      "phone_number": "+919876543210",
      "role": "rider"  // Options: "rider", "driver", "admin"
  }
  ```
- **Response** (200 OK):
  ```json
  {
      "success": true,
      "data": {
          "message": "OTP sent successfully",
          "task_id": "uuid-for-tracking",
          "expires_in": 600
      }
  }
  ```

#### 1.2 Verify OTP & Login
Completes authentication and provisions JWT tokens.
- **Endpoint**: `POST /auth/login/`
- **Auth**: None
- **Request Body**:
  ```json
  {
      "phone_number": "+919876543210",
      "otp": "123456",
      "device_token": "fcm_device_token_string"
  }
  ```
- **Response** (200 OK):
  ```json
  {
      "success": true,
      "data": {
          "token": "eyJhbG...",
          "refresh_token": "eyJhbG...",
          "user": {
              "id": 1,
              "full_name": null,
              "phone_number": "+919876543210",
              "role": "rider"
          }
      }
  }
  ```

#### 1.3 Refresh Token
Exchanges a valid refresh token for a new access token.
- **Endpoint**: `POST /auth/refresh/`
- **Auth**: None
- **Request Body**:
  ```json
  {
      "refresh_token": "eyJhbG..."
  }
  ```

#### 1.4 Update User Profile
- **Endpoint**: `PATCH /auth/update/`
- **Auth**: Required
- **Request Body** (All fields optional):
  ```json
  {
      "full_name": "John Doe",
      "email": "john.doe@example.com",
      "gender": "male",
      "dob": "1990-01-01",
      "house_no": "A-12",
      "street": "MG Road",
      "city": "Hyderabad",
      "zip_code": "500001",
      "emergency_contact": "+919876543211",
      "avatar": "https://bucket.s3.amazonaws.com/avatar.png"
  }
  ```

---

### 🛵 2. Rider Operations (`/rider/`)

#### 2.1 Save Favorite Location
- **Endpoint**: `POST /rider/locations/`
- **Auth**: Required (Rider)
- **Request Body**:
  ```json
  {
      "address_text": "Home",
      "latitude": 17.385000,
      "longitude": 78.486700
  }
  ```

#### 2.2 Get Favorite Locations
- **Endpoint**: `GET /rider/locations/all/`
- **Auth**: Required (Rider)

#### 2.3 Get Nearby Drivers
- **Endpoint**: `GET /rider/nearby/?lat=17.3850&lng=78.4867&radius=5&count=10`
- **Auth**: Required (Rider)
- **Response** (200 OK):
  ```json
  {
      "success": true,
      "data": [
          {
              "driver_id": "2",
              "location": {
                  "latitude": 17.3860,
                  "longitude": 78.4870
              },
              "distance": 0.5
          }
      ]
  }
  ```

#### 2.4 Notifications
- List: `GET /rider/notifications/`
- Mark Read: `PATCH /rider/notifications/{id}/read/`
- Mark All Read: `POST /rider/notifications/read-all/`

---

### 🚗 3. Driver Operations (`/driver/`)

#### 3.1 Driver Earnings
- **List**: `GET /driver/earnings/?page=1&page_size=10`
- **Summary**: `GET /driver/earnings/summary/`
- **Summary Response** (200 OK):
  ```json
  {
      "success": true,
      "data": {
          "total_earned": "15000.00",
          "total_commission": "3000.00",
          "total_trips": 120,
          "today_earned": "1200.00",
          "today_trips": 8,
          "commission_percent": "20"
      }
  }
  ```

#### 3.2 Vehicle Management
- **List**: `GET /driver/vehicles/`
- **Add**: `POST /driver/vehicles/add/`
  ```json
  {
      "vehicle_number": "TS09EA1234",
      "vehicle_type": "sedan",
      "brand": "Maruti Suzuki",
      "model": "Dzire",
      "color": "White",
      "year": 2022,
      "capacity": 4
  }
  ```
- **Update**: `PATCH /driver/vehicles/{id}/`
- **Delete**: `DELETE /driver/vehicles/{id}/delete/`

---

### 🚖 4. Ride Orchestration (`/ride/`)

#### 4.1 Estimate Fare
- **Endpoint**: `POST /ride/estimate-fare/`
- **Auth**: Required
- **Request Body**:
  ```json
  {
      "pickup_lat": 17.3850, "pickup_long": 78.4867,
      "destination_lat": 17.4400, "destination_long": 78.3480,
      "distance_km": 12.5,
      "duration_min": 35,
      "vehicle_type": "sedan"
  }
  ```
- **Response** (200 OK):
  ```json
  {
      "success": true,
      "data": {
          "estimated_fare": "250.00",
          "fare_breakdown": {
              "base_fare": "50.00",
              "distance_fare": "150.00",
              "time_fare": "50.00",
              "surge_multiplier": "1.0",
              "total_fare": "250.00"
          },
          "vehicle_type": "sedan"
      }
  }
  ```

#### 4.2 Ride History
- **Rider**: `GET /ride/ride-history/?status=completed&page=1`
- **Driver**: `GET /ride/driver-history/?status=completed&page=1`
- **Detail**: `GET /ride/trip/{id}/` (Returns full fare breakdown and ratings)

#### 4.3 Rate Trip
- **Endpoint**: `POST /ride/rate-trip/`
- **Auth**: Required
- **Request Body**:
  ```json
  {
      "trip_id": 101,
      "score": 5,
      "comments": "Excellent driver, very polite."
  }
  ```

---

### 💳 5. Payments (`/payments/`)

#### 5.1 Create Razorpay Order
- **Endpoint**: `POST /payments/create-order/`
- **Auth**: Required (Rider)
- **Request Body**: `{"trip_id": 101}`
- **Response** (201 Created):
  ```json
  {
      "success": true,
      "data": {
          "payment_id": 1,
          "razorpay_order_id": "order_xyz",
          "amount_paise": 25000,
          "currency": "INR",
          "prefill": {
              "name": "John Doe",
              "contact": "+919876543210"
          }
      }
  }
  ```

#### 5.2 Verify Payment (Client-Side)
- **Endpoint**: `POST /payments/verify/`
- **Auth**: Required
- **Request Body**:
  ```json
  {
      "razorpay_order_id": "order_xyz",
      "razorpay_payment_id": "pay_abc",
      "razorpay_signature": "hex_signature"
  }
  ```

#### 5.3 Razorpay Webhook
- **Endpoint**: `POST /payments/webhook/`
- **Auth**: None (Verified via `X-Razorpay-Signature` header)
- **Supported Events**: `payment.captured`

#### 5.4 Refund Payment
- **Endpoint**: `POST /payments/refund/`
- **Auth**: Required (Rider)
- **Request Body**: `{"trip_id": 101}`

---

## 📡 Real-Time WebSockets APIs

### 1. Driver Location Updates
- **Endpoint**: `ws://<domain>/ws/driver/location/?token=<jwt>`
- **Role**: Driver
- **Payload IN**: `{"lng": 78.4867, "lat": 17.3850}`
- **Behavior**: Streams location to Redis Geo-spatial index.

### 2. Ride Request & Dispatch
- **Endpoint**: `ws://<domain>/ws/ride/request/?token=<jwt>`
- **Role**: Rider
- **Payload IN**: Create trip
  ```json
  {
      "pickup_lat": 17.385, "pickup_lng": 78.486,
      "destination_lat": 17.440, "destination_lng": 78.348,
      "pickup_address": "Home", "destination_address": "Office",
      "vehicle_type": "sedan",
      "distance_km": 12.5, "duration_min": 35
  }
  ```
- **Events OUT**: `trip_created`, `drivers_notified`

### 3. Trip Status Synchronization
- **Endpoint**: `ws://<domain>/ws/ride/trip/<trip_id>/?token=<jwt>`
- **Role**: Driver & Rider
- **Payload IN (Driver)**: `{"action": "accept" | "arrive" | "start" | "complete" | "cancel"}`
- **Events OUT**: Broadcasts `trip_status_update` to both parties.

---

## 🗃️ Database Models Overview (ERD)

- **`customUser`**: Base user with `role` (rider, driver, admin).
- **`Rider`**: Tied 1:1 to User. Aggregates rating.
- **`Driver`**: Tied 1:1 to User. Tracks `status`, `ratings`, `total_trips`.
- **`Vehicle`**: Vehicles owned by Driver. Tied to `VehicleType` (Pricing tier).
- **`Trip`**: Core transactional record mapping Rider, Driver, Vehicle, and Locations.
- **`TripStatus`**: Enum for ride states (`accepted`, `in_progress`, etc.).
- **`FarePricing`**: 1:1 with Trip. Granular breakdown of fares.
- **`Payment`**: Invoice and Gateway IDs representing a charge to a rider.
- **`DriverEarning`**: Ledger representation of the driver's cut for a completed trip.

---
_Auto-generated by AI Documentation Generator Workflow._
