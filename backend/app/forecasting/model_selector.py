"""
Model selection layer for the forecasting engine.
Re-exports from app.evaluation.model_selector.
"""

from app.evaluation.model_selector import (
    ModelCandidateEvaluation,
    ModelSelectionResult,
    ModelSelector,
    model_selector,
)

__all__ = [
    "ModelCandidateEvaluation",
    "ModelSelectionResult",
    "ModelSelector",
    "model_selector",
]
