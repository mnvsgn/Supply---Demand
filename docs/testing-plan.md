# Testing Plan & Strategy

This document outlines the testing strategy, test suites, and validation criteria for the **Supply and Demand Forecasting** monorepo.

---

## 1. Testing Philosophy

1. **Deterministic Core**: All data processing, feature engineering, and model training pipelines must be thoroughly tested with synthetic fixture data.
2. **Graceful Degradation**: Natural-language and intelligence features must have dedicated fallback tests verifying complete functionality when an external LLM is disabled or unavailable.
3. **Session Isolation**: Tests must verify that session-based datasets do not leak state between requests.

---

## 2. Backend Automated Test Suites (`backend/tests/`)

### `test_upload.py`
- **File Validation**:
  - Accept valid `.csv` and `.xlsx` files.
  - Reject unsupported extensions (e.g., `.pdf`, `.json`, `.exe`).
  - Reject files exceeding the maximum size limit (`MAX_UPLOAD_SIZE_MB`).
  - Handle corrupt or empty files gracefully with clear error responses.
- **Session Creation**:
  - Verify assignment of a unique `session_id` and initial caching in memory.

### `test_schema_mapping.py`
- **Column Detection**:
  - Correctly identify dates in standard formats (`YYYY-MM-DD`, `DD/MM/YYYY`, ISO-8601).
  - Infer target demand columns (`units_sold`, `demand`, `sales`).
  - Detect categorical entity keys (`sku`, `store_id`).
- **Data Normalization**:
  - Handle missing days via zero-fill or interpolation.
  - Reject datasets missing both timestamp and target metrics.

### `test_forecasting.py`
- **Feature Engineering**:
  - Correctly generate lag variables ($t-1, t-7$) and rolling averages without data leakage.
- **Model Pipelines**:
  - Fit baseline models (moving average, naive).
  - Train `scikit-learn` regressor and `XGBoost` model.
  - Confirm prediction outputs match the requested forecast horizon length.
- **Metrics Calculation**:
  - Verify mathematical accuracy of MAE, RMSE, and MAPE calculations.

### `test_intent.py`
- **Domain Restriction**:
  - Verify that out-of-scope prompts (e.g., "Write me a poem", "What is the capital of France?") receive appropriate formal scope rejection.
  - Verify that legitimate inventory queries (e.g., "Forecast next month for SKU-101") pass domain validation.
- **LLM Fallback**:
  - Verify that when `LLM_ENABLED=False`, deterministic rule-based responses are produced.

### `test_api.py`
- **API Routing & Health**:
  - Validate `GET /api/health` returns status `200` with expected payload.
  - Verify CORS middleware headers allow configured frontend origins.
  - Validate proper HTTP status codes on missing sessions (`404`) and bad inputs (`422`).

---

## 3. Test Execution Instructions

Run all backend tests with Pytest:

```bash
cd backend
pytest -v
```

Run specific test modules:
```bash
pytest tests/test_api.py -v
pytest tests/test_forecasting.py -v
```
