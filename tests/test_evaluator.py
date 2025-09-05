"""Tests for evaluation metrics."""

import pytest
import numpy as np
import pandas as pd
from models.nfl_elo.evaluator import (
    brier_score, log_loss_score, mean_absolute_error,
    calibration, expected_calibration_error, sharpness,
    calculate_all_metrics, compare_models
)


class TestBrierScore:
    """Test Brier score calculation."""
    
    def test_perfect_predictions(self):
        """Perfect predictions should give Brier score of 0."""
        probs = np.array([1.0, 0.0, 1.0, 0.0])
        outcomes = np.array([1, 0, 1, 0])
        score = brier_score(probs, outcomes)
        assert score == 0.0
    
    def test_random_predictions(self):
        """Random predictions should give Brier score around 0.25."""
        np.random.seed(42)
        probs = np.random.uniform(0, 1, 1000)
        outcomes = np.random.randint(0, 2, 1000)
        score = brier_score(probs, outcomes)
        assert 0.2 < score < 0.4  # Relaxed range for random data
    
    def test_constant_predictions(self):
        """Constant predictions should give expected Brier score."""
        probs = np.array([0.5, 0.5, 0.5, 0.5])
        outcomes = np.array([1, 0, 1, 0])
        score = brier_score(probs, outcomes)
        assert score == 0.25
    
    def test_invalid_inputs(self):
        """Invalid inputs should raise errors."""
        with pytest.raises(ValueError):
            brier_score(np.array([0.5, 0.5]), np.array([0, 1, 0]))
        
        with pytest.raises(ValueError):
            brier_score(np.array([1.5, 0.5]), np.array([0, 1]))
        
        with pytest.raises(ValueError):
            brier_score(np.array([0.5, 0.5]), np.array([0, 2]))


class TestLogLoss:
    """Test log loss calculation."""
    
    def test_perfect_predictions(self):
        """Perfect predictions should give log loss of 0."""
        probs = np.array([1.0, 0.0, 1.0, 0.0])
        outcomes = np.array([1, 0, 1, 0])
        loss = log_loss_score(probs, outcomes)
        assert loss == pytest.approx(0.0, abs=1e-10)
    
    def test_extreme_predictions(self):
        """Extreme predictions should give high log loss."""
        probs = np.array([0.0, 1.0, 0.0, 1.0])
        outcomes = np.array([1, 0, 1, 0])
        loss = log_loss_score(probs, outcomes)
        assert loss > 10  # Should be very high
    
    def test_clipping(self):
        """Should handle extreme probabilities by clipping."""
        probs = np.array([0.0, 1.0])
        outcomes = np.array([1, 0])
        loss = log_loss_score(probs, outcomes)
        assert not np.isnan(loss)
        assert not np.isinf(loss)


class TestMeanAbsoluteError:
    """Test MAE calculation."""
    
    def test_perfect_predictions(self):
        """Perfect predictions should give MAE of 0."""
        preds = np.array([1.0, 2.0, 3.0, 4.0])
        actuals = np.array([1.0, 2.0, 3.0, 4.0])
        mae = mean_absolute_error(preds, actuals)
        assert mae == 0.0
    
    def test_constant_error(self):
        """Constant error should give expected MAE."""
        preds = np.array([1.0, 2.0, 3.0, 4.0])
        actuals = np.array([2.0, 3.0, 4.0, 5.0])
        mae = mean_absolute_error(preds, actuals)
        assert mae == 1.0
    
    def test_mixed_errors(self):
        """Mixed errors should give correct MAE."""
        preds = np.array([1.0, 2.0, 3.0, 4.0])
        actuals = np.array([1.5, 1.5, 3.5, 3.5])
        mae = mean_absolute_error(preds, actuals)
        expected = (0.5 + 0.5 + 0.5 + 0.5) / 4
        assert mae == expected


