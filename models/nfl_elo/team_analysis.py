"""Team-specific analysis for environmental integrations."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path
from collections import defaultdict

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


class TeamAnalysis:
    """Analyze team-specific performance with environmental integrations."""
    
    def __init__(self, years: List[int] = [2022, 2023]):
        """Initialize the team analysis."""
        self.years = years
        self.results = {}
        
        # Load data
        print("Loading data for team analysis...")
        self._load_data()
        
    def _load_data(self):
        """Load all required data."""
        # Load games data
        self.games = load_games(self.years)
        print(f"Loaded {len(self.games)} games")
        
        # Load weather data
        self.weather_data = load_weather_data_with_retry(self.games)
        print(f"Loaded weather data for {len(self.weather_data)} games")
        
        # Load EPA data
        self.epa_data = load_epa_with_weather_and_travel_context(self.years, sample_size=5000)
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
        
    def analyze_team_performance(self) -> Dict[str, Any]:
        """Analyze team-specific performance with different configurations."""
        print("\n" + "="*80)
        print("TEAM-SPECIFIC PERFORMANCE ANALYSIS")
        print("="*80)
        
        # Get all unique teams
        all_teams = set(self.games['home_team'].unique()) | set(self.games['away_team'].unique())
        print(f"Analyzing {len(all_teams)} teams...")
        
        # Test configurations
        configs = self._create_team_configurations()
        
        # Analyze each team
        team_results = {}
        for team in sorted(all_teams):
            print(f"\nAnalyzing {team}...")
            team_games = self._get_team_games(team)
            
            if len(team_games) < 10:  # Skip teams with too few games
                continue
                
            team_analysis = self._analyze_single_team(team, team_games, configs)
            team_results[team] = team_analysis
            
        # Generate team comparisons
        comparisons = self._generate_team_comparisons(team_results)
        
        return {
            'team_results': team_results,
            'comparisons': comparisons,
            'summary': self._generate_team_summary(team_results)
        }
    
    def _create_team_configurations(self) -> Dict[str, EloConfig]:
        """Create configurations for team analysis."""
        configs = {}
        
        # Baseline
        configs['baseline'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=False,
            use_travel_adjustment=False, use_qb_adjustment=False
        )
        
        # Travel only (best performing from full season tests)
        configs['travel_only'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=False,
            use_travel_adjustment=True, travel_adjustment_weight=1.0,
            travel_max_delta=3.0, use_qb_adjustment=False
        )
        
        # All environmental
        configs['all_environmental'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=1.0, weather_max_delta=5.0,
            use_travel_adjustment=True, travel_adjustment_weight=1.0,
            travel_max_delta=3.0, use_qb_adjustment=True,
            qb_adjustment_weight=1.0, qb_max_delta=10.0
        )
        
        # Enhanced
        configs['enhanced'] = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=0.5, weather_max_delta=3.0,
            use_travel_adjustment=True, travel_adjustment_weight=0.5,
            travel_max_delta=2.0, use_qb_adjustment=True,
            qb_adjustment_weight=1.5, qb_max_delta=5.0
        )
        
        return configs
    
    def _get_team_games(self, team: str) -> pd.DataFrame:
        """Get all games for a specific team."""
        team_games = self.games[
            (self.games['home_team'] == team) | (self.games['away_team'] == team)
        ].copy()
        return team_games
    
    def _analyze_single_team(self, team: str, team_games: pd.DataFrame, configs: Dict[str, EloConfig]) -> Dict[str, Any]:
        """Analyze a single team's performance."""
        team_analysis = {
            'team': team,
            'total_games': len(team_games),
            'configurations': {}
        }
        
        for config_name, config in configs.items():
            try:
                if config_name == 'enhanced':
                    # Use enhanced Elo system
                    elo_system = EnhancedEloSystem(
                        config=config,
                        enhanced_qb_tracker=self.enhanced_qb_tracker,
                        adjusted_epa_calculator=self.adjusted_epa_calculator
                    )
                    
                    # Process games
                    game_results = []
                    for idx, game in team_games.iterrows():
                        try:
                            result = elo_system.process_game(game)
                            game_results.append(result)
                        except Exception as e:
                            continue
                    
                    if not game_results:
                        continue
                    
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
                    
                    team_analysis['configurations'][config_name] = {
                        'metrics': metrics,
                        'environmental_breakdown': environmental_breakdown,
                        'game_results': results_df,
                        'total_games': len(game_results)
                    }
                    
                else:
                    # Use standard backtest
                    result = run_backtest(
                        team_games, config, 
                        qb_data=self.qb_data, 
                        epa_data=self.epa_data, 
                        weather_data=self.weather_data
                    )
                    
                    team_analysis['configurations'][config_name] = {
                        'metrics': result['metrics'],
                        'environmental_breakdown': {},
                        'game_results': result['history'],
                        'total_games': len(result['history'])
                    }
                    
            except Exception as e:
                print(f"  Error analyzing {team} with {config_name}: {e}")
                continue
        
        return team_analysis
    
    def _generate_team_comparisons(self, team_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate team comparisons."""
        comparisons = {
            'best_improvements': [],
            'worst_performers': [],
            'environmental_impact_leaders': [],
            'accuracy_leaders': []
        }
        
        for team, analysis in team_results.items():
            if 'baseline' not in analysis['configurations']:
                continue
                
            baseline_metrics = analysis['configurations']['baseline']['metrics']
            baseline_brier = baseline_metrics['brier_score']
            baseline_accuracy = baseline_metrics['accuracy']
            
            # Find best improvement
            best_improvement = 0
            best_config = None
            for config_name, config_data in analysis['configurations'].items():
                if config_name == 'baseline':
                    continue
                    
                brier_score = config_data['metrics']['brier_score']
                improvement = ((baseline_brier - brier_score) / baseline_brier) * 100
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_config = config_name
            
            if best_config:
                comparisons['best_improvements'].append({
                    'team': team,
                    'improvement': best_improvement,
                    'best_config': best_config,
                    'baseline_brier': baseline_brier
                })
            
            # Track accuracy leaders
            comparisons['accuracy_leaders'].append({
                'team': team,
                'accuracy': baseline_accuracy,
                'total_games': analysis['total_games']
            })
            
            # Track environmental impact leaders
            if 'enhanced' in analysis['configurations']:
                env_breakdown = analysis['configurations']['enhanced']['environmental_breakdown']
                total_impact = env_breakdown.get('overall', {}).get('total_environmental_impact', 0)
                comparisons['environmental_impact_leaders'].append({
                    'team': team,
                    'total_impact': total_impact,
                    'avg_impact_per_game': env_breakdown.get('overall', {}).get('avg_environmental_impact_per_game', 0)
                })
        
        # Sort by improvement
        comparisons['best_improvements'].sort(key=lambda x: x['improvement'], reverse=True)
        comparisons['accuracy_leaders'].sort(key=lambda x: x['accuracy'], reverse=True)
        comparisons['environmental_impact_leaders'].sort(key=lambda x: x['total_impact'], reverse=True)
        
        return comparisons
    
    def _generate_team_summary(self, team_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate team summary statistics."""
        summary = {
            'total_teams_analyzed': len(team_results),
            'teams_with_improvements': 0,
            'average_improvement': 0,
            'best_team_improvement': 0,
            'environmental_impact_stats': {}
        }
        
        improvements = []
        for team, analysis in team_results.items():
            if 'baseline' not in analysis['configurations']:
                continue
                
            baseline_brier = analysis['configurations']['baseline']['metrics']['brier_score']
            
            # Find best improvement for this team
            best_improvement = 0
            for config_name, config_data in analysis['configurations'].items():
                if config_name == 'baseline':
                    continue
                    
                brier_score = config_data['metrics']['brier_score']
                improvement = ((baseline_brier - brier_score) / baseline_brier) * 100
                best_improvement = max(best_improvement, improvement)
            
            if best_improvement > 0:
                summary['teams_with_improvements'] += 1
                improvements.append(best_improvement)
                summary['best_team_improvement'] = max(summary['best_team_improvement'], best_improvement)
        
        if improvements:
            summary['average_improvement'] = np.mean(improvements)
        
        return summary
    
    def print_team_analysis(self, results: Dict[str, Any]):
        """Print team analysis results."""
        print("\n" + "="*80)
        print("TEAM-SPECIFIC PERFORMANCE ANALYSIS RESULTS")
        print("="*80)
        
        # Print summary
        summary = results['summary']
        print(f"\nSUMMARY:")
        print(f"  Total Teams Analyzed: {summary['total_teams_analyzed']}")
        print(f"  Teams with Improvements: {summary['teams_with_improvements']}")
        print(f"  Average Improvement: {summary['average_improvement']:.2f}%")
        print(f"  Best Team Improvement: {summary['best_team_improvement']:.2f}%")
        
        # Print best improvements
        print(f"\nTOP 10 TEAM IMPROVEMENTS:")
        comparisons = results['comparisons']
        for i, team_improvement in enumerate(comparisons['best_improvements'][:10], 1):
            print(f"{i:2d}. {team_improvement['team']:4s} - {team_improvement['improvement']:+6.2f}% ({team_improvement['best_config']})")
        
        # Print accuracy leaders
        print(f"\nTOP 10 ACCURACY LEADERS:")
        for i, team_accuracy in enumerate(comparisons['accuracy_leaders'][:10], 1):
            print(f"{i:2d}. {team_accuracy['team']:4s} - {team_accuracy['accuracy']:.3f} ({team_accuracy['total_games']} games)")
        
        # Print environmental impact leaders
        print(f"\nTOP 10 ENVIRONMENTAL IMPACT LEADERS:")
        for i, team_impact in enumerate(comparisons['environmental_impact_leaders'][:10], 1):
            print(f"{i:2d}. {team_impact['team']:4s} - {team_impact['total_impact']:+.1f} total, {team_impact['avg_impact_per_game']:+.2f} per game")
    
    def save_team_analysis(self, results: Dict[str, Any], filename: str = None):
        """Save team analysis results to file."""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"team_analysis_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = {}
        for team, analysis in results['team_results'].items():
            json_analysis = {
                'team': analysis['team'],
                'total_games': analysis['total_games'],
                'configurations': {}
            }
            
            for config_name, config_data in analysis['configurations'].items():
                json_analysis['configurations'][config_name] = {
                    'metrics': config_data['metrics'],
                    'environmental_breakdown': config_data['environmental_breakdown'],
                    'total_games': config_data['total_games']
                }
            
            json_results[team] = json_analysis
        
        json_results['comparisons'] = results['comparisons']
        json_results['summary'] = results['summary']
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"Team analysis results saved to {filename}")


def run_team_analysis(years: List[int] = [2022, 2023]):
    """Run team-specific analysis."""
    analyzer = TeamAnalysis(years=years)
    results = analyzer.analyze_team_performance()
    analyzer.print_team_analysis(results)
    analyzer.save_team_analysis(results)
    return results


if __name__ == "__main__":
    results = run_team_analysis()
