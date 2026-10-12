# Supply and Demand Forecasting

An end-to-end Machine Learning web application designed to forecast supply and demand patterns from uploaded time-series business data. Built as a college ML capstone project, this application features an interactive React dashboard, a robust Python FastAPI backend, intelligent schema mapping, automated time-series forecasting (scikit-learn & XGBoost), and optional natural-language interpretation.

---

## 🚀 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React, Vite, Tailwind CSS, Recharts, JavaScript |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2, Uvicorn |
| **Data Processing** | pandas, NumPy, openpyxl |
| **Machine Learning** | scikit-learn, XGBoost |
| **Natural Language** | Optional LLM API integration (system functions 100% without an LLM key) |
| **Storage Architecture** | Temporary session-based storage (no external database required for v1) |

---

## 🏛️ System Architecture & Workflow

```text
+-----------------------------------------------------------------------------------+
|                                 React Frontend                                    |
|   (Upload Wizard | Dynamic Schema Mapper | Forecast Charts | Optional Chat UI)    |
+-----------------------------------------+-----------------------------------------+
                                          | REST API (HTTP)
                                          v
+-----------------------------------------------------------------------------------+
|                                 FastAPI Backend                                   |
|                                                                                   |
|  [ File Validation & Parsing ] ---> [ Schema Detection & Mapping ]                 |
|                                                     |                             |
|                                                     v                             |
|  [ Optional LLM / Rule Intent ] <---- [ Temporary Session Store ]                 |
|                                                     |                             |
|                                                     v                             |
|  [ Evaluation & Metrics ] <------- [ Forecasting & Analytics Engine ]             |
|                                       (scikit-learn / XGBoost)                    |
+-----------------------------------------------------------------------------------+
```

### Core Workflow:
1. **Dataset Upload & Validation**: User uploads `.csv` or `.xlsx` files; backend validates format, size, and structure.
2. **Schema Mapping**: Inspects columns and suggests mappings for timestamp, target demand/sales quantity, and optional attributes (product ID, store ID, price, promotions).
3. **Session-Based Caching**: Verified datasets are held in a temporary session without requiring a persistent database or user authentication.
4. **Forecasting & Analytics**: Runs machine learning pipelines (baseline models, regression, XGBoost) across designated forecast horizons with metrics (MAE, RMSE, MAPE).
5. **Interactive Visualization**: Frontend renders responsive historical trends, forecast horizons, prediction intervals, and summary analytics via Recharts.
6. **Optional Natural Language Interpretation**: When enabled, an LLM provides high-level narrative summaries and answers queries; when disabled, rule-based responses take over seamlessly.

---

## 📁 Repository Structure

```text
supply-demand-forecasting/
├── frontend/                     # React + Vite client application
│   ├── public/                   # Static browser assets
│   ├── src/
│   │   ├── assets/               # Local icons and media
│   │   ├── components/           # Reusable UI component modules
│   │   │   ├── chat/             # Optional NL query & chat components
│   │   │   ├── upload/           # Drag-and-drop file upload & schema mapping
│   │   │   ├── forecast/         # Horizon selectors, charts & metrics
│   │   │   └── layout/           # App navigation, header, and containers
│   │   ├── pages/                # Main dashboard and view pages
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # API client modules
│   │   ├── context/              # Global state & session providers
│   │   ├── utils/                # UI formatting and helpers
│   │   ├── App.jsx               # Root application component
│   │   ├── main.jsx              # Application entry point
│   │   └── index.css             # Tailwind base and custom styles
│   ├── index.html                # HTML entry point
│   ├── package.json              # Frontend dependencies and scripts
│   ├── vite.config.js            # Vite build and proxy configuration
│   └── .env.example              # Frontend environment variables template
├── backend/                      # FastAPI Python service
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/           # Endpoint handlers (upload, forecast, etc.)
│   │   ├── schemas/              # Pydantic data schemas and DTOs
│   │   ├── services/             # Application coordination and session storage
│   │   ├── intelligence/         # Intent parsing and optional LLM integration
│   │   ├── data_processing/      # File parsing, cleaning, schema validation
│   │   ├── forecasting/          # scikit-learn & XGBoost model pipelines
│   │   ├── evaluation/           # Model accuracy metrics (MAE, RMSE, MAPE)
│   │   ├── analytics/            # Trends, seasonality, stockout analysis
│   │   ├── core/                 # App configuration and settings
│   │   ├── utils/                # Shared helper functions and logging
│   │   └── main.py               # FastAPI application entry point
│   ├── tests/                    # Pytest automated test suites
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Backend environment variables template
│   └── pytest.ini                # Pytest configuration
├── docs/                         # Technical documentation & project specifications
│   ├── architecture.md           # Deep dive into system architecture
│   ├── api-spec.md               # REST API endpoints and schema contract
│   ├── dataset-guide.md          # Input dataset formats and sample schemas
│   └── testing-plan.md           # Verification and testing strategy
├── .gitignore                    # Version control ignore rules
├── directory.md                  # Comprehensive directory breakdown & responsibilities
└── README.md                     # Project overview and developer guide
```

---

## 🛠️ Planned Setup Instructions

### Prerequisites
- **Node.js** (v18.0 or higher) and `npm`
- **Python** (v3.10 or higher)
- `pip` or virtual environment manager (`venv`)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The backend API documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Configure environment variables
cp .env.example .env

# Start Vite development server
npm run dev
```
The frontend application will be accessible at `http://localhost:5173`.

---

## 🧪 Testing

```bash
# Run complete backend test suite (76 automated tests)
cd backend
pytest -v
```
---

## 🔒 Security & Privacy Notice
- The application uses safe placeholder configuration files (`.env.example`).
- Never commit actual API keys, secrets, or administrative passwords to version control.
- Datasets uploaded during development remain local and temporary.
