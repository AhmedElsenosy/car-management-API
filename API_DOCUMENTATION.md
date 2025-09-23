# Car Management API Documentation

## Base URL
- Local: `http://localhost:8000/api/`
- Production: `https://your-app.onrender.com/api/`

## API Endpoints

### 1. CREATE a New Car
**Endpoint:** `POST /api/cars/`

**Request Body:**
```json
{
    "car_model": "Toyota Camry 2022",
    "license_start": "2024-01-01",
    "license_end": "2025-01-01"
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "car_model": "Toyota Camry 2022",
    "license_start": "2024-01-01",
    "license_end": "2025-01-01"
}
```

---

### 2. GET ALL Cars
**Endpoint:** `GET /api/cars/`

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "car_model": "Toyota Camry 2022",
        "license_start": "2024-01-01",
        "license_end": "2025-01-01"
    },
    {
        "id": 2,
        "car_model": "Honda Civic 2023",
        "license_start": "2024-02-01",
        "license_end": "2025-02-01"
    }
]
```

---

### 3. GET Car by ID
**Endpoint:** `GET /api/cars/{id}/`

**Example:** `GET /api/cars/1/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "car_model": "Toyota Camry 2022",
    "license_start": "2024-01-01",
    "license_end": "2025-01-01"
}
```

---

### 4. UPDATE Car
**Endpoint:** `PUT /api/cars/{id}/`

**Example:** `PUT /api/cars/1/`

**Request Body:**
```json
{
    "car_model": "Toyota Camry 2023 Updated",
    "license_start": "2024-01-15",
    "license_end": "2025-01-15"
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "car_model": "Toyota Camry 2023 Updated",
    "license_start": "2024-01-15",
    "license_end": "2025-01-15"
}
```

---

### 5. DELETE Car
**Endpoint:** `DELETE /api/cars/{id}/`

**Example:** `DELETE /api/cars/1/`

**Response:** `204 No Content`
```json
{
    "message": "Car deleted successfully"
}
```

---

## Testing with cURL

### Create a car:
```bash
curl -X POST http://localhost:8000/api/cars/ \
  -H "Content-Type: application/json" \
  -d '{"car_model":"BMW X5 2024","license_start":"2024-01-01","license_end":"2025-01-01"}'
```

### Get all cars:
```bash
curl http://localhost:8000/api/cars/
```

### Get car by ID:
```bash
curl http://localhost:8000/api/cars/1/
```

### Update car:
```bash
curl -X PUT http://localhost:8000/api/cars/1/ \
  -H "Content-Type: application/json" \
  -d '{"car_model":"BMW X5 2024 Updated","license_start":"2024-02-01","license_end":"2025-02-01"}'
```

### Delete car:
```bash
curl -X DELETE http://localhost:8000/api/cars/1/
```

---

## Error Responses

### 404 Not Found
```json
{
    "error": "Car not found"
}
```

### 400 Bad Request
```json
{
    "car_model": ["This field is required."],
    "license_start": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]
}
```
