"""Evaluation metrics for Elo rating system."""

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss
from typing import Dict, List, Tuple
import warnings


def brier_score(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """
    Calculate Brier score for probability predictions.
    
    Args:
        probs: Predicted probabilities (0 to 1)
        outcomes: Actual binary outcomes (0 or 1)
        
    Returns:
        Brier score (lower is better)
    """
    if len(probs) != len(outcomes):
        raise ValueError("Probs and outcomes must have same length")
    
    if not np.all((probs >= 0) & (probs <= 1)):
        raise ValueError("Probabilities must be between 0 and 1")
    
    if not np.all(np.isin(outcomes, [0, 1])):
        raise ValueError("Outcomes must be 0 or 1")
    
    return np.mean((probs - outcomes) ** 2)


def log_loss_score(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """
    Calculate log loss for probability predictions.
    
    Args:
        probs: Predicted probabilities (0 to 1)
        outcomes: Actual binary outcomes (0 or 1)
        
    Returns:
        Log loss (lower is better)
    """
    if len(probs) != len(outcomes):
        raise ValueError("Probs and outcomes must have same length")
    
    # Clip probabilities to avoid log(0)
    probs_clipped = np.clip(probs, 1e-15, 1 - 1e-15)
    
    # Handle case where all outcomes are the same
    unique_outcomes = np.unique(outcomes)
    if len(unique_outcomes) == 1:
        # If all outcomes are the same, use manual calculation
        if unique_outcomes[0] == 1:
            return -np.mean(np.log(probs_clipped))
        else:
            return -np.mean(np.log(1 - probs_clipped))
    
    return log_loss(outcomes, probs_clipped)


def mean_absolute_error(predictions: np.ndarray, actuals: np.ndarray) -> float:
    """
    Calculate mean absolute error.
    
    Args:
        predictions: Predicted values
        actuals: Actual values
        
    Returns:
        Mean absolute error
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")
    
    return np.mean(np.abs(predictions - actuals))


def calibration(df: pd.DataFrame, p_col: str, y_col: str, bins: int = 10) -> pd.DataFrame:
    """
    Calculate calibration metrics by binning predictions.
    
    Args:
        df: DataFrame with predictions and outcomes
        p_col: Column name for predictions
        y_col: Column name for outcomes
        bins: Number of bins to use
        
    Returns:
        DataFrame with calibration metrics per bin
    """
    if p_col not in df.columns:
        raise ValueError(f"Column {p_col} not found in DataFrame")
    if y_col not in df.columns:
        raise ValueError(f"Column {y_col} not found in DataFrame")
    
    # Create bins
    try:
        cuts = pd.qcut(df[p_col], q=bins, duplicates="drop")
    except ValueError:
        # If we can't create equal-sized bins, use equal-width bins
        cuts = pd.cut(df[p_col], bins=bins, duplicates="drop")
    
    # Calculate metrics per bin
    result = (df.assign(bin=cuts)
              .groupby("bin", observed=True)
              .agg(
                  p_hat=(p_col, "mean"),
                  y_rate=(y_col, "mean"),
                  n=(y_col, "size"),
                  p_min=(p_col, "min"),
                  p_max=(p_col, "max")
              )
              .reset_index())
    
    # Add calibration error
    result["calibration_error"] = np.abs(result["p_hat"] - result["y_rate"])
    result["weighted_error"] = result["calibration_error"] * result["n"]
    
    return result


def expected_calibration_error(df: pd.DataFrame, p_col: str, y_col: str, bins: int = 10) -> float:
    """
    Calculate expected calibration error.
    
    Args:
        df: DataFrame with predictions and outcomes
        p_col: Column name for predictions
        y_col: Column name for outcomes
        bins: Number of bins to use
        
    Returns:
        Expected calibration error
    """
    calib_df = calibration(df, p_col, y_col, bins)
    
    if len(calib_df) == 0:
        return np.nan
    
    total_games = calib_df["n"].sum()
    if total_games == 0:
        return np.nan
    
    return (calib_df["weighted_error"].sum() / total_games)


def sharpness(df: pd.DataFrame, p_col: str) -> float:
    """
    Calculate sharpness (variance of predictions).
    
    Args:
        df: DataFrame with predictions
        p_col: Column name for predictions
        
    Returns:
        Sharpness (variance of predictions)
    """
    if p_col not in df.columns:
        raise ValueError(f"Column {p_col} not found in DataFrame")
    
    return np.var(df[p_col])


def reliability_diagram_data(df: pd.DataFrame, p_col: str, y_col: str, bins: int = 10) -> Dict:
    """
    Prepare data for reliability diagram plotting.
    
    Args:
        df: DataFrame with predictions and outcomes
        p_col: Column name for predictions
        y_col: Column name for outcomes
        bins: Number of bins to use
        
    Returns:
        Dictionary with plotting data
    """
    calib_df = calibration(df, p_col, y_col, bins)
    
    return {
        "bin_centers": calib_df["p_hat"].values,
        "empirical_rates": calib_df["y_rate"].values,
        "bin_counts": calib_df["n"].values,
        "bin_ranges": [(row["p_min"], row["p_max"]) for _, row in calib_df.iterrows()]
    }


def calculate_all_metrics(df: pd.DataFrame, p_col: str = "p_home", y_col: str = "home_win") -> Dict[str, float]:
    """
    Calculate all evaluation metrics for a dataset.
    
    Args:
        df: DataFrame with predictions and outcomes
        p_col: Column name for predictions
        y_col: Column name for outcomes
        
    Returns:
        Dictionary with all metrics
    """
    if p_col not in df.columns:
        raise ValueError(f"Column {p_col} not found in DataFrame")
    if y_col not in df.columns:
        raise ValueError(f"Column {y_col} not found in DataFrame")
    
    # Remove any rows with missing values
    clean_df = df[[p_col, y_col]].dropna()
    
    if len(clean_df) == 0:
        return {"error": "No valid data points"}
    
    probs = clean_df[p_col].values
    outcomes = clean_df[y_col].values
    
    metrics = {
        "brier_score": brier_score(probs, outcomes),
        "log_loss": log_loss_score(probs, outcomes),
        "ece": expected_calibration_error(clean_df, p_col, y_col),
        "sharpness": sharpness(clean_df, p_col),
        "n_games": len(clean_df),
        "mean_prediction": np.mean(probs),
        "std_prediction": np.std(probs),
        "min_prediction": np.min(probs),
        "max_prediction": np.max(probs)
    }
    
    # Add accuracy if we have binary outcomes
    if np.all(np.isin(outcomes, [0, 1])):
        predictions = (probs > 0.5).astype(int)
        metrics["accuracy"] = np.mean(predictions == outcomes)
    
    return metrics


def compare_models(results: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Compare multiple model results side by side.
    
    Args:
        results: Dictionary mapping model names to their metrics
        
    Returns:
        DataFrame with comparison
    """
    if not results:
        return pd.DataFrame()
    
    # Get all unique metrics
    all_metrics = set()
    for model_metrics in results.values():
        all_metrics.update(model_metrics.keys())
    
    # Create comparison DataFrame
    comparison_data = []
    for model_name, metrics in results.items():
        row = {"model": model_name}
        for metric in sorted(all_metrics):
            row[metric] = metrics.get(metric, np.nan)
        comparison_data.append(row)
    
    return pd.DataFrame(comparison_data)
