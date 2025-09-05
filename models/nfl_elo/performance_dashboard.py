"""Performance comparison dashboard for environmental integrations."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path
from datetime import datetime

from .config import EloConfig
from .backtest import run_backtest
from .enhanced_elo_system import EnhancedEloSystem
from .evaluator import calculate_all_metrics
from ingest.nfl.data_loader import load_games
from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context
from ingest.nfl.weather_loader import load_weather_data_with_retry
from ingest.nfl.qb_data_loader import load_qb_performance
from models.nfl_elo.enhanced_qb_performance import EnhancedQBPerformanceTracker
from models.nfl_elo.adjusted_epa_calculator import AdjustedEPACalculator


class PerformanceDashboard:
    """Comprehensive performance comparison dashboard."""
    
    def __init__(self, years: List[int] = [2022, 2023], sample_size: int = 100):
        """Initialize the performance dashboard."""
        self.years = years
        self.sample_size = sample_size
        self.results = {}
        
        # Load data
        print("Loading data for performance dashboard...")
        self._load_data()
        
    def _load_data(self):
        """Load all required data."""
        # Load games data
        self.games = load_games(self.years)
        if self.sample_size:
            self.games = self.games.head(self.sample_size)
        print(f"Loaded {len(self.games)} games")
        
        # Load weather data
        self.weather_data = load_weather_data_with_retry(self.games)
        print(f"Loaded weather data for {len(self.weather_data)} games")
        
        # Load EPA data
        self.epa_data = load_epa_with_weather_and_travel_context(self.years, sample_size=2000)
        print(f"Loaded {len(self.epa_data)} EPA plays")
        
        # Load QB data
        self.qb_data = load_qb_performance(self.years)
        print(f"Loaded {len(self.qb_data)} QB performance records")
        
        # Initialize components
        self.enhanced_qb_tracker = EnhancedQBPerformanceTracker(
            qb_data=self.qb_data,
            games_data=self.games,
            adjusted_epa_data=self.epa_data
        )
        
        self.adjusted_epa_calculator = AdjustedEPACalculator(self.epa_data)
        
    def run_comprehensive_comparison(self) -> Dict[str, Any]:
        """Run comprehensive performance comparison."""
        print("\n" + "="*80)
        print("COMPREHENSIVE PERFORMANCE COMPARISON")
        print("="*80)
        
        # Test configurations
        configs = self._create_comparison_configurations()
        
        # Run all tests
        results = {}
        for config_name, config in configs.items():
            print(f"\nTesting {config_name}...")
            result = self._test_configuration(config_name, config)
            results[config_name] = result
            
        # Generate comprehensive analysis
        analysis = self._generate_comprehensive_analysis(results)
        results['analysis'] = analysis
        
        return results
    
    def _create_comparison_configurations(self) -> Dict[str, EloConfig]:
        """Create comprehensive comparison configurations."""
        configs = {}
        
        # 1. Baseline
        configs['baseline'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=False,
            use_travel_adjustment=False, use_qb_adjustment=False
        )
        
        # 2. Weather Only
        configs['weather_only'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=1.0, weather_max_delta=5.0,
            use_travel_adjustment=False, use_qb_adjustment=False
        )
        
        # 3. Travel Only
        configs['travel_only'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=False,
            use_travel_adjustment=True, travel_adjustment_weight=1.0,
            travel_max_delta=3.0, use_qb_adjustment=False
        )
        
        # 4. QB Only
        configs['qb_only'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=False,
            use_travel_adjustment=False, use_qb_adjustment=True,
            qb_adjustment_weight=1.0, qb_max_delta=10.0
        )
        
        # 5. Weather + Travel
        configs['weather_travel'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=1.0, weather_max_delta=5.0,
            use_travel_adjustment=True, travel_adjustment_weight=1.0,
            travel_max_delta=3.0, use_qb_adjustment=False
        )
        
        # 6. All Environmental
        configs['all_environmental'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=1.0, weather_max_delta=5.0,
            use_travel_adjustment=True, travel_adjustment_weight=1.0,
            travel_max_delta=3.0, use_qb_adjustment=True,
            qb_adjustment_weight=1.0, qb_max_delta=10.0
        )
        
        # 7. Optimized Configuration
        configs['optimized'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=0.5, weather_max_delta=3.0,
            use_travel_adjustment=True, travel_adjustment_weight=0.5,
            travel_max_delta=2.0, use_qb_adjustment=True,
            qb_adjustment_weight=1.5, qb_max_delta=5.0
        )
        
        # 8. Enhanced (with environmental EPA)
        configs['enhanced'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=0.5, weather_max_delta=3.0,
            use_travel_adjustment=True, travel_adjustment_weight=0.5,
            travel_max_delta=2.0, use_qb_adjustment=True,
            qb_adjustment_weight=1.5, qb_max_delta=5.0
        )
        
        return configs
    
    def _test_configuration(self, config_name: str, config: EloConfig) -> Dict[str, Any]:
        """Test a specific configuration."""
        if config_name == 'enhanced':
            # Use enhanced Elo system
            elo_system = EnhancedEloSystem(
                config=config,
                enhanced_qb_tracker=self.enhanced_qb_tracker,
                adjusted_epa_calculator=self.adjusted_epa_calculator
            )
            
            # Process games
            game_results = []
            for idx, game in self.games.iterrows():
                try:
                    result = elo_system.process_game(game)
                    game_results.append(result)
                except Exception as e:
                    print(f"Error processing game {idx}: {e}")
                    continue
            
            if not game_results:
                return {'error': 'No games processed successfully'}
            
            # Convert to DataFrame for metrics
            results_df = pd.DataFrame([
                {
                    'home_team': gr.home_team,
                    'away_team': gr.away_team,
                    'home_score': gr.home_score,
                    'away_score': gr.away_score,
                    'p_home': gr.p_home,
                    'actual_result': gr.actual_result,
                    'weather_impact': gr.weather_impact,
                    'travel_impact': gr.travel_impact,
                    'qb_impact': gr.qb_impact,
                    'epa_impact': gr.epa_impact,
                    'total_environmental_impact': gr.total_environmental_impact
                }
                for gr in game_results
            ])
            
            # Calculate metrics
            metrics_df = pd.DataFrame({
                'p_home': results_df['p_home'],
                'home_win': results_df['actual_result']
            })
            metrics = calculate_all_metrics(metrics_df)
            
            # Environmental breakdown
            environmental_breakdown = elo_system.get_environmental_breakdown()
            
            return {
                'config_name': config_name,
                'metrics': metrics,
                'environmental_breakdown': environmental_breakdown,
                'game_results': results_df,
                'total_games': len(game_results)
            }
        else:
            # Use standard backtest
            result = run_backtest(
                self.games, config, 
                qb_data=self.qb_data, 
                epa_data=self.epa_data, 
                weather_data=self.weather_data
            )
            
            return {
                'config_name': config_name,
                'metrics': result['metrics'],
                'environmental_breakdown': {},
                'game_results': result['history'],
                'total_games': len(result['history'])
            }
    
    def _generate_comprehensive_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis of all results."""
        analysis = {
            'summary_table': self._create_summary_table(results),
            'performance_ranking': self._rank_performances(results),
            'improvement_analysis': self._analyze_improvements(results),
            'environmental_impact_summary': self._summarize_environmental_impacts(results),
            'recommendations': self._generate_final_recommendations(results)
        }
        
        return analysis
    
    def _create_summary_table(self, results: Dict[str, Any]) -> pd.DataFrame:
        """Create comprehensive summary table."""
        summary_data = []
        
        for config_name, result in results.items():
            if config_name == 'analysis' or 'error' in result:
                continue
                
            metrics = result['metrics']
            summary_data.append({
                'Configuration': config_name,
                'Brier Score': metrics.get('brier_score', 0.0),
                'Log Loss': metrics.get('log_loss', 0.0),
                'Accuracy': metrics.get('accuracy', 0.0),
                'MAE': metrics.get('mae', 0.0),
                'Calibration': metrics.get('calibration', 0.0),
                'ECE': metrics.get('ece', 0.0),
                'Sharpness': metrics.get('sharpness', 0.0),
                'Total Games': result.get('total_games', 0)
            })
        
        return pd.DataFrame(summary_data)
    
    def _rank_performances(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank configurations by performance."""
        rankings = []
        
        for config_name, result in results.items():
            if config_name == 'analysis' or 'error' in result:
                continue
                
            metrics = result['metrics']
            rankings.append({
                'configuration': config_name,
                'brier_score': metrics.get('brier_score', 0.0),
                'accuracy': metrics.get('accuracy', 0.0),
                'calibration': metrics.get('calibration', 0.0)
            })
        
        # Sort by Brier score (lower is better)
        rankings.sort(key=lambda x: x['brier_score'])
        
        return rankings
    
    def _analyze_improvements(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze improvements over baseline."""
        baseline_brier = results.get('baseline', {}).get('metrics', {}).get('brier_score', 0.0)
        
        improvements = {}
        for config_name, result in results.items():
            if config_name in ['analysis', 'baseline'] or 'error' in result:
                continue
                
            brier_score = result['metrics']['brier_score']
            improvement = ((baseline_brier - brier_score) / baseline_brier) * 100
            
            improvements[config_name] = {
                'brier_score': brier_score,
                'improvement_pct': improvement,
                'is_better': improvement > 0
            }
        
        return improvements
    
    def _summarize_environmental_impacts(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize environmental impacts across configurations."""
        impacts = {}
        
        for config_name, result in results.items():
            if config_name == 'analysis' or 'error' in result:
                continue
                
            env_breakdown = result.get('environmental_breakdown', {})
            if env_breakdown:
                impacts[config_name] = {
                    'total_environmental_impact': env_breakdown.get('overall', {}).get('total_environmental_impact', 0.0),
                    'avg_environmental_impact_per_game': env_breakdown.get('overall', {}).get('avg_environmental_impact_per_game', 0.0),
                    'weather_impact': env_breakdown.get('weather', {}).get('total_impact', 0.0),
                    'travel_impact': env_breakdown.get('travel', {}).get('total_impact', 0.0),
                    'qb_impact': env_breakdown.get('qb', {}).get('total_impact', 0.0),
                    'epa_impact': env_breakdown.get('epa', {}).get('total_impact', 0.0)
                }
        
        return impacts
    
    def _generate_final_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate final recommendations based on all results."""
        recommendations = []
        
        # Find best performing configuration
        rankings = self._rank_performances(results)
        if rankings:
            best_config = rankings[0]
            recommendations.append(f"Best performing configuration: {best_config['configuration']} (Brier Score: {best_config['brier_score']:.4f})")
        
        # Analyze improvements
        improvements = self._analyze_improvements(results)
        best_improvement = max(improvements.values(), key=lambda x: x['improvement_pct'])
        if best_improvement['is_better']:
            recommendations.append(f"Best improvement: {best_improvement['improvement_pct']:.2f}% over baseline")
        
        # Environmental impact insights
        impacts = self._summarize_environmental_impacts(results)
        if 'enhanced' in impacts:
            enhanced_impact = impacts['enhanced']
            recommendations.append(f"Enhanced system shows {enhanced_impact['total_environmental_impact']:.1f} total environmental impact")
        
        # Weather data recommendation
        recommendations.append("Recommendation: Implement real weather data loading to maximize weather impact")
        
        return recommendations
    
    def print_dashboard(self, results: Dict[str, Any]):
        """Print comprehensive dashboard."""
        print("\n" + "="*80)
        print("ENVIRONMENTAL INTEGRATION PERFORMANCE DASHBOARD")
        print("="*80)
        
        # Print summary table
        if 'analysis' in results:
            summary_table = results['analysis']['summary_table']
            print("\nPERFORMANCE SUMMARY:")
            print(summary_table.to_string(index=False))
        
        # Print performance ranking
        if 'analysis' in results:
            print("\nPERFORMANCE RANKING:")
            rankings = results['analysis']['performance_ranking']
            for i, ranking in enumerate(rankings, 1):
                print(f"{i:2d}. {ranking['configuration']:20s} - Brier: {ranking['brier_score']:.4f}, Accuracy: {ranking['accuracy']:.3f}")
        
        # Print improvement analysis
        if 'analysis' in results:
            print("\nIMPROVEMENT ANALYSIS (vs Baseline):")
            improvements = results['analysis']['improvement_analysis']
            for config_name, improvement in improvements.items():
                status = "✓" if improvement['is_better'] else "✗"
                print(f"  {config_name:20s}: {improvement['improvement_pct']:+6.2f}% {status}")
        
        # Print environmental impact summary
        if 'analysis' in results:
            print("\nENVIRONMENTAL IMPACT SUMMARY:")
            impacts = results['analysis']['environmental_impact_summary']
            for config_name, impact in impacts.items():
                print(f"\n{config_name}:")
                print(f"  Total Environmental Impact: {impact['total_environmental_impact']:.2f}")
                print(f"  Avg Impact per Game: {impact['avg_environmental_impact_per_game']:.2f}")
                print(f"  Weather Impact: {impact['weather_impact']:.2f}")
                print(f"  Travel Impact: {impact['travel_impact']:.2f}")
                print(f"  QB Impact: {impact['qb_impact']:.2f}")
                print(f"  EPA Impact: {impact['epa_impact']:.2f}")
        
        # Print recommendations
        if 'analysis' in results:
            print("\nFINAL RECOMMENDATIONS:")
            recommendations = results['analysis']['recommendations']
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
    
    def save_dashboard(self, results: Dict[str, Any], filename: str = None):
        """Save dashboard results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_dashboard_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = {}
        for config_name, result in results.items():
            if config_name == 'analysis':
                json_results[config_name] = result
            else:
                json_results[config_name] = {
                    'config_name': result.get('config_name'),
                    'metrics': result.get('metrics'),
                    'environmental_breakdown': result.get('environmental_breakdown'),
                    'total_games': result.get('total_games')
                }
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif hasattr(obj, 'to_dict'):  # Handle DataFrames
                return obj.to_dict('records')
            else:
                return obj
        
        json_results = convert_numpy_types(json_results)
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"Dashboard results saved to {filename}")


def run_performance_dashboard(years: List[int] = [2022, 2023], sample_size: int = 100):
    """Run comprehensive performance dashboard."""
    dashboard = PerformanceDashboard(years=years, sample_size=sample_size)
    results = dashboard.run_comprehensive_comparison()
    dashboard.print_dashboard(results)
    dashboard.save_dashboard(results)
    return results


if __name__ == "__main__":
    results = run_performance_dashboard(sample_size=50)
