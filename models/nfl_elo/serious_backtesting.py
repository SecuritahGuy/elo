"""Serious backtesting with detailed analysis for ML-enhanced NFL Elo system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from .ml_feature_engineering_pregame import PreGameFeatureEngineer
from .ml_models_regularized import RegularizedMLTrainer
from ingest.nfl.data_loader import load_games


class SeriousBacktester:
    """Serious backtesting with detailed analysis and validation."""
    
    def __init__(self):
        """Initialize serious backtester."""
        self.feature_engineer = PreGameFeatureEngineer()
        self.ml_trainer = RegularizedMLTrainer()
        self.elo_config = EloConfig(
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
        self.results = {}
    
    def run_comprehensive_analysis(self, years: List[int]) -> Dict[str, Any]:
        """
        Run comprehensive backtesting analysis.
        
        Args:
            years: Years to analyze
            
        Returns:
            Comprehensive analysis results
        """
        print(f"🔍 SERIOUS BACKTESTING ANALYSIS")
        print(f"Years: {years}")
        print("="*80)
        
        all_results = {}
        
        for year in years:
            print(f"\\n📅 Analyzing {year}...")
            year_results = self._analyze_single_year(year)
            all_results[year] = year_results
        
        # Calculate overall performance
        overall_results = self._calculate_overall_performance(all_results)
        
        # Run baseline comparison
        baseline_results = self._run_baseline_comparison(years)
        
        # Detailed analysis
        detailed_analysis = self._perform_detailed_analysis(all_results, overall_results, baseline_results)
        
        return {
            'yearly_results': all_results,
            'overall_results': overall_results,
            'baseline_results': baseline_results,
            'detailed_analysis': detailed_analysis
        }
    
    def _analyze_single_year(self, year: int) -> Dict[str, Any]:
        """Analyze a single year with detailed breakdown."""
        # Load data
        games = load_games([year])
        
        if len(games) == 0:
            return {'error': f'No data for {year}'}
        
        print(f"  Loaded {len(games)} games for {year}")
        
        # Train on previous years (if available)
        if year > 2019:
            train_years = [y for y in range(2019, year) if y != 2020]
            if train_years:
                train_games = load_games(train_years)
                print(f"  Training on {len(train_games)} games from {train_years}")
                
                # Train ML system
                ml_features = self.feature_engineer.create_pregame_features(train_games, train_years)
                X, y = self.ml_trainer.prepare_data(train_games, train_years)
                ml_results = self.ml_trainer.train_regularized_models(X, y)
                
                # Calculate Elo predictions for current year
                elo_predictions = self._calculate_elo_predictions(games, [year])
                
                # Get ML predictions for current year
                X_test, y_test = self.ml_trainer.prepare_data(games, [year])
                ml_predictions = {}
                
                for model_name in ['neural_network', 'random_forest']:
                    if model_name in self.ml_trainer.models:
                        pred, prob = self.ml_trainer.predict(X_test, model_name)
                        ml_predictions[model_name] = {
                            'predictions': pred,
                            'probabilities': prob
                        }
                
                # Calculate ensemble predictions
                ensemble_predictions = []
                ensemble_probabilities = []
                
                for i in range(len(games)):
                    elo_prob = elo_predictions[i]
                    nn_prob = ml_predictions.get('neural_network', {}).get('probabilities', [0.5])[i]
                    rf_prob = ml_predictions.get('random_forest', {}).get('probabilities', [0.5])[i]
                    
                    # Simple ensemble (50% Elo, 50% ML)
                    ensemble_prob = 0.5 * elo_prob + 0.5 * nn_prob
                    ensemble_predictions.append(1 if ensemble_prob > 0.5 else 0)
                    ensemble_probabilities.append(ensemble_prob)
                
                # Calculate metrics
                y_true = (games['home_score'] > games['away_score']).astype(int)
                
                ml_accuracy = np.mean(ensemble_predictions == y_true)
                ml_brier = np.mean((np.array(ensemble_probabilities) - y_true) ** 2)
                
                # Calculate Elo metrics
                elo_predictions_binary = (np.array(elo_predictions) > 0.5).astype(int)
                elo_accuracy = np.mean(elo_predictions_binary == y_true)
                elo_brier = np.mean((np.array(elo_predictions) - y_true) ** 2)
                
                return {
                    'year': year,
                    'games_processed': len(games),
                    'ml_ensemble': {
                        'accuracy': ml_accuracy,
                        'brier_score': ml_brier,
                        'predictions': ensemble_predictions,
                        'probabilities': ensemble_probabilities
                    },
                    'elo_baseline': {
                        'accuracy': elo_accuracy,
                        'brier_score': elo_brier,
                        'predictions': elo_predictions_binary,
                        'probabilities': elo_predictions
                    },
                    'improvement': {
                        'accuracy_improvement': ml_accuracy - elo_accuracy,
                        'brier_improvement': elo_brier - ml_brier
                    }
                }
            else:
                # No training data available
                return {
                    'year': year,
                    'games_processed': len(games),
                    'error': 'No training data available'
                }
        else:
            # No training data available
            return {
                'year': year,
                'games_processed': len(games),
                'error': 'No training data available'
            }
    
    def _calculate_elo_predictions(self, games: pd.DataFrame, years: List[int]) -> np.ndarray:
        """Calculate Elo-based predictions."""
        elo_result = run_backtest(games, self.elo_config)
        
        elo_predictions = []
        for _, game in games.iterrows():
            home_rating = elo_result.get('final_ratings', {}).get(game['home_team'], 1500)
            away_rating = elo_result.get('final_ratings', {}).get(game['away_team'], 1500)
            
            elo_diff = home_rating - away_rating + self.elo_config.hfa_points
            win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
            elo_predictions.append(win_prob)
        
        return np.array(elo_predictions)
    
    def _calculate_overall_performance(self, yearly_results: Dict[int, Dict]) -> Dict[str, Any]:
        """Calculate overall performance across all years."""
        print("\\n📊 Calculating overall performance...")
        
        total_games = 0
        total_ml_accuracy = 0
        total_ml_brier = 0
        total_elo_accuracy = 0
        total_elo_brier = 0
        valid_years = 0
        
        for year, results in yearly_results.items():
            if 'error' in results:
                continue
            
            valid_years += 1
            total_games += results['games_processed']
            
            ml_metrics = results['ml_ensemble']
            elo_metrics = results['elo_baseline']
            
            total_ml_accuracy += ml_metrics['accuracy']
            total_ml_brier += ml_metrics['brier_score']
            total_elo_accuracy += elo_metrics['accuracy']
            total_elo_brier += elo_metrics['brier_score']
        
        if valid_years == 0:
            return {'error': 'No valid years found'}
        
        # Calculate averages
        avg_ml_accuracy = total_ml_accuracy / valid_years
        avg_ml_brier = total_ml_brier / valid_years
        avg_elo_accuracy = total_elo_accuracy / valid_years
        avg_elo_brier = total_elo_brier / valid_years
        
        return {
            'total_games': total_games,
            'valid_years': valid_years,
            'ml_ensemble': {
                'accuracy': avg_ml_accuracy,
                'brier_score': avg_ml_brier
            },
            'elo_baseline': {
                'accuracy': avg_elo_accuracy,
                'brier_score': avg_elo_brier
            },
            'improvements': {
                'accuracy_improvement': avg_ml_accuracy - avg_elo_accuracy,
                'brier_improvement': avg_elo_brier - avg_ml_brier
            }
        }
    
    def _run_baseline_comparison(self, years: List[int]) -> Dict[str, Any]:
        """Run baseline Elo comparison."""
        print("\\n🔍 Running baseline Elo comparison...")
        
        all_games = load_games(years)
        baseline_result = run_backtest(all_games, self.elo_config)
        
        return baseline_result
    
    def _perform_detailed_analysis(self, yearly_results: Dict, overall_results: Dict, baseline_results: Dict) -> Dict[str, Any]:
        """Perform detailed analysis of results."""
        print("\\n🔬 Performing detailed analysis...")
        
        analysis = {
            'suspicious_metrics': [],
            'data_quality_issues': [],
            'overfitting_indicators': [],
            'recommendations': []
        }
        
        # Check for suspicious metrics
        if overall_results.get('ml_ensemble', {}).get('accuracy', 0) > 0.75:
            analysis['suspicious_metrics'].append(f"ML accuracy {overall_results['ml_ensemble']['accuracy']:.3f} seems too high")
        
        if overall_results.get('elo_baseline', {}).get('accuracy', 0) > 0.70:
            analysis['suspicious_metrics'].append(f"Elo accuracy {overall_results['elo_baseline']['accuracy']:.3f} seems too high")
        
        # Check for overfitting indicators
        for year, results in yearly_results.items():
            if 'error' in results:
                continue
            
            ml_acc = results['ml_ensemble']['accuracy']
            elo_acc = results['elo_baseline']['accuracy']
            
            if ml_acc > 0.80:
                analysis['overfitting_indicators'].append(f"{year}: ML accuracy {ml_acc:.3f} suspiciously high")
            
            if elo_acc > 0.75:
                analysis['overfitting_indicators'].append(f"{year}: Elo accuracy {elo_acc:.3f} suspiciously high")
        
        # Check for data quality issues
        if overall_results.get('total_games', 0) < 100:
            analysis['data_quality_issues'].append("Low number of games for analysis")
        
        # Generate recommendations
        if analysis['suspicious_metrics']:
            analysis['recommendations'].append("Investigate suspiciously high accuracy metrics")
        
        if analysis['overfitting_indicators']:
            analysis['recommendations'].append("Check for overfitting in individual years")
        
        if analysis['data_quality_issues']:
            analysis['recommendations'].append("Improve data quality and quantity")
        
        return analysis
    
    def generate_detailed_report(self, results: Dict[str, Any]) -> str:
        """Generate detailed analysis report."""
        report = []
        report.append("🔍 SERIOUS BACKTESTING ANALYSIS REPORT")
        report.append("="*80)
        
        # Overall performance
        overall = results['overall_results']
        if 'error' not in overall:
            report.append(f"\\n📊 OVERALL PERFORMANCE ({overall['valid_years']} years, {overall['total_games']} games)")
            report.append("-" * 50)
            
            ml_metrics = overall['ml_ensemble']
            elo_metrics = overall['elo_baseline']
            improvements = overall['improvements']
            
            report.append(f"ML Ensemble    : Accuracy={ml_metrics['accuracy']:.3f}, Brier={ml_metrics['brier_score']:.3f}")
            report.append(f"Elo Baseline   : Accuracy={elo_metrics['accuracy']:.3f}, Brier={elo_metrics['brier_score']:.3f}")
            report.append(f"Improvements   : Accuracy={improvements['accuracy_improvement']:+.3f}, Brier={improvements['brier_improvement']:+.3f}")
        
        # Yearly breakdown
        report.append(f"\\n📅 YEARLY BREAKDOWN")
        report.append("-" * 50)
        
        for year, year_results in results['yearly_results'].items():
            if 'error' in year_results:
                report.append(f"{year}: {year_results['error']}")
                continue
            
            ml_metrics = year_results['ml_ensemble']
            elo_metrics = year_results['elo_baseline']
            improvement = year_results['improvement']
            
            report.append(f"{year}: ML={ml_metrics['accuracy']:.3f} vs Elo={elo_metrics['accuracy']:.3f} (Δ{improvement['accuracy_improvement']:+.3f})")
        
        # Detailed analysis
        analysis = results['detailed_analysis']
        report.append(f"\\n🔬 DETAILED ANALYSIS")
        report.append("-" * 50)
        
        if analysis['suspicious_metrics']:
            report.append("⚠️  SUSPICIOUS METRICS:")
            for metric in analysis['suspicious_metrics']:
                report.append(f"  - {metric}")
        
        if analysis['overfitting_indicators']:
            report.append("\\n⚠️  OVERFITTING INDICATORS:")
            for indicator in analysis['overfitting_indicators']:
                report.append(f"  - {indicator}")
        
        if analysis['data_quality_issues']:
            report.append("\\n⚠️  DATA QUALITY ISSUES:")
            for issue in analysis['data_quality_issues']:
                report.append(f"  - {issue}")
        
        if analysis['recommendations']:
            report.append("\\n💡 RECOMMENDATIONS:")
            for rec in analysis['recommendations']:
                report.append(f"  - {rec}")
        
        return "\\n".join(report)


def test_serious_backtesting():
    """Test serious backtesting system."""
    print("🔍 TESTING SERIOUS BACKTESTING")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create backtester
    backtester = SeriousBacktester()
    
    # Run comprehensive analysis
    results = backtester.run_comprehensive_analysis(years)
    
    # Generate detailed report
    report = backtester.generate_detailed_report(results)
    print("\\n" + report)
    
    return backtester, results


if __name__ == "__main__":
    backtester, results = test_serious_backtesting()
