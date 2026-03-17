# VahanGo WebSocket API Documentation

This document provides a comprehensive integration guide for the Frontend applications (Rider and Driver apps) to communicate with the Backend WebSocket consumers based on the `servers/consumers.py` logic.

## Common Overview
- **Authentication**: All WebSocket connections must include a valid JWT token as a query parameter.
  - **Format**: `ws://<host>/ws/.../?token=<jwt_token>`
- **Errors/Rejections**: 
  - Connections with an invalid token drop with `4001` HTTP code.
  - Unauthorized domain access (e.g. non-driver trying to connect to driver socket) will drop with `4003` HTTP code.
  - Unapproved drivers connecting will drop with `4004` HTTP code.

---

## 1. Driver Location WebSocket
**Endpoint**: `ws://<host>/ws/driver/location/?token=<jwt>&lat=<latitude>&lng=<longitude>`
**Purpose**: For drivers to continuously send real-time location telemetry to the system. The server uses this same connection to push incoming ride requests. The initial connection *must* include `lat` and `lng` query parameters or it will be rejected with code `4003`.
**Access**: Only authenticated users with approved `driver` profiles can connect.

### Incoming Messages (Client -> Server)
#### Send Location Update
```json
{
  "lng": 78.4867,
  "lat": 17.3850
}
```

### Outgoing Messages (Server -> Client)

#### 1. Connection Established
```json
{
  "type": "connection_established",
  "message": "Driver <driver_id> connected"
}
```

#### 2. Location Update Confirmation
```json
{
  "type": "location_updated",
  "lng": 78.4867,
  "lat": 17.3850
}
```

#### 3. Ride Request Notification
Received when a nearby rider requests a ride that matches the driver's vehicle. Requires immediate UI response (accept or ignore) which maps to the **Trip Status WebSocket**.
```json
{
  "type": "ride_request",
  "trip_id": 123,
  "rider_name": "John Doe",
  "pickup_lat": "17.385",
  "pickup_lng": "78.486",
  "destination_lat": "17.440",
  "destination_lng": "78.348",
  "pickup_address": "123 Main St",
  "destination_address": "456 Destination Ave",
  "estimated_fare": "150.00"
}
```

#### 4. General Errors
```json
{
  "type": "error",
  "message": "lng and lat are required" // Example message
}
```

---

## 2. Ride Request WebSocket
**Endpoint**: `ws://<host>/ws/ride/request/?token=<jwt>`
**Purpose**: For riders to request new rides, retry searching for drivers, and securely receive initial trip-related notifications (driver found, trip updates) directly to the user's personal communication channel.
**Access**: All authenticated users.

### Incoming Messages (Client -> Server)

#### 1. Request a New Ride
*Note: The `action` key defaults to `"request"` if omitted.*
```json
{
  "action": "request",
  "pickup_lat": 17.385,
  "pickup_lng": 78.486,
  "destination_lat": 17.440,
  "destination_lng": 78.348,
  "pickup_address": "123 Main St",
  "destination_address": "456 Destination Ave",
  "distance_km": 12.5,
  "duration_min": 25,
  "vehicle_type": "bike", // Options map to database types, e.g., "bike", "auto", "car"
  "payment_method": "cash" // Defaults to "cash". E.g., "cash", "online"
}
```

#### 2. Retry Driver Search
Used by the rider app to expand the search scope or retry if the initial broadcast times out with no driver accepting.
```json
{
  "action": "retry",
  "trip_id": 123,
  "radius": 5000 // Optional: Search radius in meters, caps at 5000 max automatically by the server.
}
```

### Outgoing Messages (Server -> Client)

#### 1. Connection Established
```json
{
  "type": "connection_established",
  "message": "Rider connected, ready for ride requests"
}
```

#### 2. Trip Created Confirmation
```json
{
  "type": "trip_created",
  "trip_id": 123,
  "estimated_fare": "150.00",
  "message": "Searching for nearby drivers..."
}
```

#### 3. Drivers Notified (Search Started)
```json
{
  "type": "drivers_notified",
  "trip_id": 123,
  "drivers_notified": 3,
  "message": "3 nearby driver(s) notified" // message string may change based on action (request/retry)
}
```

#### 4. No Drivers Found
Returned if the initial or subsequent backend geo-search returns zero available online drivers.
```json
{
  "type": "no_drivers",
  "trip_id": 123,
  "message": "No nearby drivers found. Please try again shortly."
}
```

#### 5. Retry Started Confirmation
```json
{
  "type": "retry_started",
  "trip_id": 123,
  "radius": 5000,
  "message": "Retrying — searching for nearby drivers..."
}
```

