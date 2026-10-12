import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class ColumnCandidate:
    column_name: str
    confidence_score: float  # 0.0 to 1.0
    matched_pattern: str
    inferred_type: str


@dataclass
class SchemaDetectionResult:
    suggested_mapping: Dict[str, Optional[str]]
    confidence: Dict[str, str]  # 'high' | 'medium' | 'low'
    candidates: Dict[str, List[Dict[str, Any]]]
    ambiguity_warnings: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    inferred_frequency: Optional[str] = None


# Canonical schema fields and their priority patterns
PATTERNS = {
    "date": [
        (r"^(date|ds|datetime|timestamp)$", 0.95),
        (r"^(order_date|transaction_date|sale_date|invoice_date|period_date|trans_date)$", 0.90),
        (r"^(period|day|week|month|year_month|dt)$", 0.75),
        (r".*(date|timestamp|datetime).*", 0.65),
        (r".*(day|week|month|period).*", 0.45),
    ],
    "demand": [
        (r"^(units_sold|unit_sales|sales_quantity|quantity|qty|volume|demand)$", 0.95),
        (r"^(item_cnt_day|item_cnt_month|order_qty|num_orders|orders_count|sales_count)$", 0.90),
        (r"^(weekly_sales|daily_sales|monthly_sales)$", 0.85),
        (r"^(sales|orders|volume_sold|pieces)$", 0.75),
        (r".*(quantity|qty|units|demand|volume).*", 0.70),
        (r".*(sales|orders|sold).*", 0.50),
    ],
    "product_id": [
        (r"^(sku|sku_id|product_id|item_id|article_id|material_id)$", 0.95),
        (r"^(product|sku_code|item_code|product_code|item_number|item_nbr)$", 0.90),
        (r"^(item|article|material|dept|department|category|upc)$", 0.75),
        (r".*(sku|product|item|article|material).*", 0.60),
    ],
    "store_id": [
        (r"^(store_id|store|outlet_id|outlet|branch_id|shop_id)$", 0.95),
        (r"^(warehouse_id|location_id|center_id|facility_id|store_nbr)$", 0.90),
        (r"^(warehouse|location|branch|shop|plant|site|channel)$", 0.80),
        (r".*(store|outlet|branch|shop|warehouse|location).*", 0.60),
    ],
    "price": [
        (r"^(unit_price|price|sell_price|selling_price|retail_price)$", 0.95),
        (r"^(base_price|mrp|cost|unit_cost|standard_price|rate)$", 0.85),
        (r".*(price|mrp|cost).*", 0.60),
    ],
    "promotion": [
        (r"^(promo|is_promo|promotion|on_sale|is_promotion|promo_flag)$", 0.95),
        (r"^(promo1|promo2|promo3|discount|discount_pct|discount_percent)$", 0.90),
        (r"^(isholiday|is_holiday|holiday|event|stateholiday|schoolholiday|event_name)$", 0.85),
        (r".*(promo|promotion|discount|sale_flag|holiday|event).*", 0.65),
    ],
}

# Revenue / Monetary keywords indicating financial turnover rather than physical volume
REVENUE_KEYWORDS = [
    "revenue",
    "turnover",
    "dollars",
    "amount",
    "total_amount",
    "sales_value",
    "sales_val",
    "gross",
    "net",
    "monetary",
    "income",
    "earnings",
]


