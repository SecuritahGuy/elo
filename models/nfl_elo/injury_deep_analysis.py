"""Deep injury analysis for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from .evaluator import calculate_all_metrics
from .injury_integration import InjuryImpactCalculator
from ingest.nfl.data_loader import load_games


class InjuryDeepAnalyzer:
    """Deep analysis of injury impact on NFL Elo ratings."""
    
    def __init__(self, years: List[int] = [2018, 2023]):
        """
        Initialize deep injury analyzer.
        
        Args:
            years: Years to analyze
        """
        self.years = years
        self.games = None
        self.injuries = None
        self.team_injury_df = None
        self.games_with_injuries = None
        self.injury_calculator = InjuryImpactCalculator()
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load all required data for deep injury analysis."""
        print("Loading data for deep injury analysis...")
        
        # Load games
        self.games = load_games(self.years)
        print(f"Loaded {len(self.games)} games")
        
        # Load injury data
        self.injuries = self.injury_calculator.load_injury_data(self.years)
        print(f"Loaded {len(self.injuries)} injury records")
        
        # Create team injury database
        self.team_injury_df = self.injury_calculator.create_team_injury_database(self.injuries)
        
        # Add injury data to games
        self.games_with_injuries = self.injury_calculator.add_injury_data_to_games(
            self.games, self.team_injury_df
        )
        print(f"Added injury data to {len(self.games_with_injuries)} games")
    
    def analyze_injury_impact_by_season(self) -> Dict[str, Any]:
        """Analyze injury impact by individual season."""
        print("\n📊 ANALYZING INJURY IMPACT BY SEASON")
        print("="*60)
        
        season_results = {}
        
        for season in self.years:
            print(f"\nAnalyzing {season} season...")
            
            # Filter games for this season
            season_games = self.games_with_injuries[self.games_with_injuries['season'] == season]
            
            if len(season_games) < 10:  # Skip if too few games
                continue
            
            print(f"  {len(season_games)} games in {season}")
            
            # Create configuration
            config = EloConfig(
                base_rating=1500.0,
                k=20.0,
                hfa_points=55.0,
                mov_enabled=True,
                preseason_regress=0.75,
                use_weather_adjustment=False,
                use_travel_adjustment=True,
                use_qb_adjustment=True,
                use_injury_adjustment=True,
                injury_adjustment_weight=2.0  # Use optimal weight from previous analysis
            )
            
            try:
                # Standard backtest
                standard_config = config.model_copy()
                standard_config.use_injury_adjustment = False
                standard_result = run_backtest(season_games, standard_config)
                standard_metrics = standard_result['metrics']
                
                # Injury-adjusted backtest
                injury_result = run_backtest(season_games, config)
                injury_metrics = injury_result['metrics']
                
                # Calculate improvement
                brier_improvement = ((standard_metrics['brier_score'] - injury_metrics['brier_score']) / 
                                   standard_metrics['brier_score']) * 100
                accuracy_improvement = injury_metrics['accuracy'] - standard_metrics['accuracy']
                
                season_results[season] = {
                    'games_count': len(season_games),
                    'standard_brier': standard_metrics['brier_score'],
                    'injury_brier': injury_metrics['brier_score'],
                    'brier_improvement_pct': brier_improvement,
                    'standard_accuracy': standard_metrics['accuracy'],
                    'injury_accuracy': injury_metrics['accuracy'],
                    'accuracy_improvement': accuracy_improvement,
                    'avg_home_injury_impact': season_games['home_injury_impact'].mean(),
                    'avg_away_injury_impact': season_games['away_injury_impact'].mean(),
                    'max_home_injury_impact': season_games['home_injury_impact'].max(),
                    'max_away_injury_impact': season_games['away_injury_impact'].max()
                }
                
                print(f"  Standard Brier: {standard_metrics['brier_score']:.4f}")
                print(f"  Injury Brier: {injury_metrics['brier_score']:.4f}")
                print(f"  Improvement: {brier_improvement:+.2f}%")
                print(f"  Avg Home Injury Impact: {season_games['home_injury_impact'].mean():.2f}")
                print(f"  Avg Away Injury Impact: {season_games['away_injury_impact'].mean():.2f}")
                
            except Exception as e:
                print(f"  Error analyzing {season}: {e}")
                season_results[season] = {'error': str(e)}
        
        return season_results
    
    def analyze_injury_impact_by_team_strength(self) -> Dict[str, Any]:
        """Analyze injury impact by team strength (based on Elo ratings)."""
        print("\n🏈 ANALYZING INJURY IMPACT BY TEAM STRENGTH")
        print("="*60)
        
        # Calculate team strength based on final Elo ratings
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False  # Use standard Elo for strength calculation
        )
        
        # Run backtest to get final ratings
        result = run_backtest(self.games_with_injuries, config)
        final_ratings = result['final_ratings']
        
        # Categorize teams by strength
        strength_categories = {
            'elite': [],      # >1600 rating
            'strong': [],     # 1500-1600 rating
            'average': [],    # 1400-1500 rating
            'weak': []        # <1400 rating
        }
        
        for team, rating in final_ratings.items():
            if rating > 1600:
                strength_categories['elite'].append(team)
            elif rating > 1500:
                strength_categories['strong'].append(team)
            elif rating > 1400:
                strength_categories['average'].append(team)
            else:
                strength_categories['weak'].append(team)
        
        print(f"Team strength distribution:")
        for category, teams in strength_categories.items():
            print(f"  {category}: {len(teams)} teams")
        
        # Analyze injury impact by team strength
        strength_results = {}
        
        for category, teams in strength_categories.items():
            if len(teams) < 3:  # Skip if too few teams
                continue
                
            print(f"\nAnalyzing {category} teams ({len(teams)} teams)...")
            
            # Filter games involving these teams
            category_games = self.games_with_injuries[
                (self.games_with_injuries['home_team'].isin(teams)) |
                (self.games_with_injuries['away_team'].isin(teams))
            ]
            
            if len(category_games) < 10:
                continue
            
            print(f"  {len(category_games)} games involving {category} teams")
            
            # Test injury impact
            config_with_injury = config.model_copy()
            config_with_injury.use_injury_adjustment = True
            config_with_injury.injury_adjustment_weight = 2.0
            
            try:
                # Standard backtest
                standard_result = run_backtest(category_games, config)
                standard_metrics = standard_result['metrics']
                
                # Injury-adjusted backtest
                injury_result = run_backtest(category_games, config_with_injury)
                injury_metrics = injury_result['metrics']
                
                # Calculate improvement
                brier_improvement = ((standard_metrics['brier_score'] - injury_metrics['brier_score']) / 
                                   standard_metrics['brier_score']) * 100
                
                strength_results[category] = {
                    'teams': teams,
                    'games_count': len(category_games),
                    'standard_brier': standard_metrics['brier_score'],
                    'injury_brier': injury_metrics['brier_score'],
                    'brier_improvement_pct': brier_improvement,
                    'avg_injury_impact': category_games[['home_injury_impact', 'away_injury_impact']].max(axis=1).mean()
                }
                
                print(f"  Standard Brier: {standard_metrics['brier_score']:.4f}")
                print(f"  Injury Brier: {injury_metrics['brier_score']:.4f}")
                print(f"  Improvement: {brier_improvement:+.2f}%")
                
            except Exception as e:
                print(f"  Error analyzing {category} teams: {e}")
                strength_results[category] = {'error': str(e)}
        
        return strength_results
    
    def analyze_high_impact_injury_scenarios(self) -> Dict[str, Any]:
        """Analyze specific high-impact injury scenarios."""
        print("\n🚨 ANALYZING HIGH-IMPACT INJURY SCENARIOS")
        print("="*60)
        
        # Find games with very high injury impact
        high_impact_games = self.games_with_injuries[
            (self.games_with_injuries['home_injury_impact'] > 5.0) |
            (self.games_with_injuries['away_injury_impact'] > 5.0)
        ]
        
        print(f"Games with very high injury impact (>5.0): {len(high_impact_games)}")
        
        if len(high_impact_games) > 0:
            print("\nSample high-impact injury games:")
            sample_cols = ['season', 'week', 'home_team', 'away_team', 'home_injury_impact', 
                          'away_injury_impact', 'home_injured_players', 'away_injured_players']
            print(high_impact_games[sample_cols].head(10))
        
        # Find games with QB injuries
        qb_injury_games = self.games_with_injuries[
            (self.games_with_injuries['home_key_position_injury_impact'] > 2.0) |
            (self.games_with_injuries['away_key_position_injury_impact'] > 2.0)
        ]
        
        print(f"\nGames with significant key position injuries (>2.0): {len(qb_injury_games)}")
        
        # Analyze these scenarios
        scenarios = {
            'high_impact': high_impact_games,
            'key_position': qb_injury_games
        }
        
        scenario_results = {}
        
        for scenario_name, scenario_games in scenarios.items():
            if len(scenario_games) < 5:
                continue
                
            print(f"\nAnalyzing {scenario_name} scenario ({len(scenario_games)} games)...")
            
            config = EloConfig(
                base_rating=1500.0,
                k=20.0,
                hfa_points=55.0,
                mov_enabled=True,
                preseason_regress=0.75,
                use_weather_adjustment=False,
                use_travel_adjustment=True,
                use_qb_adjustment=True,
                use_injury_adjustment=True,
                injury_adjustment_weight=2.0
            )
            
            try:
                # Standard backtest
                standard_config = config.model_copy()
                standard_config.use_injury_adjustment = False
                standard_result = run_backtest(scenario_games, standard_config)
                standard_metrics = standard_result['metrics']
                
                # Injury-adjusted backtest
                injury_result = run_backtest(scenario_games, config)
                injury_metrics = injury_result['metrics']
                
                # Calculate improvement
                brier_improvement = ((standard_metrics['brier_score'] - injury_metrics['brier_score']) / 
                                   standard_metrics['brier_score']) * 100
                
                scenario_results[scenario_name] = {
                    'games_count': len(scenario_games),
                    'standard_brier': standard_metrics['brier_score'],
                    'injury_brier': injury_metrics['brier_score'],
                    'brier_improvement_pct': brier_improvement,
                    'standard_accuracy': standard_metrics['accuracy'],
                    'injury_accuracy': injury_metrics['accuracy']
                }
                
                print(f"  Standard Brier: {standard_metrics['brier_score']:.4f}")
                print(f"  Injury Brier: {injury_metrics['brier_score']:.4f}")
                print(f"  Improvement: {brier_improvement:+.2f}%")
                
            except Exception as e:
                print(f"  Error analyzing {scenario_name}: {e}")
                scenario_results[scenario_name] = {'error': str(e)}
        
        return scenario_results
    
    def test_injury_weight_sensitivity(self) -> Dict[str, Any]:
        """Test sensitivity to different injury weight ranges."""
        print("\n⚖️ TESTING INJURY WEIGHT SENSITIVITY")
        print("="*60)
        
        # Test different weight ranges
        weight_ranges = [
            (0.0, 1.0, 0.1),    # Low range
            (1.0, 3.0, 0.2),    # Medium range
            (3.0, 5.0, 0.5),    # High range
        ]
        
        all_results = []
        
        for start, end, step in weight_ranges:
            print(f"\nTesting weights from {start} to {end} (step {step})...")
            
            weights = np.arange(start, end + step, step)
            range_results = []
            
            for weight in weights:
                config = EloConfig(
                    base_rating=1500.0,
                    k=20.0,
                    hfa_points=55.0,
                    mov_enabled=True,
                    preseason_regress=0.75,
                    use_weather_adjustment=False,
                    use_travel_adjustment=True,
                    use_qb_adjustment=True,
                    use_injury_adjustment=True,
                    injury_adjustment_weight=weight
                )
                
                try:
                    # Run backtest on sample
                    sample_games = self.games_with_injuries.head(200)
                    result = run_backtest(sample_games, config)
                    metrics = result['metrics']
                    
                    range_results.append({
                        'weight': weight,
                        'brier_score': metrics['brier_score'],
                        'accuracy': metrics['accuracy'],
                        'log_loss': metrics['log_loss']
                    })
                    
                    print(f"  Weight {weight:.1f}: Brier {metrics['brier_score']:.4f}")
                    
                except Exception as e:
                    print(f"  Weight {weight:.1f}: Error - {e}")
                    range_results.append({
                        'weight': weight,
                        'brier_score': float('inf'),
                        'accuracy': 0.0,
                        'log_loss': float('inf')
                    })
            
            all_results.extend(range_results)
        
        # Find best weight
        results_df = pd.DataFrame(all_results)
        best_idx = results_df['brier_score'].idxmin()
        best_result = results_df.iloc[best_idx]
        
        print(f"\nWeight Sensitivity Results:")
        print(f"Best weight: {best_result['weight']:.1f}")
        print(f"Best Brier Score: {best_result['brier_score']:.4f}")
        
        return {
            'all_results': all_results,
            'best_weight': best_result['weight'],
            'best_brier_score': best_result['brier_score']
        }
    
    def run_comprehensive_deep_analysis(self) -> Dict[str, Any]:
        """Run comprehensive deep injury analysis."""
        print("🔍 COMPREHENSIVE DEEP INJURY ANALYSIS")
        print("="*80)
        
        # Run all analyses
        season_results = self.analyze_injury_impact_by_season()
        strength_results = self.analyze_injury_impact_by_team_strength()
        scenario_results = self.analyze_high_impact_injury_scenarios()
        weight_results = self.test_injury_weight_sensitivity()
        
        # Summary
        print(f"\n" + "="*80)
        print("DEEP ANALYSIS SUMMARY")
        print("="*80)
        
        # Season analysis summary
        print(f"\nSeason-by-Season Analysis:")
        for season, results in season_results.items():
            if 'error' not in results:
                print(f"  {season}: {results['brier_improvement_pct']:+.2f}% improvement "
                      f"({results['games_count']} games)")
        
        # Team strength analysis summary
        print(f"\nTeam Strength Analysis:")
        for strength, results in strength_results.items():
            if 'error' not in results:
                print(f"  {strength}: {results['brier_improvement_pct']:+.2f}% improvement "
                      f"({results['games_count']} games)")
        
        # Scenario analysis summary
        print(f"\nHigh-Impact Scenario Analysis:")
        for scenario, results in scenario_results.items():
            if 'error' not in results:
                print(f"  {scenario}: {results['brier_improvement_pct']:+.2f}% improvement "
                      f"({results['games_count']} games)")
        
        # Weight sensitivity summary
        print(f"\nWeight Sensitivity Analysis:")
        print(f"  Best weight: {weight_results['best_weight']:.1f}")
        print(f"  Best Brier Score: {weight_results['best_brier_score']:.4f}")
        
        # Overall assessment
        all_improvements = []
        for results in [season_results, strength_results, scenario_results]:
            for result in results.values():
                if isinstance(result, dict) and 'brier_improvement_pct' in result:
                    all_improvements.append(result['brier_improvement_pct'])
        
        if all_improvements:
            avg_improvement = np.mean(all_improvements)
            max_improvement = np.max(all_improvements)
            
            print(f"\nOverall Assessment:")
            print(f"  Average improvement: {avg_improvement:+.2f}%")
            print(f"  Maximum improvement: {max_improvement:+.2f}%")
            
            if max_improvement > 0.1:
                print(f"  ✅ INJURY ADJUSTMENTS PROVIDE SIGNIFICANT IMPROVEMENT!")
            elif max_improvement > 0.0:
                print(f"  ⚠️  INJURY ADJUSTMENTS PROVIDE MINOR IMPROVEMENT")
            else:
                print(f"  ❌ INJURY ADJUSTMENTS PROVIDE NO IMPROVEMENT")
        
        return {
            'season_results': season_results,
            'strength_results': strength_results,
            'scenario_results': scenario_results,
            'weight_results': weight_results,
            'overall_assessment': {
                'avg_improvement': np.mean(all_improvements) if all_improvements else 0.0,
                'max_improvement': np.max(all_improvements) if all_improvements else 0.0
            }
        }


def run_deep_injury_analysis(years: List[int] = [2018, 2023]):
    """Run comprehensive deep injury analysis."""
    analyzer = InjuryDeepAnalyzer(years)
    return analyzer.run_comprehensive_deep_analysis()


if __name__ == "__main__":
    results = run_deep_injury_analysis()
