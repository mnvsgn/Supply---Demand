"""
Chat service module for orchestrating conversational intelligence and forecasting dispatch.
"""

from typing import Any, Dict, Optional
from app.intelligence.domain_guard import is_in_domain, get_formal_domain_response
from app.intelligence.intent_parser import parse_intent
from app.intelligence.prompt_interpreter import interpret_prompt
from app.intelligence.response_builder import (
    build_forecast_response_text,
    build_evaluation_response_text,
    build_data_quality_response_text,
    build_analytics_response_text,
)
from app.schemas.chat import ChatResponse
from app.services.dataset_registry import dataset_registry
from app.services.forecast_service import forecast_service
from app.analytics.insights import business_analytics


class ChatService:
    """Service handling conversational prompt routing and execution."""

    async def handle_prompt(
        self,
        prompt: str,
        dataset_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Processes a user prompt through domain guards, intent classification,
        and backend operations.
        """
        # 1. Domain Guard Boundary Check
        if not is_in_domain(prompt):
            return ChatResponse(
                message=get_formal_domain_response(),
                message_type="text",
                intent="out_of_scope",
            )

        # 2. Intent Parsing and Entity Interpretation
        intent_data = parse_intent(prompt)
        intent = intent_data["intent"]
        entities = interpret_prompt(prompt)

        # 3. Check Dataset Availability if Required
        if intent_data["requires_dataset"] and not dataset_id:
            return ChatResponse(
                message=(
                    "I need a historical demand dataset before generating forecasts or analytics. "
                    "Please upload a CSV or XLSX file using the attachment button."
                ),
                message_type="text",
                intent=intent,
            )

        # 4. Dispatch based on Intent
        if intent == "forecast" and dataset_id:
            record = dataset_registry.get_dataset(dataset_id, session_id=session_id)
            if not record or not record.is_mapped:
                return ChatResponse(
                    message="Please confirm column mappings for Date and Demand before forecasting.",
                    message_type="error",
                    intent=intent,
                )

            horizon = entities.get("horizon", 14)
            model_type = entities.get("model_type", "auto")
            target_level = entities.get("target_level", "aggregate")
            product_id = entities.get("product_id")

            result = forecast_service.generate_forecast(
                dataset_id=dataset_id,
                model_type=model_type,
                horizon=horizon,
                target_level=target_level,
                product_id=product_id,
                confidence_level=entities.get("service_level", 0.95),
            )

            res_dict = result.to_dict()
            forecast_rows = res_dict.get("forecast", [])
            msg = build_forecast_response_text(
                model_name=result.model_name,
                horizon=horizon,
                points_count=len(forecast_rows),
                product_id=product_id,
            )

            payload = {
                "dataset_id": dataset_id,
                "model_name": result.model_name,
                "model_type": result.model_type,
                "horizon": horizon,
                "frequency": result.frequency,
                "forecast": forecast_rows,
                "feature_importance": result.feature_importance,
                "metrics": result.metrics,
                "model_comparison": result.model_comparison,
                "metadata": result.metadata,
                "warnings": result.warnings,
            }

            return ChatResponse(
                message=msg,
                message_type="forecast",
                data=payload,
                intent=intent,
            )

        elif intent == "evaluate_models" and dataset_id:
            record = dataset_registry.get_dataset(dataset_id, session_id=session_id)
            if not record or not record.is_mapped:
                return ChatResponse(
                    message="Please verify column mappings before evaluating models.",
                    message_type="error",
                    intent=intent,
                )

            horizon = entities.get("horizon", 14)
            target_level = entities.get("target_level", "aggregate")
            product_id = entities.get("product_id")
            eval_res = forecast_service.evaluate_dataset(
                dataset_id=dataset_id,
                horizon=horizon,
                target_level=target_level,
                product_id=product_id,
                primary_metric="wape",
            )

            msg = build_evaluation_response_text(
                winning_model=eval_res.selected_model_name,
                metric_name=eval_res.primary_metric if hasattr(eval_res, "primary_metric") else "WAPE",
            )

            eval_dict = eval_res.to_dict()
            payload = {
                "dataset_id": dataset_id,
                "target_level": target_level,
                "product_id": product_id,
                "primary_metric": "wape",
                "evaluation_mode": eval_dict.get("evaluation_mode"),
                "selected_model_type": eval_dict.get("selected_model_type"),
                "selected_model_name": eval_dict.get("selected_model_name"),
                "comparison_table": eval_dict.get("comparison_table"),
                "validation_period": eval_dict.get("validation_period"),
                "validation_metrics": eval_dict.get("validation_metrics"),
                "warnings": eval_dict.get("warnings"),
            }

            return ChatResponse(
                message=msg,
                message_type="evaluation",
                data=payload,
                intent=intent,
            )


        elif intent == "data_quality" and dataset_id:
            record = dataset_registry.get_dataset(dataset_id, session_id=session_id)
            if not record:
                return ChatResponse(
                    message="Dataset not found or session expired.",
                    message_type="error",
                    intent=intent,
                )

            quality = record.data_quality or {}
            summary = record.summary or {}

            msg = build_data_quality_response_text(
                filename=record.original_filename,
                total_records=record.row_count,
                frequency=quality.get("detected_frequency", "Daily"),
                gap_count=quality.get("gap_count", 0),
                negative_count=quality.get("negative_demand_count", 0),
                duplicate_count=quality.get("duplicate_count", 0),
            )

            return ChatResponse(
                message=msg,
                message_type="quality_warning",
                data=quality,
                intent=intent,
            )

        elif (intent in ["business_analytics", "inventory_insights"]) and dataset_id:
            record = dataset_registry.get_dataset(dataset_id, session_id=session_id)
            if not record or record.raw_df is None:
                return ChatResponse(
                    message="Dataset not loaded for analytics.",
                    message_type="error",
                    intent=intent,
                )

            df = record.raw_df
            trend = business_analytics.analyze_sales_trend(df)
            rankings = business_analytics.analyze_product_rankings(df)
            seasonality = business_analytics.analyze_seasonality(df)
            inventory = business_analytics.analyze_inventory_insights(
                df,
                lead_time_days=entities.get("lead_time_days"),
                service_level=entities.get("service_level", 0.95),
            )
            correlations = business_analytics.analyze_correlations(df)

            payload = {
                "dataset_id": dataset_id,
                "trend": trend,
                "product_rankings": rankings,
                "seasonality": seasonality,
                "inventory_insights": inventory,
                "correlations": correlations,
            }

            return ChatResponse(
                message=build_analytics_response_text(),
                message_type="analytics",
                data=payload,
                intent=intent,
            )

        # Guidance / General fallback
        return ChatResponse(
            message=(
                "I am ready to assist with your supply and demand forecasting workflow.\n"
                "1. **Upload your dataset** (.csv or .xlsx) using the attachment button.\n"
                "2. Verify or adjust auto-detected column mappings.\n"
                "3. Ask me to **'Forecast total demand for the next 14 days'**, "
                "**'Show sales trends and seasonality'**, or **'Compare ML models'**."
            ),
            message_type="text",
            intent="guidance",
        )


chat_service = ChatService()