#### 6. Trip Status Updates (`trip_update`)
Pushed to the specific rider whenever the state of the trip progresses (Accept -> Reached -> Start -> Complete/Cancel).

**When Accepted By Driver:**
```json
{
  "type": "trip_update",
  "trip_id": 123,
  "status": "accept",
  "message": "Trip accepted",
  "driver_id": 45,
  "driver_name": "Driver Name",
  "otp": "123456", // Sent exclusively upon acceptance for rider to provide to driver
  "driver_info": {
    "name": "Jane Doe",
    "id": 45,
    "phone_number": "+1234567890",
    "stars": "4.8"
  },
  "vehicle_info": {
    "model": "Model S",
    "brand": "Tesla",
    "vehicle_number": "ABC-1234",
    "color": "Black"
  }
}
```
**When Reached / Started / Completed / Cancelled:**
```json
{
  "type": "trip_update",
  "trip_id": 123,
  "status": "reached", // Alternates: "start", "complete", "cancel"
  "message": "Trip reached", // Maps to server description of the status update
  "driver_id": 45,
  "driver_name": "Jane Doe"
}
```

#### 7. Live Driver Location Broadcast (`driver_location_update`)
Received rapidly whenever the assigned driver moves during an ongoing active trip (bridged automatically from `DriverLocationConsumer`).
```json
{
  "type": "driver_location_update",
  "lng": 78.486,
  "lat": 17.385,
  "driver_id": 45
}
```

#### 8. Errors
```json
{
  "type": "error",
  "message": "<Error string detail>"
}
```

---

## 3. Trip Status WebSocket
**Endpoint**: `ws://<host>/ws/ride/trip/<trip_id>/?token=<jwt>`
**Purpose**: For localized real-time updates bound to a specific assigned active trip. **Both the rider and driver should connect** to this channel once a trip transitions from unassigned to assigned/in-progress. *A driver clicks the notification of a ride request, connects to this view, then sends `{"action": "accept"}`.*
**Access**: Only the original Rider of the trip, the specifically assigned Driver, or *any* Driver (only before the trip has an assigned driver).

### Incoming Messages (Client -> Server)

#### 1. Accept Trip (Allowed: Driver Only)
```json
{
  "action": "accept"
}
```

#### 2. Reached Pickup Location (Allowed: Assigned Driver Only)
```json
{
  "action": "reached"
}
```

#### 3. Start Trip (Allowed: Assigned Driver Only)
*Requires the OTP provided by the rider during acceptance.*
```json
{
  "action": "start",
  "otp": "123456"
}
```

#### 4. Complete Trip (Allowed: Assigned Driver Only)
```json
{
  "action": "complete"
}
```

#### 5. Cancel Trip (Allowed: Both Diver and Rider)
```json
{
  "action": "cancel"
}
```

### Outgoing Messages (Server -> Client)

#### 1. Connection Established
```json
{
  "type": "connection_established",
  "trip_id": 123,
  "message": "Connected to trip updates"
}
```

#### 2. Trip Status Broadcasts (`trip_status_update`)
Broadcast out to all individuals observing the trip whenever an action command passes validation logically.

**When Accepted By a Driver:**
```json
{
  "type": "trip_status_update",
  "trip_id": 123,
  "status": "accept",
  "message": "Trip accepted",
  "driver_id": 45,
  "otp": "123456",
  "driver_info": {
    "name": "Jane Doe",
    "id": 45,
    "phone_number": "+1234567890",
    "stars": "4.8"
  },
  "vehicle_info": {
    "model": "Model S",
    "brand": "Tesla",
    "vehicle_number": "ABC-1234",
    "color": "Black"
  }
}
```

**When Reached / Started / Completed / Cancelled:**
```json
{
  "type": "trip_status_update",
  "trip_id": 123,
  "status": "reached", // Alternates: "start", "complete", "cancel"
  "message": "Trip reached",
  "driver_id": 45
}
```

#### 3. Live Driver Location Broadcast (`driver_location_update`)
Visible continuously to the Rider reflecting the Driver's telemetry via this group as well.
```json
{
  "type": "driver_location_update",
  "lng": 78.486,
  "lat": 17.385,
  "driver_id": 45
}
```

#### 4. State Transition Errors
Returned safely over Websockets if a client requests an action sequence incorrectly (example: attempting to `"start"` a `"cancelled"` ride) or if another driver already snapped up the ride request.
```json
{
  "type": "error",
  "message": "Invalid status transition: cannot change from accepted to completed"
}
```
*Note: Possible transitional logic errors strings: "Trip is already cancelled", "Trip already accepted by another driver", "Only drivers can accept rides".*
