# Supply and Demand Forecasting — Directory Responsibilities

This document provides a breakdown of the repository structure and explains the specific responsibilities of each major directory and module in the project.

---

## 1. Monorepo Directory Tree

```text
supply-demand-forecasting/
├── frontend/
│   ├── public/
│   │   └── .gitkeep
│   ├── src/
│   │   ├── assets/
│   │   │   └── .gitkeep
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   └── .gitkeep
│   │   │   ├── upload/
│   │   │   │   └── .gitkeep
│   │   │   ├── forecast/
│   │   │   │   └── .gitkeep
│   │   │   └── layout/
│   │   │       └── .gitkeep
│   │   ├── pages/
│   │   │   └── .gitkeep
│   │   ├── hooks/
│   │   │   └── .gitkeep
│   │   ├── services/
│   │   │   └── .gitkeep
│   │   ├── context/
│   │   │   └── .gitkeep
│   │   ├── utils/
│   │   │   └── .gitkeep
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   ├── intelligence/
│   │   │   └── __init__.py
│   │   ├── data_processing/
│   │   │   └── __init__.py
│   │   ├── forecasting/
│   │   │   └── __init__.py
│   │   ├── evaluation/
│   │   │   └── __init__.py
│   │   ├── analytics/
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   └── __init__.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_upload.py
│   │   ├── test_schema_mapping.py
│   │   ├── test_forecasting.py
│   │   ├── test_intent.py
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── .env.example
│   └── pytest.ini
├── docs/
│   ├── architecture.md
│   ├── api-spec.md
│   ├── dataset-guide.md
│   └── testing-plan.md
├── .gitignore
├── directory.md
├── README.md
├── mermaid-diagram.png           # Architecture & query flow diagram
└── Upload Flow.png               # File upload & schema validation flow
```

---

## 2. Root Directory Responsibilities

| File / Folder | Responsibility |
| :--- | :--- |
| `frontend/` | Complete client-side single-page application built with React and Vite. |
| `backend/` | Python FastAPI web service containing data processing, ML, and intelligence logic. |
| `docs/` | System specifications, architecture documentation, dataset guidelines, and testing plans. |
| `.gitignore` | Excludes development artifacts, caches (`__pycache__`, `.pytest_cache`), virtual environments (`.venv`), `node_modules`, build directories (`dist`), uploaded datasets, and sensitive credentials (`.env`). |
| `directory.md` | Comprehensive directory documentation mapping responsibilities across the codebase. |
| `README.md` | Primary entry point with project overview, tech stack, architecture summary, and setup commands. |
| `*.png` | Preserved user design diagrams illustrating the upload flow and architecture query workflow. |

---

## 3. Frontend Directory Responsibilities (`frontend/`)

The frontend delivers an interactive dashboard for uploading data, validating schemas, configuring forecast models, and inspecting results.

### `frontend/src/components/`
Modular UI components grouped by functional domain:
- **`upload/`**:
  - Drag-and-drop file ingestion zone for `.csv` and `.xlsx` files.
  - Table preview of ingested raw records.
  - Interactive schema mapping controls to select or confirm date, target demand, and SKU columns.
- **`forecast/`**:
  - Model selection toggles (Baseline, Scikit-Learn Random Forest, XGBoost).
  - Forecast horizon parameter controls (e.g. 7, 14, 30, 90 periods).
  - Recharts visual canvas rendering historical demand curves, forecast points, and prediction bounds.
  - Performance evaluation summary cards (MAE, RMSE, MAPE).
- **`chat/`**:
  - Chat window and input area for natural language queries regarding the active dataset.
  - Bubble components presenting answers, scope alerts, and structured data tables.
- **`layout/`**:
  - Reusable layout scaffolding: top navigation bar, status badges, notifications, and responsive containers.

### Supporting Frontend Directories
- **`public/`**: Static browser assets served directly without Vite transformation (favicons, manifest).
- **`src/assets/`**: Local images, SVGs, and brand assets imported by React components.
- **`src/pages/`**: High-level page compositions (e.g., Dashboard, Upload, Analytics).
- **`src/hooks/`**: Custom React hooks (e.g., `useSession`, `useForecast`, `useUpload`) encapsulating state and async workflows.
- **`src/services/`**: API client modules using `fetch` to talk to backend endpoints (`/api/upload`, `/api/forecast`, etc.).
- **`src/context/`**: Global React Context providers for managing active session state, uploaded file metadata, and model results.
- **`src/utils/`**: Utility functions for date formatting, numeric aggregation, chart color generators, and validation helpers.

