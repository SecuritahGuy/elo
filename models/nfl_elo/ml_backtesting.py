"""Comprehensive backtesting for ML-enhanced NFL Elo system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from .ml_ensemble import MLEnsembleSystem
from ingest.nfl.data_loader import load_games


class MLBacktester:
    """Comprehensive backtesting for ML-enhanced system."""
    
    def __init__(self):
        """Initialize ML backtester."""
        self.ensemble_system = MLEnsembleSystem()
        self.results = {}
    
    def run_comprehensive_backtest(self, years: List[int]) -> Dict[str, Any]:
        """
        Run comprehensive backtesting across multiple years.
        
        Args:
            years: Years to test
            
        Returns:
            Comprehensive backtest results
        """
        print(f"🏈 RUNNING COMPREHENSIVE ML BACKTEST")
        print(f"Years: {years}")
        print("="*80)
        
        all_results = {}
        
        for year in years:
            print(f"\\n📅 Testing {year}...")
            year_results = self._test_single_year(year)
            all_results[year] = year_results
        
        # Calculate overall performance
        overall_results = self._calculate_overall_performance(all_results)
        
        # Compare with baseline Elo
        baseline_results = self._run_baseline_comparison(years)
        
        # Generate summary
        summary = self._generate_summary(all_results, overall_results, baseline_results)
        
        return {
            'yearly_results': all_results,
            'overall_results': overall_results,
            'baseline_results': baseline_results,
            'summary': summary
        }
    
    def _test_single_year(self, year: int) -> Dict[str, Any]:
        """Test a single year."""
        # Load data
        games = load_games([year])
        
        if len(games) == 0:
            return {'error': f'No data for {year}'}
        
        # Train ensemble on previous years (if available)
        if year > 2019:
            train_years = [y for y in range(2019, year) if y != 2020]
            if train_years:
                train_games = load_games(train_years)
                self.ensemble_system.train_ensemble(train_games, train_years)
        
        # Evaluate on current year
        evaluation_results = self.ensemble_system.evaluate_ensemble(games, [year])
        
        # Run baseline Elo for comparison
        baseline_config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=False,
            use_downs_adjustment=False,
            use_clock_management_adjustment=False,
            use_situational_adjustment=False,
            use_turnover_adjustment=False
        )
        
        baseline_result = run_backtest(games, baseline_config)
        
        return {
            'year': year,
            'games_processed': len(games),
            'ml_ensemble': evaluation_results,
            'baseline_elo': {
                'brier_score': baseline_result.get('metrics', {}).get('brier_score', 0),
                'accuracy': baseline_result.get('metrics', {}).get('accuracy', 0),
                'log_loss': baseline_result.get('metrics', {}).get('log_loss', 0)
            }
        }
    
    def _calculate_overall_performance(self, yearly_results: Dict[int, Dict]) -> Dict[str, Any]:
        """Calculate overall performance across all years."""
        print("\\n📊 Calculating overall performance...")
        
        # Aggregate metrics
        total_games = 0
        total_accuracy = 0
        total_brier = 0
        total_log_loss = 0
        
        baseline_accuracy = 0
        baseline_brier = 0
        baseline_log_loss = 0
        
        valid_years = 0
        
        for year, results in yearly_results.items():
            if 'error' in results:
                continue
            
            valid_years += 1
            total_games += results['games_processed']
            
            # ML Ensemble metrics
            ml_metrics = results['ml_ensemble']
            total_accuracy += ml_metrics['accuracy']
            total_brier += ml_metrics['brier_score']
            total_log_loss += ml_metrics['log_loss']
            
            # Baseline metrics
            baseline_metrics = results['baseline_elo']
            baseline_accuracy += baseline_metrics['accuracy']
            baseline_brier += baseline_metrics['brier_score']
            baseline_log_loss += baseline_metrics['log_loss']
        
        if valid_years == 0:
            return {'error': 'No valid years found'}
        
        # Calculate averages
        avg_accuracy = total_accuracy / valid_years
        avg_brier = total_brier / valid_years
        avg_log_loss = total_log_loss / valid_years
        
        avg_baseline_accuracy = baseline_accuracy / valid_years
        avg_baseline_brier = baseline_brier / valid_years
        avg_baseline_log_loss = baseline_log_loss / valid_years
        
        # Calculate improvements
        accuracy_improvement = avg_accuracy - avg_baseline_accuracy
        brier_improvement = avg_baseline_brier - avg_brier  # Lower is better
        log_loss_improvement = avg_baseline_log_loss - avg_log_loss  # Lower is better
        
        return {
            'total_games': total_games,
            'valid_years': valid_years,
            'ml_ensemble': {
                'accuracy': avg_accuracy,
                'brier_score': avg_brier,
                'log_loss': avg_log_loss
            },
            'baseline_elo': {
                'accuracy': avg_baseline_accuracy,
                'brier_score': avg_baseline_brier,
                'log_loss': avg_baseline_log_loss
            },
            'improvements': {
                'accuracy_improvement': accuracy_improvement,
                'brier_improvement': brier_improvement,
                'log_loss_improvement': log_loss_improvement
            }
        }
    
    def _run_baseline_comparison(self, years: List[int]) -> Dict[str, Any]:
        """Run baseline Elo comparison."""
        print("\\n🔍 Running baseline Elo comparison...")
        
        # Load all data
        all_games = load_games(years)
        
        # Run baseline Elo
        baseline_config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=False,
            use_downs_adjustment=False,
            use_clock_management_adjustment=False,
            use_situational_adjustment=False,
            use_turnover_adjustment=False
        )
        
        baseline_result = run_backtest(all_games, baseline_config)
        
        return baseline_result
    
    def _generate_summary(self, yearly_results: Dict, overall_results: Dict, baseline_results: Dict) -> str:
        """Generate summary report."""
        summary = []
        summary.append("🏈 ML-ENHANCED NFL ELO SYSTEM - COMPREHENSIVE BACKTEST RESULTS")
        summary.append("="*80)
        
        if 'error' in overall_results:
            summary.append(f"❌ Error: {overall_results['error']}")
            return "\\n".join(summary)
        
        # Overall performance
        summary.append(f"📊 OVERALL PERFORMANCE ({overall_results['valid_years']} years, {overall_results['total_games']} games)")
        summary.append("-" * 50)
        
        ml_metrics = overall_results['ml_ensemble']
        baseline_metrics = overall_results['baseline_elo']
        improvements = overall_results['improvements']
        
        summary.append(f"ML Ensemble    : Accuracy={ml_metrics['accuracy']:.3f}, Brier={ml_metrics['brier_score']:.3f}, LogLoss={ml_metrics['log_loss']:.3f}")
        summary.append(f"Baseline Elo   : Accuracy={baseline_metrics['accuracy']:.3f}, Brier={baseline_metrics['brier_score']:.3f}, LogLoss={baseline_metrics['log_loss']:.3f}")
        summary.append(f"Improvements   : Accuracy={improvements['accuracy_improvement']:+.3f}, Brier={improvements['brier_improvement']:+.3f}, LogLoss={improvements['log_loss_improvement']:+.3f}")
        
        # Yearly breakdown
        summary.append(f"\\n📅 YEARLY BREAKDOWN")
        summary.append("-" * 50)
        
        for year, results in yearly_results.items():
            if 'error' in results:
                summary.append(f"{year}: {results['error']}")
                continue
            
            ml_metrics = results['ml_ensemble']
            baseline_metrics = results['baseline_elo']
            
            summary.append(f"{year}: ML={ml_metrics['accuracy']:.3f} vs Baseline={baseline_metrics['accuracy']:.3f} (Δ{ml_metrics['accuracy']-baseline_metrics['accuracy']:+.3f})")
        
        # Recommendations
        summary.append(f"\\n🎯 RECOMMENDATIONS")
        summary.append("-" * 50)
        
        if improvements['accuracy_improvement'] > 0.02:
            summary.append("✅ SIGNIFICANT IMPROVEMENT: ML ensemble shows meaningful accuracy gains")
        elif improvements['accuracy_improvement'] > 0.005:
            summary.append("✅ MODERATE IMPROVEMENT: ML ensemble shows modest accuracy gains")
        elif improvements['accuracy_improvement'] > 0:
            summary.append("✅ MINOR IMPROVEMENT: ML ensemble shows slight accuracy gains")
        else:
            summary.append("❌ NO IMPROVEMENT: ML ensemble does not improve over baseline Elo")
        
        if improvements['brier_improvement'] > 0.01:
            summary.append("✅ BETTER CALIBRATION: ML ensemble shows improved probability calibration")
        elif improvements['brier_improvement'] > 0:
            summary.append("✅ SLIGHTLY BETTER CALIBRATION: ML ensemble shows modest calibration improvement")
        else:
            summary.append("❌ NO CALIBRATION IMPROVEMENT: ML ensemble does not improve calibration")
        
        return "\\n".join(summary)


def test_ml_backtesting():
    """Test ML backtesting system."""
    print("🏈 TESTING ML BACKTESTING SYSTEM")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create backtester
    backtester = MLBacktester()
    
    # Run comprehensive backtest
    results = backtester.run_comprehensive_backtest(years)
    
    # Print summary
    print("\\n" + results['summary'])
    
    return backtester, results


if __name__ == "__main__":
    backtester, results = test_ml_backtesting()
