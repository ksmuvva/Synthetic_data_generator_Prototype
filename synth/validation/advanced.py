"""
Advanced validation metrics for synthetic data.

Provides mutual information, ML benchmarking, and
other advanced validation techniques.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list
import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.metrics import mutual_info_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score


class AdvancedValidator:
    """
    Advanced validation for synthetic data.

    Computes mutual information, feature importance,
    and ML performance metrics.
    """

    def __init__(self):
        """Initialize validator."""

    def compute_mutual_information(
        self,
        synthetic: pd.DataFrame,
        reference: pd.DataFrame,
    ) -> dict[str, float]:
        """
        Compute mutual information between columns.

        Args:
            synthetic: Synthetic data
            reference: Reference data

        Returns:
            Dictionary of mutual information scores
        """
        mi_scores = {}

        # Get common columns
        common_cols = [c for c in synthetic.columns if c in reference.columns]

        for col in common_cols:
            try:
                # Compute MI for each pair
                for other_col in common_cols:
                    if col != other_col:
                        key = f"{col}__{other_col}"
                        mi_synthetic = mutual_info_score(
                            synthetic[col].fillna("UNKNOWN"),
                            synthetic[other_col].fillna("UNKNOWN")
                        )
                        mi_reference = mutual_info_score(
                            reference[col].fillna("UNKNOWN"),
                            reference[other_col].fillna("UNKNOWN")
                        )
                        mi_scores[key] = abs(mi_synthetic - mi_reference)
            except Exception:
                pass

        return mi_scores

    def benchmark_ml_model(
        self,
        synthetic: pd.DataFrame,
        reference: pd.DataFrame,
        target_column: str,
    ) -> dict[str, float]:
        """
        Benchmark ML model performance on synthetic vs reference.

        Args:
            synthetic: Synthetic data
            reference: Reference data
            target_column: Target variable for prediction

        Returns:
            Dictionary with performance metrics
        """
        # Prepare data
        syn_features = synthetic.drop(columns=[target_column])
        ref_features = reference.drop(columns=[target_column])

        syn_target = synthetic[target_column]
        ref_target = reference[target_column]

        # Get common feature columns
        feature_cols = [c for c in syn_features.columns if c in ref_features.columns]

        if not feature_cols:
            return {}

        # Train on reference, test on synthetic
        rf = RandomForestClassifier(n_estimators=50, random_state=42)

        try:
            # Cross-validation on reference
            ref_scores = cross_val_score(
                rf, ref_features[feature_cols], ref_target, cv=3
            )

            # Train on reference, test on synthetic
            rf.fit(ref_features[feature_cols], ref_target)
            syn_score = rf.score(syn_features[feature_cols], syn_target)

            return {
                "reference_cv_mean": ref_scores.mean(),
                "reference_cv_std": ref_scores.std(),
                "synthetic_test_score": syn_score,
                "score_difference": abs(ref_scores.mean() - syn_score),
            }

        except Exception:
            return {}


class ModelComparison:
    """
    Compare ML models trained on synthetic vs real data.

    Validates if synthetic data can be used for ML training.
    """

    def __init__(self):
        """Initialize comparator."""

    def compare_performance(
        self,
        synthetic_train: pd.DataFrame,
        real_train: pd.DataFrame,
        test_data: pd.DataFrame,
        target_column: str,
    ) -> dict[str, dict]:
        """
        Compare model performance.

        Args:
            synthetic_train: Training data (synthetic)
            real_train: Training data (real)
            test_data: Test data (real)
            target_column: Target variable

        Returns:
            Performance comparison
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, classification_report

        feature_cols = [c for c in synthetic_train.columns if c != target_column]

        results = {}

        # Train on synthetic
        rf_synthetic = RandomForestClassifier(n_estimators=50, random_state=42)
        rf_synthetic.fit(synthetic_train[feature_cols], synthetic_train[target_column])
        synthetic_preds = rf_synthetic.predict(test_data[feature_cols])
        synthetic_acc = accuracy_score(test_data[target_column], synthetic_preds)

        # Train on real
        rf_real = RandomForestClassifier(n_estimators=50, random_state=42)
        rf_real.fit(real_train[feature_cols], real_train[target_column])
        real_preds = rf_real.predict(test_data[feature_cols])
        real_acc = accuracy_score(test_data[target_column], real_preds)

        results["random_forest"] = {
            "synthetic_trained_accuracy": synthetic_acc,
            "real_trained_accuracy": real_acc,
            "accuracy_difference": abs(synthetic_acc - real_acc),
        }

        return results