### Frontend Root Files
- **`App.jsx`**: Root React component establishing layout structure and view routing.
- **`main.jsx`**: DOM mount entry point initializing React strict mode and loading styles.
- **`index.css`**: Global stylesheet importing Tailwind CSS v4 (`@import "tailwindcss";`).
- **`index.html`**: HTML entry point containing viewport settings and script injection tags.
- **`package.json`**: NPM package manifest with dependencies (`react`, `recharts`, `lucide-react`, `tailwindcss`, `@tailwindcss/vite`) and scripts.
- **`vite.config.js`**: Vite configuration with `@tailwindcss/vite` plugin and backend API proxy (`/api` -> `http://localhost:8000`).
- **`.env.example`**: Safe sample file for frontend environment variables (`VITE_API_BASE_URL`).

---

## 4. Backend Directory Responsibilities (`backend/`)

The backend is built as a layered, modular FastAPI application without persistent database dependencies. It stores session state in memory.

### `backend/app/` Subpackages

- **`api/routes/`**:
  - FastAPI router modules exposing REST endpoints.
  - Separated into route handlers for health, dataset upload, schema confirmation, forecasting, analytics, and chat.
- **`schemas/`**:
  - Pydantic models (DTOs) for strict request validation and response serialization.
  - Defines contracts for upload responses, schema mapping payloads, forecast requests, and chat queries.
- **`services/`**:
  - Orchestration layer bridging route handlers with underlying data and ML engines.
  - Implements the in-memory **Session Manager** managing dataset lifecycles, cache expiration, and session IDs.
- **`data_processing/`**:
  - Ingestion parser for `.csv` and `.xlsx` files using `pandas` and `openpyxl`.
  - Schema detection heuristics: identifies datetime columns, numeric demand columns, and SKU identifiers.
  - Normalization pipeline: timestamp conversion, missing value zero-filling/interpolation, and regular time-bucket aggregation.
- **`forecasting/`**:
  - Machine learning pipelines and feature engineering.
  - Feature generators: time lags ($t-1, t-7$), rolling statistics, day-of-week, month, and holiday features.
  - Model definitions: Baseline models (naive/moving average), Scikit-Learn regressors, and XGBoost models.
  - Multi-step future horizon generator with prediction interval estimation.
- **`evaluation/`**:
  - Evaluation metric calculators (Mean Absolute Error, Root Mean Squared Error, Mean Absolute Percentage Error).
  - Train/test holdout splitting and backtesting validation tools.
- **`analytics/`**:
  - Exploratory statistical metrics: total volume, moving trends, coefficient of variation, peak day/month detection.
  - Stockout risk scoring and inventory safety stock suggestions.
- **`intelligence/`**:
  - Natural language interpretation and intent handling.
  - **Domain Validation**: Guards against out-of-scope requests, enforcing supply-chain topic restrictions.
  - **Intent Parser**: Rule-based extractor for queries (e.g. extracting SKU IDs, target date ranges, forecast requests).
  - **Optional LLM Provider**: Pluggable wrapper providing narrative summaries when an LLM key is configured; seamlessly falls back to rule-based templates when unconfigured.
- **`core/`**:
  - Global application settings using `pydantic-settings` (`config.py`).
  - Constants, supported model definitions, and system logging setups.
- **`utils/`**:
  - Common utility functions: datetime manipulation, math helpers, and file format validation.
- **`main.py`**:
  - FastAPI application factory, CORS middleware configuration, route inclusion, and health check route.

### `backend/tests/`
Automated test suite maintaining system reliability:
- **`test_upload.py`**: Tests file validation, size enforcement, and temporary session instantiation.
- **`test_schema_mapping.py`**: Tests automated column detection, date parsing, and schema confirmation.
- **`test_forecasting.py`**: Tests feature engineering, model training (sklearn & XGBoost), and metric calculations.
- **`test_intent.py`**: Tests domain scoping, rule-based intent parsing, and LLM fallback behaviors.
- **`test_api.py`**: Integration tests for FastAPI endpoints, CORS headers, and error responses.

### Backend Root Files
- **`requirements.txt`**: Python dependencies (`fastapi`, `uvicorn`, `pydantic`, `pandas`, `openpyxl`, `scikit-learn`, `xgboost`, `pytest`).
- **`.env.example`**: Safe configuration template defining host, port, CORS origins, and optional LLM keys.
- **`pytest.ini`**: Pytest configuration setting test paths and verbosity.

---

## 5. Documentation Directory Responsibilities (`docs/`)

- **`architecture.md`**: Detailed technical architecture, component interactions, session lifecycle, and system diagrams.
- **`api-spec.md`**: Complete REST API specification including paths, methods, request bodies, and JSON responses.
- **`dataset-guide.md`**: Guidelines for supported file formats, expected schemas, required columns, and data hygiene rules.
- **`testing-plan.md`**: Comprehensive quality assurance strategy covering unit tests, integration tests, and verification flows.
