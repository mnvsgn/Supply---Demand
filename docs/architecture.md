# System Architecture

## 1. Overview

The **Supply and Demand Forecasting** application is an end-to-end machine learning platform tailored for business demand planning and inventory optimization. The architecture couples a responsive client application with a modular FastAPI service designed around temporary, session-based datasets.

```text
+-----------------------------------------------------------------------------------------+
|                                      USER BROWSER                                       |
|  +-----------------------------------------------------------------------------------+  |
|  |                                  React Frontend                                   |  |
|  |  [Layout & Navigation]  [Upload Wizard]  [Schema Mapper]  [Forecast & Analytics]  |  |
|  |                            [Natural Language Assistant]                           |  |
|  +-----------------------------------------+-----------------------------------------+  |
+--------------------------------------------|--------------------------------------------+
                                             | HTTP / REST (JSON & Multipart)
                                             v
+-----------------------------------------------------------------------------------------+
|                                    FASTAPI BACKEND                                      |
|                                                                                         |
|  +---------------------+   +---------------------+   +-------------------------------+  |
|  |   API Route Layer   |-->|   Pydantic DTOs     |-->|     Service Orchestrator      |  |
|  +---------------------+   +---------------------+   +---------------+---------------+  |
|                                                                      |                  |
|          +----------------------------+------------------------------+                  |
|          |                            |                              |                  |
|          v                            v                              v                  |
|  +---------------+            +---------------+            +--------------------+       |
|  | Data Pipeline |            | ML Engine     |            | Intelligence Layer |       |
|  | - Validation  |            | - Baselines   |            | - Domain Filter    |       |
|  | - Profiling   |            | - Sklearn     |            | - Intent Parser    |       |
|  | - Schema Map  |            | - XGBoost     |            | - Optional LLM     |       |
|  | - Normalizer  |            | - Evaluation  |            |   (Fallback Rules) |       |
|  +-------+-------+            +-------+-------+            +--------------------+       |
|          |                            |                                                 |
|          +----------------------------+                                                 |
|                                       v                                                 |
|                    +-------------------------------------+                              |
|                    |   Temporary Session Store (In-Mem)  |                              |
|                    |   (No External Database in v1)      |                              |
|                    +-------------------------------------+                              |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Frontend Architecture (`frontend/`)

Built with React, Vite, Tailwind CSS, and Recharts.

### Key Modules:
- **`components/upload/`**: Handles drag-and-drop file upload, file format/size checks, previewing table data, and displaying schema mapping configuration.
- **`components/forecast/`**: Configures forecasting horizon (e.g., 7 days, 30 days, 90 days), model selection (Baseline, Random Forest, XGBoost), and renders time-series Recharts visualizations with prediction intervals.
- **`components/chat/`**: Provides an interactive natural-language prompt interface for users to ask supply/demand questions against their active dataset session.
- **`components/layout/`**: Shared UI scaffolding (navigation header, sidebar, session indicator, notifications).
- **`services/`**: Encapsulates Axios/Fetch HTTP calls to the backend endpoints (`api.js`, `forecastService.js`, `uploadService.js`).
- **`context/`**: Manages React context for the active dataset session, schema mappings, and query history.

---

## 3. Backend Architecture (`backend/app/`)

The backend is built around FastAPI, following a layered, decoupled design pattern:

### 3.1. API & Schema Layers
- **`api/routes/`**: Exposes thin REST endpoint handlers for uploading datasets, confirming schema mappings, running forecasts, and processing queries.
- **`schemas/`**: Pydantic models guaranteeing type safety and request/response validation.

### 3.2. Data Processing Pipeline (`data_processing/`)
- **File Validation**: Accepts `.csv` and `.xlsx` files up to a defined size threshold.
- **Schema Detection**: Examines column names and data types to infer timestamps, demand/sales volume, product identifiers (SKUs), and geographic/store segments.
- **Normalization**: Handles date parsing, missing value interpolation, aggregation at consistent time grains (daily, weekly, monthly), and zero-filling for non-sale intervals.

### 3.3. Forecasting & Evaluation Engine (`forecasting/`, `evaluation/`)
- **Model Implementations**:
  - *Baseline*: Naive, Moving Average, Exponential Smoothing.
  - *Linear & Tree-Based*: Ridge Regression, Random Forest (via `scikit-learn`).
  - *Gradient Boosting*: `XGBoost` for non-linear lag-feature regression.
- **Feature Engineering**: Time lags, rolling means, seasonal indicators (day of week, month, holidays).
- **Evaluation**: Calculates Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Absolute Percentage Error (MAPE) against a hold-out test set.

### 3.4. Analytics Engine (`analytics/`)
- Extracts descriptive insights: historical growth rate, seasonal indices, stockout risk indicators, and product volatility categorization (ABC/XYZ analysis).

### 3.5. Intelligence & Optional LLM Layer (`intelligence/`)
- **Domain Restriction**: Enforces that user queries pertain strictly to supply chain, demand forecasting, inventory, and dataset statistics. Out-of-scope queries receive standard formal boundaries.
- **Rule-Based Intent Parser**: Extracts target metrics, SKU filters, and time horizons using rule patterns without relying on an external network connection.
- **Optional LLM Integration**: When configured with an API key, passes structured intent and summary metrics to an LLM provider for richer narrative explanations. When unconfigured, the application functions seamlessly via deterministic templates.

### 3.6. Temporary Session Storage & Lifecycle (`services/session_manager.py`)
- **No Login / No Database in v1**: User sessions are established anonymously with cryptographically unguessable, 256-bit entropy session tokens (`sess_<token>`).
- **Session Isolation & Ownership**: Datasets, schema mappings, and conversation histories are strictly scoped to the originating session. Users cannot access, map, or forecast another session's dataset by guessing or modifying identifiers.
- **Configurable Expiration & Cleanup**: Sessions expire after an idle timeout (default: 30 minutes) or absolute TTL (default: 60 minutes). Expired sessions are evicted from memory and their associated storage directories and artifacts are purged from disk.
- **Modular Storage Interface**: Built upon `BaseSessionStore` so persistent storage backends (Redis, PostgreSQL, S3) can be plugged in without refactoring forecasting or preprocessing services.

#### Multi-Worker Deployment Limitations (Important):
Because the initial local architecture uses an `InMemorySessionStore`:
1. **Process Isolation**: In deployments with multiple worker processes (e.g. Uvicorn/Gunicorn with `--workers > 1`) or distributed replicas (Kubernetes pods), RAM is not shared across processes. A request routed to a different worker than the one that created the session will encounter a `404 Session Not Found` unless the load balancer enforces sticky sessions (session affinity).
2. **Worker Recycling & Restarts**: Restarting worker processes flushes active in-memory session states.
3. **Horizontal Scaling**: Scaling horizontally requires transitioning from `InMemorySessionStore` to a centralized session store (e.g., Redis for metadata and S3/MinIO for dataset artifacts).

