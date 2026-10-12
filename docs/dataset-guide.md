# Dataset Guidelines & Preparation

This guide explains the data format requirements, supported schema structures, and best practices for preparing business datasets for the **Supply and Demand Forecasting** system.

---

## 1. Supported File Formats

- **Comma-Separated Values (`.csv`)**: Standard UTF-8 encoded files.
- **Excel Spreadsheets (`.xlsx`)**: Microsoft Excel workbooks (the first sheet is ingested by default).
- **Maximum File Size**: 25 MB (configurable via backend `.env`).

---

## 2. Schema Structure

The platform accepts flexible column names and uses automatic schema detection to map fields. However, the dataset must satisfy minimum time-series requirements.

### Required Fields

| Field Concept | Typical Column Names | Expected Data Type | Description |
| :--- | :--- | :--- | :--- |
| **Timestamp / Date** | `date`, `timestamp`, `order_date`, `day`, `transaction_date` | Date / String / Datetime | Chronological indicator for time-series ordering. Must contain parseable dates (e.g., `2023-05-15` or `05/15/2023`). |
| **Demand Target** | `demand`, `units_sold`, `sales_quantity`, `volume`, `quantity` | Numeric (Integer / Float) | The primary quantity to forecast. Negative values represent returns and will be flagged during validation. |

### Recommended Optional Fields

| Field Concept | Typical Column Names | Expected Data Type | Description |
| :--- | :--- | :--- | :--- |
| **Product / SKU** | `sku`, `product_id`, `item_id`, `article_number` | String / Categorical | Allows item-level breakdown and individualized forecasting models. |
| **Store / Location** | `store_id`, `warehouse_id`, `region`, `branch` | String / Categorical | Enables regional or distribution center level aggregation. |
| **Price / Revenue** | `price`, `unit_price`, `selling_price` | Numeric | Exogenous feature for demand elasticity modeling. |
| **Promotions** | `is_promo`, `discount_percent`, `on_sale` | Numeric / Boolean | Indicator for marketing spikes and promotional uplift. |

---

## 3. Sample Dataset

```csv
date,sku_id,store_id,units_sold,unit_price,is_promo
2023-01-01,SKU-1001,STORE-A,42,19.99,0
2023-01-01,SKU-1002,STORE-A,15,49.99,0
2023-01-02,SKU-1001,STORE-A,48,19.99,0
2023-01-02,SKU-1002,STORE-A,12,49.99,0
2023-01-03,SKU-1001,STORE-A,65,17.99,1
2023-01-03,SKU-1002,STORE-A,18,49.99,0
```

---

## 4. Preprocessing & Quality Checks

During the ingestion step, the backend performs the following automated verifications:
1. **Date Continuity**: Checks whether time steps are regular (e.g. daily) or contain gaps.
2. **Missing Value Resolution**:
   - Gaps in continuous dates for existing SKUs are zero-filled (reflecting zero demand).
   - Missing prices are forward-filled.
3. **Duplicate Timestamps**: Multiple entries on the same date for the same SKU/Store are summed.
4. **Data Volume Thresholds**: Recommends at least 60 historical observations per entity to reliably fit machine learning models (e.g., XGBoost, Random Forest).
