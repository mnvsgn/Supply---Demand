"""
Business Analytics & Grounded Insights Service.
Aggregates sales trends, seasonality patterns, product rankings,
and inventory estimates.
"""

from typing import Any, Dict, List, Optional
import pandas as pd

from app.analytics.sales_trends import analyze_sales_trend, analyze_product_rankings
from app.analytics.seasonality import analyze_seasonality
from app.analytics.inventory_insights import analyze_inventory_insights, analyze_correlations


class BusinessAnalyticsService:
    """
    Computes grounded statistical analytics from normalized dataset representations.
    Strictly avoids unsupported causal claims or invented numbers.
    """

    def analyze_sales_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        return analyze_sales_trend(df)

    def analyze_product_rankings(self, df: pd.DataFrame, top_n: int = 10) -> Optional[List[Dict[str, Any]]]:
        return analyze_product_rankings(df, top_n=top_n)

    def analyze_seasonality(self, df: pd.DataFrame) -> Dict[str, Any]:
        return analyze_seasonality(df)

    def analyze_inventory_insights(
        self,
        df: pd.DataFrame,
        lead_time_days: Optional[int] = None,
        service_level: float = 0.95,
        current_inventory: Optional[float] = None,
    ) -> Dict[str, Any]:
        return analyze_inventory_insights(
            df=df,
            lead_time_days=lead_time_days,
            service_level=service_level,
            current_inventory=current_inventory,
        )

    def analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        return analyze_correlations(df)

    def generate_full_insights(
        self,
        df: pd.DataFrame,
        lead_time_days: Optional[int] = None,
        service_level: float = 0.95,
        current_inventory: Optional[float] = None,
    ) -> Dict[str, Any]:
        return {
            "trend": self.analyze_sales_trend(df),
            "product_rankings": self.analyze_product_rankings(df),
            "seasonality": self.analyze_seasonality(df),
            "inventory_insights": self.analyze_inventory_insights(
                df=df,
                lead_time_days=lead_time_days,
                service_level=service_level,
                current_inventory=current_inventory,
            ),
            "correlations": self.analyze_correlations(df),
        }


business_analytics = BusinessAnalyticsService()