class SchemaDetector:
    """
    Intelligently inspects raw dataset columns to detect canonical fields,
    evaluates confidence levels, and flags ambiguities (e.g., revenue vs units).
    """

    def detect(self, df: pd.DataFrame, dtypes: Dict[str, str]) -> SchemaDetectionResult:
        suggested: Dict[str, Optional[str]] = {
            "date": None,
            "demand": None,
            "product_id": None,
            "store_id": None,
            "price": None,
            "promotion": None,
        }
        confidence: Dict[str, str] = {role: "low" for role in suggested}
        candidates: Dict[str, List[Dict[str, Any]]] = {role: [] for role in suggested}
        warnings: List[str] = []

        assigned_columns = set()

        # Step 1: Score all candidate columns for each canonical role
        for role, patterns in PATTERNS.items():
            role_candidates: List[Tuple[str, float, str]] = []

            for col in df.columns:
                col_lower = str(col).lower().strip()
                col_type = dtypes.get(col, "text")

                best_score = 0.0
                best_match = "none"

                for regex, base_score in patterns:
                    if re.match(regex, col_lower, re.IGNORECASE):
                        if base_score > best_score:
                            best_score = base_score
                            best_match = regex

                # Adjust score based on data type suitability
                best_score = self._adjust_score_by_dtype(role, col_type, best_score, df[col])

                if best_score >= 0.35:
                    role_candidates.append((col, round(best_score, 3), best_match))

            # Sort descending by score
            role_candidates.sort(key=lambda x: x[1], reverse=True)
            candidates[role] = [
                {
                    "column_name": c[0],
                    "confidence_score": c[1],
                    "matched_pattern": c[2],
                    "inferred_type": dtypes.get(c[0], "text"),
                }
                for c in role_candidates
            ]

        # Step 2: Disambiguate Demand vs Revenue
        ambiguous_revenue_col, physical_unit_col = self._check_revenue_vs_units_ambiguity(df)
        if ambiguous_revenue_col and physical_unit_col:
            warnings.append(
                f"Detected potential ambiguity between monetary sales ('{ambiguous_revenue_col}') "
                f"and physical volume ('{physical_unit_col}'). Defaulting demand to physical units. "
                "Please confirm or adjust in schema mapping."
            )
        elif ambiguous_revenue_col and not physical_unit_col:
            warnings.append(
                f"The target column '{ambiguous_revenue_col}' may represent monetary revenue/sales rather than "
                "physical units. Please verify if units or revenue forecasting is intended."
            )

        # Step 3: Assign best matches avoiding duplicate usage for primary fields
        for role in ["date", "demand", "product_id", "store_id", "price", "promotion"]:
            valid_candidates = [
                c for c in candidates[role] if c["column_name"] not in assigned_columns
            ]

            # If ambiguous revenue was detected and we have physical units, force physical units
            if role == "demand" and physical_unit_col and physical_unit_col in df.columns:
                suggested[role] = physical_unit_col
                confidence[role] = "high"
                assigned_columns.add(physical_unit_col)
                continue

            if valid_candidates:
                top = valid_candidates[0]
                suggested[role] = top["column_name"]
                assigned_columns.add(top["column_name"])

                # Determine confidence
                if top["confidence_score"] >= 0.80:
                    if len(valid_candidates) > 1 and (top["confidence_score"] - valid_candidates[1]["confidence_score"] < 0.15):
                        confidence[role] = "medium"
                    else:
                        confidence[role] = "high"
                elif top["confidence_score"] >= 0.55:
                    confidence[role] = "medium"
                else:
                    confidence[role] = "low"
            else:
                suggested[role] = None
                confidence[role] = "low"

        # Step 4: Determine if user confirmation is required
        requires_confirmation = False

        if not suggested["date"] or confidence["date"] != "high":
            requires_confirmation = True
            if not suggested["date"]:
                warnings.append("Could not reliably detect a timestamp/date column. Manual mapping is required.")

        if not suggested["demand"] or confidence["demand"] != "high":
            requires_confirmation = True
            if not suggested["demand"]:
                warnings.append("Could not reliably detect a demand/sales target column. Manual mapping is required.")

        if bool(warnings):
            requires_confirmation = True

        return SchemaDetectionResult(
            suggested_mapping=suggested,
            confidence=confidence,
            candidates=candidates,
            ambiguity_warnings=warnings,
            requires_confirmation=requires_confirmation,
        )

    def _adjust_score_by_dtype(
        self, role: str, col_type: str, score: float, series: pd.Series
    ) -> float:
        """Fine-tunes matching score based on type checks and value distributions."""
        if role == "date":
            if col_type == "datetime":
                return min(1.0, score + 0.30 if score > 0 else 0.85)
            elif col_type in ("numeric", "integer"):
                # Numeric column as date is unlikely unless year (1900-2100) or timestamp
                return max(0.0, score - 0.35)

        elif role == "demand":
            if col_type in ("integer", "numeric"):
                score = min(1.0, score + 0.15 if score > 0 else 0.40)
                # If non-negative integers, high suitability for count demand
                non_null = series.dropna()
                if not non_null.empty and pd.api.types.is_numeric_dtype(non_null):
                    if (non_null >= 0).all():
                        score = min(1.0, score + 0.10)
            elif col_type in ("text", "datetime"):
                return max(0.0, score - 0.50)

        elif role == "price":
            if col_type in ("numeric", "integer"):
                score = min(1.0, score + 0.15)
            else:
                return max(0.0, score - 0.40)

        elif role == "promotion":
            non_null = series.dropna()
            if not non_null.empty:
                unique_vals = set(non_null.unique())
                # Binary promotion indicator (0/1 or True/False)
                if unique_vals.issubset({0, 1, 0.0, 1.0, True, False, "0", "1", "Y", "N"}):
                    score = min(1.0, score + 0.30 if score > 0 else 0.60)

        elif role in ("product_id", "store_id"):
            if col_type in ("categorical", "text", "integer"):
                score = min(1.0, score + 0.10)

        return score

    def _check_revenue_vs_units_ambiguity(
        self, df: pd.DataFrame
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Detects if both physical volume (units/qty) and monetary metrics (revenue/sales/dollars)
        are present in the dataset.
        Returns: (monetary_column, physical_column)
        """
        revenue_col: Optional[str] = None
        physical_col: Optional[str] = None

        for col in df.columns:
            col_l = str(col).lower().strip()

            # Check for explicit physical unit indicators
            if any(term in col_l for term in ["units_sold", "unit_sales", "qty", "quantity", "volume", "item_cnt"]):
                physical_col = col

            # Check for monetary keywords
            if any(term in col_l for term in REVENUE_KEYWORDS):
                revenue_col = col

        # If both exist or if 'sales' exists alongside 'units_sold'
        if not revenue_col:
            for col in df.columns:
                col_l = str(col).lower().strip()
                if col_l in ("sales", "weekly_sales", "daily_sales") and physical_col and col != physical_col:
                    revenue_col = col
                    break

        return revenue_col, physical_col


# Global singleton
schema_detector = SchemaDetector()
