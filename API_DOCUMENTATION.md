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

---

# Daily & Weekly Operations

## Create Daily Entry
- Endpoint: `POST /api/daily-entries/`
- Description: Add a daily record for a car. Week is derived (Saturday→Friday) from `inspection_date`.
- Required fields: `car_id`, `inspection_date`, `day_name`, `driver_name`
- Optional numeric fields default to 0: `freight, default_freight, gas, oil, card, fines, tips, maintenance, spare_parts, tires, balance, washing, without`

Request body
```json
{
  "car_id": 2,
  "inspection_date": "2025-10-02",
  "day_name": "Thursday",
  "driver_name": "Ahmed",
  "area": "Nasr City",
  "freight": 1000,
  "default_freight": 800,
  "gas": 200,
  "oil": 50,
  "card": 0,
  "fines": 0,
  "tips": 0,
  "maintenance": 0,
  "spare_parts": 0,
  "tires": 0,
  "balance": 0,
  "washing": 20,
  "without": 30
}
```

Response: `201 Created` (returns created daily entry with computed `week_start`).

---

## Create/Upsert Weekly Summary
- Endpoint: `POST /api/weekly/`
- Description: Create or update the weekly summary for a car. Provide any date in the target week via `week_ref_date`. The backend computes `week_start`/`week_end`, totals, `net_expenses`, and `net_revenue`.
- Required: `car_id`, `week_ref_date`, `odometer_start`, `odometer_end`
- Optional: `driver_salary`, `custody`, `description`

Request body
```json
{
  "car_id": 2,
  "week_ref_date": "2025-10-02",
  "odometer_start": 50000,
  "odometer_end": 51000,
  "driver_salary": 1000,
  "custody": 1800,
  "description": "Weekly notes here."
}
```

Response: `201 Created` (returns weekly detail payload).

---

## Get Weekly Detail
- Endpoint: `GET /api/weekly/detail/?car_id={id}&date=YYYY-MM-DD`
- Description: Returns weekly report (Saturday→Friday week for `date`), including:
  - `week_start`, `week_end`
  - `odometer_start`, `odometer_end`, `distance`, `gas_per_km`
  - `driver_salary`, `custody`, `description`
  - `net_expenses` (sum of weekly expenses + driver_salary)
  - `net_revenue` = (sum `freight` + `custody`) − `net_expenses`
  - `default_net_revenue` = (sum `default_freight` + `custody`) − `net_expenses`
  - `totals`: per-column sums (freight, default_freight, gas, oil, card, fines, tips, maintenance, spare_parts, tires, balance, washing, without)
  - `daily_entries`: all daily rows for that week

Example
```
GET /api/weekly/detail/?car_id=2&date=2025-10-02
```

---

## Get Monthly Detail
- Endpoint: `GET /api/monthly/detail/?car_id={id}&year=YYYY&month=MM`
- Description: Monthly summary per car, built from weekly summaries and daily entries in the calendar month.
  - `odometer_start`: from the first weekly summary in the month
  - `odometer_end`: from the last weekly summary in the month
  - `distance_total`: sum of weekly distances (each `odometer_end - odometer_start`, floored at 0)
  - `gas_total`: sum of `gas` across all daily entries in the month
  - `gas_per_km`: `gas_total / distance_total` (0 if distance is 0)
  - Totals included: `driver_salary_total`, `custody_total`, `net_expenses_total`, `net_revenue_total`, `default_net_revenue_total`

Computation notes
- For each week in the month, monetary values are recomputed from DailyEntry rows (not taken from stored weekly fields):
  - weekly_expenses = gas + oil + card + fines + tips + maintenance + spare_parts + tires + balance + washing + without + driver_salary
  - weekly_net_revenue = (sum freight + custody) − weekly_expenses
  - weekly_default_net_revenue = (sum default_freight + custody) − weekly_expenses
- The monthly totals (net_expenses_total, net_revenue_total, default_net_revenue_total) are the sums of these weekly values.
- gas_total comes from summing DailyEntry.gas across the calendar month.

Example
```
GET /api/monthly/detail/?car_id=2&year=2025&month=10
```

Response fields
- `car_id, year, month, period_start, period_end`
- `odometer_start, odometer_end, distance_total, gas_total, gas_per_km`
- `driver_salary_total, custody_total, net_expenses_total, net_revenue_total, default_net_revenue_total`
- `weeks`: array of week objects with `week_start, week_end, odometer_start, odometer_end, distance, driver_salary, custody, net_expenses, net_revenue, default_net_revenue`

---

## Update Daily Entry by Date
- Endpoint: `PUT|PATCH /api/daily-entries/by-date/`
- Description: Update a unique daily entry identified by `(car_id, inspection_date)`.
- Required in body: `car_id`, `inspection_date` (YYYY-MM-DD)
- Provide any fields you want to change (partial updates allowed): e.g., `freight, gas, oil, card, fines, tips, maintenance, spare_parts, tires, balance, washing, without, day_name, driver_name, area`.

Request body (example)
```json
{
  "car_id": 2,
  "inspection_date": "2025-10-02",
  "freight": 1200,
  "gas": 210,
  "without": 25,
  "day_name": "Thursday"
}
```

Responses
- `200 OK` with updated daily entry
- `404 Not Found` if no daily entry exists for `(car_id, inspection_date)`
- `400 Bad Request` if more than one entry exists for that date (then update by ID instead)