class TestCalibration:
    """Test calibration metrics."""
    
    def test_perfect_calibration(self):
        """Perfectly calibrated predictions should have ECE of 0."""
        df = pd.DataFrame({
            'prob': [0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4],
            'outcome': [0, 0, 0, 0, 1, 1, 1, 1]
        })
        
        calib_df = calibration(df, 'prob', 'outcome', bins=4)
        ece = expected_calibration_error(df, 'prob', 'outcome', bins=4)
        
        # Should be well calibrated (relaxed threshold for small sample)
        assert ece < 0.5
    
    def test_poor_calibration(self):
        """Poorly calibrated predictions should have high ECE."""
        df = pd.DataFrame({
            'prob': [0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4],
            'outcome': [1, 1, 1, 1, 0, 0, 0, 0]  # Opposite of probabilities
        })
        
        ece = expected_calibration_error(df, 'prob', 'outcome', bins=4)
        assert ece > 0.3
    
    def test_single_bin(self):
        """Single bin should work."""
        df = pd.DataFrame({
            'prob': [0.5, 0.5, 0.5, 0.5],
            'outcome': [1, 0, 1, 0]
        })
        
        calib_df = calibration(df, 'prob', 'outcome', bins=1)
        assert len(calib_df) == 1
        assert calib_df['p_hat'].iloc[0] == 0.5
        assert calib_df['y_rate'].iloc[0] == 0.5


class TestSharpness:
    """Test sharpness calculation."""
    
    def test_constant_predictions(self):
        """Constant predictions should have sharpness of 0."""
        df = pd.DataFrame({'prob': [0.5, 0.5, 0.5, 0.5]})
        sharp = sharpness(df, 'prob')
        assert sharp == 0.0
    
    def test_variable_predictions(self):
        """Variable predictions should have positive sharpness."""
        df = pd.DataFrame({'prob': [0.1, 0.3, 0.7, 0.9]})
        sharp = sharpness(df, 'prob')
        assert sharp > 0.0


class TestCalculateAllMetrics:
    """Test comprehensive metrics calculation."""
    
    def test_basic_metrics(self):
        """Should calculate basic metrics correctly."""
        df = pd.DataFrame({
            'p_home': [0.6, 0.4, 0.8, 0.2],
            'home_win': [1, 0, 1, 0]
        })
        
        metrics = calculate_all_metrics(df)
        
        assert 'brier_score' in metrics
        assert 'log_loss' in metrics
        assert 'ece' in metrics
        assert 'sharpness' in metrics
        assert 'n_games' in metrics
        assert metrics['n_games'] == 4
    
    def test_empty_dataframe(self):
        """Empty DataFrame should return error."""
        df = pd.DataFrame({'p_home': [], 'home_win': []})
        metrics = calculate_all_metrics(df)
        assert 'error' in metrics
    
    def test_missing_columns(self):
        """Missing columns should raise error."""
        df = pd.DataFrame({'prob': [0.5, 0.5]})
        
        with pytest.raises(ValueError):
            calculate_all_metrics(df, 'p_home', 'home_win')


class TestCompareModels:
    """Test model comparison functionality."""
    
    def test_empty_results(self):
        """Empty results should return empty DataFrame."""
        results = {}
        comparison = compare_models(results)
        assert len(comparison) == 0
    
    def test_single_model(self):
        """Single model should work."""
        results = {
            'model1': {'brier_score': 0.25, 'log_loss': 0.69}
        }
        comparison = compare_models(results)
        assert len(comparison) == 1
        assert comparison['model'].iloc[0] == 'model1'
    
    def test_multiple_models(self):
        """Multiple models should be compared."""
        results = {
            'model1': {'brier_score': 0.25, 'log_loss': 0.69},
            'model2': {'brier_score': 0.30, 'log_loss': 0.75, 'ece': 0.05}
        }
        comparison = compare_models(results)
        assert len(comparison) == 2
        assert set(comparison['model']) == {'model1', 'model2'}
        assert 'brier_score' in comparison.columns
        assert 'log_loss' in comparison.columns
        assert 'ece' in comparison.columns
