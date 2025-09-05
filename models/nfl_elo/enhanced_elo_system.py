"""Enhanced Elo system with environmental adjustments and breakout capability."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from .config import EloConfig
from .ratings import RatingBook, TeamRating
from .updater import apply_game_update
from .features import apply_all_adjustments
from .qb_performance import QBPerformanceTracker
from .enhanced_qb_performance import EnhancedQBPerformanceTracker
from .adjusted_epa_calculator import AdjustedEPACalculator


@dataclass
class EnvironmentalAdjustments:
    """Environmental adjustments for a game."""
    weather_home_delta: float = 0.0
    weather_away_delta: float = 0.0
    travel_home_delta: float = 0.0
    travel_away_delta: float = 0.0
    qb_home_delta: float = 0.0
    qb_away_delta: float = 0.0
    epa_home_delta: float = 0.0
    epa_away_delta: float = 0.0
    total_home_delta: float = 0.0
    total_away_delta: float = 0.0


@dataclass
class GameResult:
    """Enhanced game result with environmental breakdown."""
    season: int
    week: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_rating_before: float
    away_rating_before: float
    home_rating_after: float
    away_rating_after: float
    p_home: float
    actual_result: int  # 1 if home wins, 0 if away wins
    
    # Environmental adjustments breakdown
    weather_home_delta: float = 0.0
    weather_away_delta: float = 0.0
    travel_home_delta: float = 0.0
    travel_away_delta: float = 0.0
    qb_home_delta: float = 0.0
    qb_away_delta: float = 0.0
    epa_home_delta: float = 0.0
    epa_away_delta: float = 0.0
    
    # Environmental context
    weather_impact: float = 0.0
    travel_impact: float = 0.0
    qb_impact: float = 0.0
    epa_impact: float = 0.0
    total_environmental_impact: float = 0.0


class EnhancedEloSystem:
    """Enhanced Elo system with environmental adjustments and breakout capability."""
    
    def __init__(self, config: EloConfig, 
                 qb_tracker: Optional[QBPerformanceTracker] = None,
                 enhanced_qb_tracker: Optional[EnhancedQBPerformanceTracker] = None,
                 adjusted_epa_calculator: Optional[AdjustedEPACalculator] = None):
        """
        Initialize the enhanced Elo system.
        
        Args:
            config: Elo configuration
            qb_tracker: Standard QB performance tracker
            enhanced_qb_tracker: Enhanced QB performance tracker with environmental context
            adjusted_epa_calculator: Calculator for adjusted EPA metrics
        """
        self.config = config
        self.qb_tracker = qb_tracker
        self.enhanced_qb_tracker = enhanced_qb_tracker
        self.adjusted_epa_calculator = adjusted_epa_calculator
        
        # Initialize rating book
        self.ratings = RatingBook(base=config.base_rating)
        
        # Game history with environmental breakdown
        self.game_history: List[GameResult] = []
        
        # Environmental impact tracking
        self.environmental_impacts = {
            'weather': {'total': 0.0, 'games': 0},
            'travel': {'total': 0.0, 'games': 0},
            'qb': {'total': 0.0, 'games': 0},
            'epa': {'total': 0.0, 'games': 0}
        }
    
    def process_game(self, game: pd.Series) -> GameResult:
        """
        Process a single game with environmental adjustments.
        
        Args:
            game: Game data with environmental context
            
        Returns:
            GameResult with environmental breakdown
        """
        # Get current ratings
        home_rating = self.ratings.get(game['home_team'])
        away_rating = self.ratings.get(game['away_team'])
        
        # Calculate environmental adjustments
        env_adj = self._calculate_environmental_adjustments(game)
        
        # Apply game update with all adjustments
        new_home_rating, new_away_rating, p_home = apply_game_update(
            home_rating, away_rating,
            int(game['home_score']), int(game['away_score']), self.config,
            home_rest_days=game.get('home_rest'),
            away_rest_days=game.get('away_rest'),
            qb_home_delta=env_adj.qb_home_delta,
            qb_away_delta=env_adj.qb_away_delta,
            weather_home_delta=env_adj.weather_home_delta,
            weather_away_delta=env_adj.weather_away_delta,
            travel_home_delta=env_adj.travel_home_delta,
            travel_away_delta=env_adj.travel_away_delta
        )
        
        # Update ratings
        self.ratings.set(game['home_team'], new_home_rating)
        self.ratings.set(game['away_team'], new_away_rating)
        
        # Create game result with environmental breakdown
        game_result = GameResult(
            season=game['season'],
            week=game['week'],
            home_team=game['home_team'],
            away_team=game['away_team'],
            home_score=int(game['home_score']),
            away_score=int(game['away_score']),
            home_rating_before=home_rating,
            away_rating_before=away_rating,
            home_rating_after=new_home_rating,
            away_rating_after=new_away_rating,
            p_home=p_home,
            actual_result=1 if game['home_score'] > game['away_score'] else 0,
            
            # Environmental adjustments
            weather_home_delta=env_adj.weather_home_delta,
            weather_away_delta=env_adj.weather_away_delta,
            travel_home_delta=env_adj.travel_home_delta,
            travel_away_delta=env_adj.travel_away_delta,
            qb_home_delta=env_adj.qb_home_delta,
            qb_away_delta=env_adj.qb_away_delta,
            epa_home_delta=env_adj.epa_home_delta,
            epa_away_delta=env_adj.epa_away_delta,
            
            # Environmental impacts
            weather_impact=env_adj.weather_home_delta + env_adj.weather_away_delta,
            travel_impact=env_adj.travel_home_delta + env_adj.travel_away_delta,
            qb_impact=env_adj.qb_home_delta + env_adj.qb_away_delta,
            epa_impact=env_adj.epa_home_delta + env_adj.epa_away_delta,
            total_environmental_impact=env_adj.total_home_delta + env_adj.total_away_delta
        )
        
        # Update environmental impact tracking
        self._update_environmental_tracking(game_result)
        
        # Store game result
        self.game_history.append(game_result)
        
        return game_result
    
    def _calculate_environmental_adjustments(self, game: pd.Series) -> EnvironmentalAdjustments:
        """
        Calculate all environmental adjustments for a game.
        
        Args:
            game: Game data with environmental context
            
        Returns:
            EnvironmentalAdjustments object
        """
        adj = EnvironmentalAdjustments()
        
        # Weather adjustments
        if self.config.use_weather_adjustment:
            adj.weather_home_delta = game.get('home_weather_adj', 0.0) * self.config.weather_adjustment_weight
            adj.weather_away_delta = game.get('away_weather_adj', 0.0) * self.config.weather_adjustment_weight
            
            # Cap weather adjustments
            adj.weather_home_delta = max(-self.config.weather_max_delta, 
                                       min(self.config.weather_max_delta, adj.weather_home_delta))
            adj.weather_away_delta = max(-self.config.weather_max_delta, 
                                       min(self.config.weather_max_delta, adj.weather_away_delta))
        
        # Travel adjustments
        if self.config.use_travel_adjustment:
            from .features import travel_adjustment
            travel_home_delta, travel_away_delta = travel_adjustment(
                game['home_team'], game['away_team'],
                game.get('home_rest'), game.get('away_rest'),
                game.get('home_previous_opponent'), game.get('away_previous_opponent')
            )
            adj.travel_home_delta = travel_home_delta * self.config.travel_adjustment_weight
            adj.travel_away_delta = travel_away_delta * self.config.travel_adjustment_weight
            
            # Cap travel adjustments
            adj.travel_home_delta = max(-self.config.travel_max_delta, 
                                      min(self.config.travel_max_delta, adj.travel_home_delta))
            adj.travel_away_delta = max(-self.config.travel_max_delta, 
                                      min(self.config.travel_max_delta, adj.travel_away_delta))
        
        # QB adjustments
        if self.config.use_qb_adjustment and self.enhanced_qb_tracker is not None:
            # Use enhanced QB tracker with environmental context
            qb_home_perf = self.enhanced_qb_tracker.get_enhanced_qb_performance_at_week(
                "", game['home_team'], game['season'], game['week']
            )
            qb_away_perf = self.enhanced_qb_tracker.get_enhanced_qb_performance_at_week(
                "", game['away_team'], game['season'], game['week']
            )
            
            if qb_home_perf:
                adj.qb_home_delta = self.enhanced_qb_tracker.calculate_enhanced_qb_rating_delta(qb_home_perf)
                adj.qb_home_delta *= self.config.qb_adjustment_weight
            
            if qb_away_perf:
                adj.qb_away_delta = self.enhanced_qb_tracker.calculate_enhanced_qb_rating_delta(qb_away_perf)
                adj.qb_away_delta *= self.config.qb_adjustment_weight
        
        # EPA adjustments (based on adjusted EPA performance)
        if self.adjusted_epa_calculator is not None:
            # Get team EPA summaries with environmental adjustments
            home_epa_summary = self.adjusted_epa_calculator.get_team_adjusted_epa_summary(
                game['home_team'], game['season'], game['week']
            )
            away_epa_summary = self.adjusted_epa_calculator.get_team_adjusted_epa_summary(
                game['away_team'], game['season'], game['week']
            )
            
            # Convert EPA impact to Elo points (scaling factor)
            epa_scale = 0.1  # 1 EPA point = 0.1 Elo points
            adj.epa_home_delta = home_epa_summary.get('environmental_impact', 0.0) * epa_scale
            adj.epa_away_delta = away_epa_summary.get('environmental_impact', 0.0) * epa_scale
        
        # Calculate total adjustments
        adj.total_home_delta = (adj.weather_home_delta + adj.travel_home_delta + 
                               adj.qb_home_delta + adj.epa_home_delta)
        adj.total_away_delta = (adj.weather_away_delta + adj.travel_away_delta + 
                               adj.qb_away_delta + adj.epa_away_delta)
        
        return adj
    
    def _update_environmental_tracking(self, game_result: GameResult):
        """Update environmental impact tracking."""
        # Weather impact
        if abs(game_result.weather_impact) > 0:
            self.environmental_impacts['weather']['total'] += abs(game_result.weather_impact)
            self.environmental_impacts['weather']['games'] += 1
        
        # Travel impact
        if abs(game_result.travel_impact) > 0:
            self.environmental_impacts['travel']['total'] += abs(game_result.travel_impact)
            self.environmental_impacts['travel']['games'] += 1
        
        # QB impact
        if abs(game_result.qb_impact) > 0:
            self.environmental_impacts['qb']['total'] += abs(game_result.qb_impact)
            self.environmental_impacts['qb']['games'] += 1
        
        # EPA impact
        if abs(game_result.epa_impact) > 0:
            self.environmental_impacts['epa']['total'] += abs(game_result.epa_impact)
            self.environmental_impacts['epa']['games'] += 1
    
    def get_environmental_breakdown(self) -> Dict[str, Any]:
        """
        Get environmental impact breakdown.
        
        Returns:
            Dictionary with environmental impact statistics
        """
        if not self.game_history:
            return {}
        
        breakdown = {}
        
        for env_type, data in self.environmental_impacts.items():
            if data['games'] > 0:
                breakdown[env_type] = {
                    'total_impact': data['total'],
                    'games_affected': data['games'],
                    'avg_impact_per_game': data['total'] / data['games'],
                    'percentage_of_games': (data['games'] / len(self.game_history)) * 100
                }
            else:
                breakdown[env_type] = {
                    'total_impact': 0.0,
                    'games_affected': 0,
                    'avg_impact_per_game': 0.0,
                    'percentage_of_games': 0.0
                }
        
        # Overall statistics
        total_environmental_impact = sum(gr.total_environmental_impact for gr in self.game_history)
        breakdown['overall'] = {
            'total_environmental_impact': total_environmental_impact,
            'avg_environmental_impact_per_game': total_environmental_impact / len(self.game_history),
            'total_games': len(self.game_history)
        }
        
        return breakdown
    
    def get_team_environmental_summary(self, team: str) -> Dict[str, Any]:
        """
        Get environmental impact summary for a specific team.
        
        Args:
            team: Team abbreviation
            
        Returns:
            Dictionary with team's environmental impact statistics
        """
        team_games = [gr for gr in self.game_history 
                     if gr.home_team == team or gr.away_team == team]
        
        if not team_games:
            return {}
        
        # Calculate team-specific impacts
        home_games = [gr for gr in team_games if gr.home_team == team]
        away_games = [gr for gr in team_games if gr.away_team == team]
        
        summary = {
            'team': team,
            'total_games': len(team_games),
            'home_games': len(home_games),
            'away_games': len(away_games),
            'weather_advantage': sum(gr.weather_home_delta if gr.home_team == team else gr.weather_away_delta 
                                   for gr in team_games),
            'travel_advantage': sum(gr.travel_home_delta if gr.home_team == team else gr.travel_away_delta 
                                  for gr in team_games),
            'qb_advantage': sum(gr.qb_home_delta if gr.home_team == team else gr.qb_away_delta 
                              for gr in team_games),
            'epa_advantage': sum(gr.epa_home_delta if gr.home_team == team else gr.epa_away_delta 
                               for gr in team_games),
            'total_environmental_advantage': sum(gr.total_environmental_impact if gr.home_team == team 
                                               else -gr.total_environmental_impact for gr in team_games)
        }
        
        return summary


def test_enhanced_elo_system():
    """Test the enhanced Elo system with environmental adjustments."""
    print("Testing Enhanced Elo System...")
    
    # Load data
    from ingest.nfl.data_loader import load_games
    from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context
    from models.nfl_elo.config import EloConfig
    from models.nfl_elo.enhanced_qb_performance import EnhancedQBPerformanceTracker
    from models.nfl_elo.adjusted_epa_calculator import AdjustedEPACalculator
    
    # Load games and EPA data
    games = load_games([2023])
    epa_data = load_epa_with_weather_and_travel_context([2023], sample_size=1000)
    
    print(f"Loaded {len(games)} games and {len(epa_data)} EPA plays")
    
    # Initialize enhanced components
    config = EloConfig(
        use_weather_adjustment=True,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        weather_adjustment_weight=1.0,
        travel_adjustment_weight=1.0,
        qb_adjustment_weight=1.0
    )
    
    enhanced_qb_tracker = EnhancedQBPerformanceTracker(
        qb_data=pd.DataFrame(),
        games_data=games,
        adjusted_epa_data=epa_data
    )
    
    adjusted_epa_calculator = AdjustedEPACalculator(epa_data)
    
    # Initialize enhanced Elo system
    elo_system = EnhancedEloSystem(
        config=config,
        enhanced_qb_tracker=enhanced_qb_tracker,
        adjusted_epa_calculator=adjusted_epa_calculator
    )
    
    # Process a few games
    print("\nProcessing games with environmental adjustments...")
    sample_games = games.head(5)
    
    for idx, game in sample_games.iterrows():
        game_result = elo_system.process_game(game)
        print(f"Game: {game_result.home_team} vs {game_result.away_team}")
        print(f"  Weather Impact: {game_result.weather_impact:.2f}")
        print(f"  Travel Impact: {game_result.travel_impact:.2f}")
        print(f"  QB Impact: {game_result.qb_impact:.2f}")
        print(f"  EPA Impact: {game_result.epa_impact:.2f}")
        print(f"  Total Environmental Impact: {game_result.total_environmental_impact:.2f}")
        print()
    
    # Get environmental breakdown
    print("Environmental Breakdown:")
    breakdown = elo_system.get_environmental_breakdown()
    for env_type, data in breakdown.items():
        if isinstance(data, dict) and 'total_impact' in data:
            print(f"  {env_type}: {data['total_impact']:.2f} total impact, "
                  f"{data['games_affected']} games affected")
    
    print("\nEnhanced Elo System test complete!")


if __name__ == "__main__":
    test_enhanced_elo_system()
