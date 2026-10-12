from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class NormalizationSummary:
    total_records: int
    date_range: Dict[str, Optional[str]]
    inferred_frequency: str
    total_demand: float
    average_demand_per_period: float
    unique_products_count: int
    unique_stores_count: int
    has_product_hierarchy: bool
    has_store_hierarchy: bool
    support_aggregate_forecast: bool
    support_product_forecast: bool
    top_products: List[Dict[str, Any]]


class PreprocessingPipeline:
    """
    Normalizes mapped canonical dataframes into standardized, clean structures
    ready for time-series forecasting, while preserving the raw source data.
    """

    def normalize(
        self,
        mapped_df: pd.DataFrame,
        inferred_freq: str = "D",
    ) -> Tuple[pd.DataFrame, NormalizationSummary]:
        """
        Cleans and types canonical fields:
        - date: pd.Timestamp, sorted chronologically
        - demand: float / numeric
        - product_id: str (if present)
        - store_id: str (if present)
        - price: float (if present)
        - promotion: float / int (if present)
        """
        df = mapped_df.copy()

        # 1. Normalize Date
        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
        # Drop unparseable dates from normalized analysis copy (preserving raw in storage)
        df = df.dropna(subset=["date"])
        df = df.sort_values(by="date").reset_index(drop=True)

        # 2. Normalize Demand
        df["demand"] = pd.to_numeric(df["demand"], errors="coerce")

        # 3. Normalize Optional Hierarchies & Features
        has_products = "product_id" in df.columns
        if has_products:
            df["product_id"] = df["product_id"].astype(str).str.strip()

        has_stores = "store_id" in df.columns
        if has_stores:
            df["store_id"] = df["store_id"].astype(str).str.strip()

        if "price" in df.columns:
            df["price"] = pd.to_numeric(df["price"], errors="coerce")

        if "promotion" in df.columns:
            # Normalize boolean/flag to numeric 0 or 1
            df["promotion"] = pd.to_numeric(
                df["promotion"].replace({True: 1, False: 0, "Y": 1, "N": 0, "y": 1, "n": 0}),
                errors="coerce",
            )

        # 4. Generate Summary Metrics
        valid_demand = df["demand"].dropna()
        total_demand = float(valid_demand.sum()) if not valid_demand.empty else 0.0
        avg_demand = float(valid_demand.mean()) if not valid_demand.empty else 0.0

        unique_products = df["product_id"].nunique() if has_products else 0
        unique_stores = df["store_id"].nunique() if has_stores else 0

        # Top 5 products by volume if product hierarchy is available
        top_products = []
        if has_products and unique_products > 0:
            top_grouped = (
                df.groupby("product_id")["demand"]
                .sum()
                .sort_values(ascending=False)
                .head(5)
            )
            top_products = [
                {"product_id": str(pid), "total_volume": float(vol)}
                for pid, vol in top_grouped.items()
            ]

        date_range = {
            "start": df["date"].min().strftime("%Y-%m-%d") if not df.empty else None,
            "end": df["date"].max().strftime("%Y-%m-%d") if not df.empty else None,
        }

        summary = NormalizationSummary(
            total_records=len(df),
            date_range=date_range,
            inferred_frequency=inferred_freq,
            total_demand=round(total_demand, 2),
            average_demand_per_period=round(avg_demand, 2),
            unique_products_count=unique_products,
            unique_stores_count=unique_stores,
            has_product_hierarchy=has_products and unique_products > 1,
            has_store_hierarchy=has_stores and unique_stores > 1,
            support_aggregate_forecast=len(df) >= 3,
            support_product_forecast=has_products and unique_products > 0,
            top_products=top_products,
        )

        return df, summary

    def get_aggregate_demand_series(
        self,
        normalized_df: pd.DataFrame,
        frequency: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Sums demand across all products and stores by timestamp for macro-level forecasting.
        """
        agg = (
            normalized_df.groupby("date", as_index=False)["demand"]
            .sum()
            .sort_values(by="date")
            .reset_index(drop=True)
        )
        return agg

    def get_product_demand_series(
        self,
        normalized_df: pd.DataFrame,
        product_id: str,
    ) -> pd.DataFrame:
        """
        Filters by specific product_id and aggregates demand by timestamp.
        """
        if "product_id" not in normalized_df.columns:
            raise ValueError("Dataset does not have a product_id hierarchy.")

        product_mask = normalized_df["product_id"] == str(product_id).strip()
        filtered = normalized_df[product_mask]

        if filtered.empty:
            raise ValueError(f"No records found for product_id '{product_id}'.")

        agg = (
            filtered.groupby("date", as_index=False)["demand"]
            .sum()
            .sort_values(by="date")
            .reset_index(drop=True)
        )
        return agg


# Global singleton
preprocessing_pipeline = PreprocessingPipeline()
