"""Analyze travel impact with cross-country games."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path

from .config import EloConfig
from .backtest import run_backtest
from .enhanced_elo_system import EnhancedEloSystem
from .evaluator import calculate_all_metrics
from ingest.nfl.data_loader import load_games
from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context
from ingest.nfl.weather_loader import load_weather_data_with_retry
from ingest.nfl.qb_data_loader import load_qb_performance
from ingest.nfl.travel_calculator import TravelCalculator
from models.nfl_elo.enhanced_qb_performance import EnhancedQBPerformanceTracker
from models.nfl_elo.adjusted_epa_calculator import AdjustedEPACalculator


class TravelImpactAnalyzer:
    """Analyze travel impact with different distances and timezone changes."""
    
    def __init__(self, years: List[int] = [2022, 2023]):
        """Initialize the travel impact analyzer."""
        self.years = years
        self.results = {}
        
        # Load data
        print("Loading data for travel impact analysis...")
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
        
        # Initialize travel calculator
        self.travel_calculator = TravelCalculator()
        
        # Initialize components
        self.enhanced_qb_tracker = EnhancedQBPerformanceTracker(
            qb_data=self.qb_data,
            games_data=self.games,
            adjusted_epa_data=self.epa_data
        )
        
        self.adjusted_epa_calculator = AdjustedEPACalculator(self.epa_data)
        
    def analyze_travel_conditions(self) -> Dict[str, Any]:
        """Analyze games by travel distance and conditions."""
        print("\nAnalyzing travel conditions...")
        
        # Calculate travel data for all games
        travel_data = self.travel_calculator.add_travel_data_to_games(self.games)
        
        # Categorize games by travel distance
        travel_categories = self._categorize_travel_conditions(travel_data)
        
        # Test each category
        results = {}
        for category, games in travel_categories.items():
            if len(games) < 10:  # Skip categories with too few games
                continue
                
            print(f"\nTesting {category} ({len(games)} games)...")
            result = self._test_travel_category(category, games)
            results[category] = result
            
        return results
    
    def _categorize_travel_conditions(self, travel_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Categorize games by travel distance and conditions."""
        categories = {}
        
        # Merge games with travel data
        merged = self.games.merge(
            travel_data[['season', 'week', 'home_team', 'away_team', 'travel_distance', 'time_zones_crossed', 'travel_fatigue', 'recovery_days_needed']], 
            on=['season', 'week', 'home_team', 'away_team'], 
            how='left'
        )
        
        # Define travel categories based on distance
        categories['local'] = merged[
            (merged['travel_distance'] <= 200)  # Local/regional games
        ].copy()
        
        categories['regional'] = merged[
            (merged['travel_distance'] > 200) & (merged['travel_distance'] <= 800)  # Regional games
        ].copy()
        
        categories['cross_country'] = merged[
            (merged['travel_distance'] > 800) & (merged['travel_distance'] <= 2000)  # Cross-country games
        ].copy()
        
        categories['coast_to_coast'] = merged[
            (merged['travel_distance'] > 2000)  # Coast-to-coast games
        ].copy()
        
        # Timezone change categories
        categories['same_timezone'] = merged[
            (merged['time_zones_crossed'] == 0)  # No timezone change
        ].copy()
        
        categories['one_timezone'] = merged[
            (merged['time_zones_crossed'] == 1)  # One timezone change
        ].copy()
        
        categories['multiple_timezones'] = merged[
            (merged['time_zones_crossed'] >= 2)  # Multiple timezone changes
        ].copy()
        
        # Print category statistics
        for category, games in categories.items():
            print(f"{category}: {len(games)} games")
            if len(games) > 0:
                print(f"  Avg distance: {games['travel_distance'].mean():.1f} miles")
                print(f"  Avg timezones: {games['time_zones_crossed'].mean():.1f}")
                print(f"  Avg fatigue: {games['travel_fatigue'].mean():.3f}")
                print(f"  Avg recovery: {games['recovery_days_needed'].mean():.3f}")
        
        return categories
    
    def _test_travel_category(self, category: str, games: pd.DataFrame) -> Dict[str, Any]:
        """Test a specific travel category."""
        # Create configurations
        baseline_config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=False,
            use_qb_adjustment=False
        )
        
        travel_config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            travel_adjustment_weight=1.0,
            travel_max_delta=3.0,
            use_qb_adjustment=False
        )
        
        # Run baseline backtest
        baseline_result = run_backtest(games, baseline_config)
        
        # Run travel-adjusted backtest
        travel_result = run_backtest(games, travel_config, weather_data=self.weather_data)
        
        # Calculate improvement
        baseline_brier = baseline_result['metrics']['brier_score']
        travel_brier = travel_result['metrics']['brier_score']
        improvement = ((baseline_brier - travel_brier) / baseline_brier) * 100
        
        # Analyze travel impact
        travel_impact = self._analyze_travel_impact(games)
        
        return {
            'category': category,
            'num_games': len(games),
            'baseline_metrics': baseline_result['metrics'],
            'travel_metrics': travel_result['metrics'],
            'improvement_pct': improvement,
            'travel_impact': travel_impact,
            'travel_stats': {
                'avg_distance': games['travel_distance'].mean(),
                'max_distance': games['travel_distance'].max(),
                'avg_timezones': games['time_zones_crossed'].mean(),
                'avg_fatigue': games['travel_fatigue'].mean(),
                'avg_recovery': games['recovery_days_needed'].mean()
            }
        }
    
    def _analyze_travel_impact(self, games: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the impact of travel on game outcomes."""
        # Calculate travel adjustments for each game
        travel_impacts = []
        
        for idx, game in games.iterrows():
            # Calculate travel impact
            distance = game['travel_distance']
            timezones = game['time_zones_crossed']
            fatigue = game['travel_fatigue']
            recovery = game['recovery_days_needed']
            
            # Calculate travel impact based on our model
            distance_impact = self._calculate_distance_impact(distance)
            timezone_impact = self._calculate_timezone_impact(timezones)
            fatigue_impact = self._calculate_fatigue_impact(fatigue)
            recovery_impact = self._calculate_recovery_impact(recovery)
            
            total_impact = distance_impact + timezone_impact + fatigue_impact + recovery_impact
            
            travel_impacts.append({
                'game_id': f"{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}",
                'distance': distance,
                'timezones': timezones,
                'fatigue': fatigue,
                'recovery': recovery,
                'distance_impact': distance_impact,
                'timezone_impact': timezone_impact,
                'fatigue_impact': fatigue_impact,
                'recovery_impact': recovery_impact,
                'total_impact': total_impact
            })
        
        if not travel_impacts:
            return {'error': 'No travel data available'}
        
        impacts_df = pd.DataFrame(travel_impacts)
        
        return {
            'total_games': len(impacts_df),
            'avg_impact': impacts_df['total_impact'].mean(),
            'max_impact': impacts_df['total_impact'].max(),
            'min_impact': impacts_df['total_impact'].min(),
            'distance_impact_avg': impacts_df['distance_impact'].mean(),
            'timezone_impact_avg': impacts_df['timezone_impact'].mean(),
            'fatigue_impact_avg': impacts_df['fatigue_impact'].mean(),
            'recovery_impact_avg': impacts_df['recovery_impact'].mean(),
            'high_impact_games': len(impacts_df[impacts_df['total_impact'] > 1.0]),
            'long_distance_games': len(impacts_df[impacts_df['distance'] > 1500]),
            'cross_timezone_games': len(impacts_df[impacts_df['timezones'] >= 2])
        }
    
    def _calculate_distance_impact(self, distance: float) -> float:
        """Calculate distance impact on game."""
        if distance > 2000:
            return -2.0  # Coast-to-coast
        elif distance > 1000:
            return -1.0  # Cross-country
        elif distance > 500:
            return -0.5  # Regional
        else:
            return 0.0   # Local
    
    def _calculate_timezone_impact(self, timezones: int) -> float:
        """Calculate timezone change impact on game."""
        if timezones >= 3:
            return -1.5  # Multiple timezones
        elif timezones == 2:
            return -1.0  # Two timezones
        elif timezones == 1:
            return -0.5  # One timezone
        else:
            return 0.0   # Same timezone
    
    def _calculate_fatigue_impact(self, fatigue: float) -> float:
        """Calculate fatigue impact on game."""
        if fatigue > 0.8:
            return -1.0  # High fatigue
        elif fatigue > 0.5:
            return -0.5  # Moderate fatigue
        else:
            return 0.0   # Low fatigue
    
    def _calculate_recovery_impact(self, recovery: float) -> float:
        """Calculate recovery impact on game."""
        if recovery < 0.3:
            return -1.0  # Poor recovery
        elif recovery < 0.6:
            return -0.5  # Moderate recovery
        else:
            return 0.0   # Good recovery
    
    def print_travel_analysis(self, results: Dict[str, Any]):
        """Print travel impact analysis results."""
        print("\n" + "="*80)
        print("TRAVEL IMPACT ANALYSIS")
        print("="*80)
        
        for category, result in results.items():
            print(f"\n{category.upper()} TRAVEL CONDITIONS:")
            print(f"  Games: {result['num_games']}")
            print(f"  Travel Stats:")
            print(f"    Avg Distance: {result['travel_stats']['avg_distance']:.1f} miles")
            print(f"    Max Distance: {result['travel_stats']['max_distance']:.1f} miles")
            print(f"    Avg Timezones: {result['travel_stats']['avg_timezones']:.1f}")
            print(f"    Avg Fatigue: {result['travel_stats']['avg_fatigue']:.3f}")
            print(f"    Avg Recovery: {result['travel_stats']['avg_recovery']:.3f}")
            
            print(f"  Performance:")
            print(f"    Baseline Brier: {result['baseline_metrics']['brier_score']:.4f}")
            print(f"    Travel Brier: {result['travel_metrics']['brier_score']:.4f}")
            print(f"    Improvement: {result['improvement_pct']:.2f}%")
            
            if 'travel_impact' in result and 'error' not in result['travel_impact']:
                impact = result['travel_impact']
                print(f"  Travel Impact:")
                print(f"    Avg Impact: {impact['avg_impact']:.2f}")
                print(f"    Max Impact: {impact['max_impact']:.2f}")
                print(f"    High Impact Games: {impact['high_impact_games']}")
                print(f"    Long Distance Games: {impact['long_distance_games']}")
                print(f"    Cross Timezone Games: {impact['cross_timezone_games']}")
    
    def run_travel_analysis(self) -> Dict[str, Any]:
        """Run complete travel impact analysis."""
        print("Running travel impact analysis...")
        results = self.analyze_travel_conditions()
        self.print_travel_analysis(results)
        return results


def run_travel_impact_analysis(years: List[int] = [2022, 2023]):
    """Run travel impact analysis."""
    analyzer = TravelImpactAnalyzer(years=years)
    return analyzer.run_travel_analysis()


if __name__ == "__main__":
    results = run_travel_impact_analysis()
