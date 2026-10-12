# REST API Specification

This document details the planned REST API endpoints for the **Supply and Demand Forecasting** backend service.

---

## 1. System Endpoints

### `GET /api/health`
Verifies backend operational status and version.

**Response:**
```json
{
  "status": "healthy",
  "service": "supply-demand-forecasting-backend",
  "version": "0.1.0"
}
```

---

## 2. Ingestion & Schema Endpoints

### `POST /api/v1/datasets/upload`
Uploads a CSV or Excel (`.xlsx`) dataset. Validates file signature, size, row/column bounds, registers it in temporary session storage, and returns metadata with a limited preview. Never returns the full dataset.

**Request:**
- `Content-Type`: `multipart/form-data`
- `file`: Binary file upload (`.csv` or `.xlsx`)

**Response (`201 Created`):**
```json
{
  "dataset_id": "981b18e6-776a-46d2-b235-012ac1af3db8",
  "filename": "retail_demand_2023.csv",
  "file_type": "csv",
  "file_size_bytes": 142500,
  "row_count": 14250,
  "column_count": 5,
  "columns": ["date", "sku_id", "store_id", "units_sold", "unit_price"],
  "dtypes": {
    "date": "datetime",
    "sku_id": "categorical",
    "store_id": "categorical",
    "units_sold": "integer",
    "price": "numeric"
  },
  "preview": [
    {
      "date": "2023-01-01",
      "sku_id": "SKU-101",
      "store_id": "STORE-01",
      "units_sold": 45,
      "unit_price": 12.50
    }
  ],
  "preview_rows_count": 1,
  "created_at": "2026-10-10T11:02:02.521938+00:00",
  "expires_at": "2026-10-10T12:02:02.521938+00:00"
}
```

---

### `GET /api/v1/datasets/{dataset_id}`
Retrieves metadata and preview rows for an active, unexpired dataset session.

---

### `POST /api/schema/map`
Submits confirmed or user-corrected schema mappings for the active session.

**Request (`200 OK`):**
```json
{
  "session_id": "8f8b3c32-2fa1-47fa-8025-fb3510d29ca1",
  "date_column": "date",
  "target_column": "units_sold",
  "item_column": "sku_id",
  "store_column": "store_id",
  "aggregation_frequency": "D"
}
```

**Response (`200 OK`):**
```json
{
  "session_id": "8f8b3c32-2fa1-47fa-8025-fb3510d29ca1",
  "status": "ready",
  "date_range": {
    "start": "2023-01-01",
    "end": "2023-12-31"
  },
  "total_records": 14250,
  "unique_items": 24
}
```

---

## 3. Forecasting & Analytics Endpoints

### `POST /api/forecast/generate`
Trains time-series models and returns forecast horizons along with evaluation metrics.

**Request:**
```json
{
  "session_id": "8f8b3c32-2fa1-47fa-8025-fb3510d29ca1",
  "model_type": "xgboost",
  "horizon_periods": 30,
  "frequency": "D",
  "item_id": "SKU-101",
  "confidence_interval": 0.95
}
```

**Response (`200 OK`):**
```json
{
  "session_id": "8f8b3c32-2fa1-47fa-8025-fb3510d29ca1",
  "model_name": "XGBoost Regressor",
  "horizon_periods": 30,
  "metrics": {
    "mae": 3.42,
    "rmse": 4.88,
    "mape": 8.15
  },
  "forecast": [
    {
      "date": "2024-01-01",
      "predicted_demand": 52.4,
      "lower_bound": 46.1,
      "upper_bound": 58.7
    }
  ]
}
```

---

### `GET /api/analytics/{session_id}`
Retrieves summary statistics, seasonal indicators, and trend breakdowns for the current session.

**Response (`200 OK`):**
```json
{
  "session_id": "8f8b3c32-2fa1-47fa-8025-fb3510d29ca1",
  "summary": {
    "total_demand": 128450,
    "average_daily_demand": 351.9,
    "volatility_score": 0.22
  },
  "seasonality": {
    "peak_day_of_week": "Friday",
    "peak_month": "November"
  }
}
```

---

## 4. Query & Chat Assistant Endpoint

### `POST /api/chat/query`
Processes natural language questions regarding the dataset and forecasts.

**Request:**
```json
{
  "session_id": "8f8b3c32-2fa1-47fa-8025-fb3510d29ca1",
  "query": "What is the expected demand for SKU-101 next week?"
}
```

**Response (`200 OK`):**
```json
{
  "session_id": "8f8b3c32-2fa1-47fa-8025-fb3510d29ca1",
  "in_scope": true,
  "intent": "forecast_inquiry",
  "llm_used": false,
  "response": "The projected demand for SKU-101 over the next 7 days averages 51 units/day, peaking on Friday at 62 units.",
  "data_context": {
    "sku_id": "SKU-101",
    "horizon": 7,
    "expected_total": 357
  }
}
```