---

## Update Weekly Summary by Date
- Endpoint: `PUT|PATCH /api/weekly/by-date/`
- Description: Update a weekly summary identified by `(car_id, week_ref_date)` where `week_ref_date` is any date inside the target week (Saturday→Friday). Updates allowed for: `odometer_start`, `odometer_end`, `driver_salary`, `custody`, `description`.
- Required in body: `car_id`, `week_ref_date` (YYYY-MM-DD)

Request body (example)
```json
{
  "car_id": 2,
  "week_ref_date": "2025-10-02",
  "odometer_end": 51050,
  "driver_salary": 1100,
  "description": "Adjusted salary and custody; extra trips on Thu."
}
```

Response
- `200 OK` with the refreshed weekly detail payload (includes corrected `week_end = week_start + 6`).

---

# Vehicle Maintenance Operations

## Create Maintenance Entry
- **Endpoint:** `POST /api/maintenance/`
- **Description:** Add a daily maintenance record for a car. All money fields default to 0.00 if not provided.
- **Required fields:** `car_id`, `date`
- **Money fields:** `air_filter`, `oil_filter`, `gas_filter`, `oil_change`, `price`
- **Optional fields:** `spare_part_type`

**Request Body:**
```json
{
  "car_id": 2,
  "date": "2025-10-06",
  "air_filter": 120.50,
  "oil_filter": 80.00,
  "gas_filter": 45.75,
  "oil_change": 300.00,
  "price": 50.25,
  "spare_part_type": "Oil Change + All Filters"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "car_id": 2,
  "date": "2025-10-06",
  "air_filter": "120.50",
  "oil_filter": "80.00",
  "gas_filter": "45.75",
  "oil_change": "300.00",
  "price": "50.25",
  "spare_part_type": "Oil Change + All Filters"
}
```

---

## Update Maintenance Entry by Date
- **Endpoint:** `PUT|PATCH /api/maintenance/by-date/`
- **Description:** Update a maintenance record identified by `(car_id, date)`.
- **Required in body:** `car_id`, `date` (YYYY-MM-DD)
- **Optional fields to update:** `air_filter`, `oil_filter`, `gas_filter`, `oil_change`, `price`, `spare_part_type`

**Request Body (Partial Update Example):**
```json
{
  "car_id": 2,
  "date": "2025-10-06",
  "price": 65.00,
  "spare_part_type": "Updated: Oil Change Only"
}
```

**Responses:**
- `200 OK` with updated maintenance entry
- `404 Not Found` if no maintenance entry exists for `(car_id, date)`
- `400 Bad Request` if multiple entries exist for that date or invalid data format

---

## Get Yearly Maintenance Table
- **Endpoint:** `GET /api/maintenance/year/?car_id={id}&year=YYYY`
- **Description:** Returns all maintenance entries for a car in the specified year, plus monthly totals and yearly totals.
- **Query Parameters:** `car_id` (required), `year` (required, YYYY format)

**Example Request:**
```
GET /api/maintenance/year/?car_id=2&year=2025
```

**Response:** `200 OK`
```json
{
  "car_id": 2,
  "year": 2025,
  "entries": [
    {
      "id": 1,
      "car_id": 2,
      "date": "2025-10-06",
      "air_filter": "120.50",
      "oil_filter": "80.00",
      "gas_filter": "45.75",
      "oil_change": "300.00",
      "price": "50.25",
      "spare_part_type": "Oil Change + All Filters"
    }
  ],
  "monthly_totals": [
    {
      "month": 1,
      "air_filter": 0,
      "oil_filter": 0,
      "gas_filter": 0,
      "oil_change": 0,
      "price": 0,
      "full_total": 0
    },
    {
      "month": 10,
      "air_filter": 120.50,
      "oil_filter": 80.00,
      "gas_filter": 45.75,
      "oil_change": 300.00,
      "price": 50.25,
      "full_total": 596.50
    }
  ],
  "yearly_totals": {
    "air_filter": 120.50,
    "oil_filter": 80.00,
    "gas_filter": 45.75,
    "oil_change": 300.00,
    "price": 50.25,
    "full_total": 596.50
  }
}
```

**Notes:**
- `monthly_totals`: Array of 12 objects (months 1-12) with totals for each month
- `yearly_totals`: Sum of all money fields across the entire year
- `full_total`: Sum of all 5 money fields (air_filter + oil_filter + gas_filter + oil_change + price)
- All money fields are returned as decimal strings

---

## Testing Maintenance Endpoints with cURL

### Create a maintenance entry:
```bash
curl -X POST http://localhost:8000/api/maintenance/ \
  -H "Content-Type: application/json" \
  -d '{"car_id":2,"date":"2025-10-06","air_filter":120.50,"oil_filter":80.00,"oil_change":300.00,"price":50.25,"spare_part_type":"Oil Change + Filters"}'
```

### Update maintenance entry by date:
```bash
curl -X PATCH http://localhost:8000/api/maintenance/by-date/ \
  -H "Content-Type: application/json" \
  -d '{"car_id":2,"date":"2025-10-06","price":65.00,"spare_part_type":"Updated: Oil Change Only"}'
```

### Get yearly maintenance table:
```bash
curl "http://localhost:8000/api/maintenance/year/?car_id=2&year=2025"
```
