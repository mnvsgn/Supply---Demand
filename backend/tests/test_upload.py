import io
import openpyxl
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app
from app.services.dataset_registry import dataset_registry

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure a clean dataset registry for each test."""
    dataset_registry.clear()
    yield
    dataset_registry.clear()


def create_sample_csv(num_rows: int = 10) -> bytes:
    """Generates standard CSV bytes for time-series demand testing."""
    lines = ["date,sku_id,units_sold,unit_price"]
    for i in range(1, num_rows + 1):
        lines.append(f"2023-01-{i:02d},SKU-100,{50 + i * 2},{19.99}")
    return "\n".join(lines).encode("utf-8")


def create_sample_xlsx(num_rows: int = 8) -> bytes:
    """Generates valid Excel (.xlsx) file bytes using openpyxl."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DemandData"
    ws.append(["date", "product_id", "demand_quantity", "store_id"])
    for i in range(1, num_rows + 1):
        ws.append([f"2023-03-{i:02d}", f"PROD-{i}", 100 + i * 5, "STORE-1"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_upload_valid_csv():
    """Verify that a standard CSV is successfully parsed, registered, and previewed."""
    csv_bytes = create_sample_csv(num_rows=10)
    files = {"file": ("sales_data.csv", csv_bytes, "text/csv")}

    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert "dataset_id" in data
    assert data["filename"] == "sales_data.csv"
    assert data["file_type"] == "csv"
    assert data["row_count"] == 10
    assert data["column_count"] == 4
    assert data["columns"] == ["date", "sku_id", "units_sold", "unit_price"]
    assert data["dtypes"]["date"] == "datetime"
    assert data["dtypes"]["units_sold"] in ("integer", "numeric")

    # Verify preview is strictly limited to 5 rows and does not leak full dataset
    assert len(data["preview"]) == 5
    assert data["preview_rows_count"] == 5
    assert data["preview"][0]["sku_id"] == "SKU-100"
    assert "expires_at" in data


def test_upload_valid_xlsx():
    """Verify that a valid Excel (.xlsx) file is correctly parsed and registered."""
    xlsx_bytes = create_sample_xlsx(num_rows=8)
    files = {
        "file": (
            "inventory.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert "dataset_id" in data
    assert data["file_type"] == "xlsx"
    assert data["row_count"] == 8
    assert data["column_count"] == 4
    assert len(data["preview"]) == 5


def test_upload_empty_file():
    """Verify that a 0-byte file is rejected with clear error."""
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["code"] == "EMPTY_FILE"


def test_upload_empty_dataset_rows():
    """Verify that a CSV with headers but no data rows is rejected."""
    csv_content = b"date,demand,sku\n"
    files = {"file": ("no_rows.csv", csv_content, "text/csv")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["code"] == "EMPTY_DATASET_ROWS"


def test_upload_empty_xlsx():
    """Verify that an empty Excel workbook (no data rows) is rejected."""
    wb = openpyxl.Workbook()
    buf = io.BytesIO()
    wb.save(buf)

    files = {"file": ("empty_sheet.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 400
    assert response.json()["code"] in ("EMPTY_DATASET_ROWS", "INSUFFICIENT_COLUMNS")


def test_upload_invalid_extension():
    """Verify that non-CSV/XLSX files are rejected with HTTP 415."""
    files = {"file": ("config.json", b'{"key": "value"}', "application/json")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 415

    data = response.json()
    assert data["code"] == "UNSUPPORTED_FILE_FORMAT"


def test_upload_spoofed_csv_with_binary_signature():
    """Verify that binary executable content disguised as a .csv is rejected."""
    fake_csv = b"\x7fELF" + b"\x00" * 200
    files = {"file": ("malicious.csv", fake_csv, "text/csv")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["code"] == "BINARY_FILE_AS_CSV"


def test_upload_spoofed_xlsx_invalid_signature():
    """Verify that plain text renamed to .xlsx is rejected due to invalid signature."""
    plain_text = b"This is just plain text, not an excel spreadsheet."
    files = {"file": ("fake_workbook.xlsx", plain_text, "application/octet-stream")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["code"] == "INVALID_XLSX_SIGNATURE"


def test_upload_corrupt_zip_as_xlsx():
    """Verify that a corrupted zip archive masquerading as .xlsx is rejected."""
    corrupt_zip = b"PK\x03\x04" + b"\x00" * 50
    files = {"file": ("corrupt.xlsx", corrupt_zip, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 400
    assert response.json()["code"] in ("CORRUPT_XLSX_FILE", "INVALID_EXCEL_STRUCTURE")


def test_upload_insufficient_columns():
    """Verify that datasets with fewer than 2 columns are rejected."""
    single_col_csv = b"demand\n100\n200\n300\n400\n"
    files = {"file": ("single_col.csv", single_col_csv, "text/csv")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["code"] == "INSUFFICIENT_COLUMNS"


def test_upload_size_limit(monkeypatch):
    """Verify that files exceeding the maximum allowed size are rejected with HTTP 413."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1 / (1024 * 1024 * 0.01))

    large_content = b"a" * (settings.max_upload_size_bytes + 10)
    files = {"file": ("oversized.csv", large_content, "text/csv")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 413

    data = response.json()
    assert data["code"] == "FILE_TOO_LARGE"


def test_filename_sanitization_and_path_traversal():
    """Verify that path traversal attempts in filenames are safely neutralized."""
    csv_bytes = create_sample_csv(num_rows=3)
    files = {"file": ("../../../../etc/passwd.csv", csv_bytes, "text/csv")}
    response = client.post("/api/v1/datasets/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert ".." not in data["filename"]
    assert "/" not in data["filename"]
    assert "\\" not in data["filename"]


def test_get_dataset_metadata():
    """Verify that uploaded dataset metadata can be retrieved by identifier."""
    csv_bytes = create_sample_csv(num_rows=5)
    files = {"file": ("test_metadata.csv", csv_bytes, "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    get_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_res.status_code == 200
    meta = get_res.json()
    assert meta["dataset_id"] == dataset_id
    assert meta["row_count"] == 5
    assert len(meta["preview"]) == 5


def test_get_dataset_not_found():
    """Verify that querying a non-existent or expired dataset returns 404."""
    response = client.get("/api/v1/datasets/non-existent-uuid-1234")
    assert response.status_code == 404
    assert response.json()["code"] == "DATASET_NOT_FOUND"
