"""Feature hooks for additional adjustments to Elo ratings."""

import pandas as pd
from typing import Optional, Dict, Any
import numpy as np
from .qb_performance import QBPerformanceTracker


def qb_delta_stub(row: pd.Series) -> float:
    """
    Placeholder for QB adjustment calculation.
    
    Args:
        row: Game row with team information
        
    Returns:
        QB adjustment in rating points (currently 0)
    """
    # TODO: Implement QB adjustment based on:
    # - QB injury status
    # - Backup QB vs starter
    # - Historical QB performance
    # - Market-based QB value
    return 0.0


def qb_adjustment_advanced(row: pd.Series, qb_tracker: Optional[QBPerformanceTracker] = None) -> tuple[float, float]:
    """
    Advanced QB adjustment using performance tracking.
    
    Args:
        row: Game row with team information
        qb_tracker: QB performance tracker instance
        
    Returns:
        Tuple of (home_qb_delta, away_qb_delta) in rating points
    """
    if qb_tracker is None:
        return 0.0, 0.0
    
    try:
        # Get QB performance for both teams using team-based lookup
        home_qb_perf = qb_tracker.get_qb_performance_at_week(
            '',  # We'll find the QB by team
            row.get('home_team', ''),
            row.get('season', 0),
            row.get('week', 0)
        )
        
        away_qb_perf = qb_tracker.get_qb_performance_at_week(
            '',  # We'll find the QB by team
            row.get('away_team', ''),
            row.get('season', 0),
            row.get('week', 0)
        )
        
        # Calculate rating deltas
        home_delta = qb_tracker.calculate_qb_rating_delta(home_qb_perf) if home_qb_perf else 0.0
        away_delta = qb_tracker.calculate_qb_rating_delta(away_qb_perf) if away_qb_perf else 0.0
        
        return home_delta, away_delta
        
    except Exception as e:
        print(f"Error calculating QB adjustment: {e}")
        return 0.0, 0.0


def qb_change_adjustment(home_team: str, away_team: str, season: int, week: int,
                        qb_tracker: Optional[QBPerformanceTracker] = None) -> tuple[float, float]:
    """
    Calculate QB change adjustment based on starter vs backup.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        season: Season year
        week: Week number
        qb_tracker: QB performance tracker instance
        
    Returns:
        Tuple of (home_qb_delta, away_qb_delta) in rating points
    """
    if qb_tracker is None:
        return 0.0, 0.0
    
    try:
        # Get current week QB performance
        home_qb_perf = qb_tracker.get_qb_performance_at_week(
            '', home_team, season, week
        )
        away_qb_perf = qb_tracker.get_qb_performance_at_week(
            '', away_team, season, week
        )
        
        # Get previous week QB performance for comparison
        home_qb_prev = qb_tracker.get_qb_performance_at_week(
            '', home_team, season, max(1, week - 1)
        )
        away_qb_prev = qb_tracker.get_qb_performance_at_week(
            '', away_team, season, max(1, week - 1)
        )
        
        # Calculate change in QB performance
        home_delta = 0.0
        away_delta = 0.0
        
        if home_qb_perf and home_qb_prev:
            home_delta = qb_tracker.calculate_qb_rating_delta(home_qb_perf) - qb_tracker.calculate_qb_rating_delta(home_qb_prev)
        
        if away_qb_perf and away_qb_prev:
            away_delta = qb_tracker.calculate_qb_rating_delta(away_qb_perf) - qb_tracker.calculate_qb_rating_delta(away_qb_prev)
        
        return home_delta, away_delta
        
    except Exception as e:
        print(f"Error calculating QB change adjustment: {e}")
        return 0.0, 0.0


def rest_days(home_rest: Optional[float], away_rest: Optional[float]) -> tuple[Optional[float], Optional[float]]:
    """
    Process rest days for both teams.
    
    Args:
        home_rest: Home team's rest days
        away_rest: Away team's rest days
        
    Returns:
        Tuple of processed rest days
    """
    # Already delivered by ingest; kept here to allow alternative derivations
    return home_rest, away_rest


def enhanced_rest_days(home_team: str, away_team: str, home_rest: Optional[float], 
                      away_rest: Optional[float], home_previous_opponent: Optional[str] = None,
                      away_previous_opponent: Optional[str] = None) -> tuple[float, float]:
    """
    Calculate enhanced rest days considering travel recovery time.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        home_rest: Home team's rest days
        away_rest: Away team's rest days
        home_previous_opponent: Home team's previous opponent
        away_previous_opponent: Away team's previous opponent
        
    Returns:
        Tuple of (home_effective_rest, away_effective_rest)
    """
    from .travel_adjustments import TravelAdjustmentCalculator
    
    # Default to 7 days if rest days not provided
    home_rest = home_rest if home_rest is not None else 7.0
    away_rest = away_rest if away_rest is not None else 7.0
    
    # Calculate travel adjustments
    calculator = TravelAdjustmentCalculator()
    home_rest_info, away_rest_info = calculator.get_rest_day_info(
        home_team, away_team, int(home_rest), int(away_rest),
        home_previous_opponent, away_previous_opponent
    )
    
    # Calculate effective rest days (considering travel recovery)
    home_effective_rest = home_rest * home_rest_info.recovery_factor
    away_effective_rest = away_rest * away_rest_info.recovery_factor
    
    return home_effective_rest, away_effective_rest


def travel_adjustment(home_team: str, away_team: str, home_rest: Optional[float], 
                     away_rest: Optional[float], home_previous_opponent: Optional[str] = None,
                     away_previous_opponent: Optional[str] = None) -> tuple[float, float]:
    """
    Calculate travel adjustments for both teams.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        home_rest: Home team's rest days
        away_rest: Away team's rest days
        home_previous_opponent: Home team's previous opponent
        away_previous_opponent: Away team's previous opponent
        
    Returns:
        Tuple of (home_travel_adj, away_travel_adj) in Elo points
    """
    from .travel_adjustments import TravelAdjustmentCalculator
    
    # Default to 7 days if rest days not provided
    home_rest = home_rest if home_rest is not None else 7.0
    away_rest = away_rest if away_rest is not None else 7.0
    
    # Calculate travel adjustments
    calculator = TravelAdjustmentCalculator()
    home_rest_info, away_rest_info = calculator.get_rest_day_info(
        home_team, away_team, int(home_rest), int(away_rest),
        home_previous_opponent, away_previous_opponent
    )
    
    # Calculate net travel adjustments
    home_travel_adj = home_rest_info.rest_advantage - home_rest_info.travel_penalty
    away_travel_adj = away_rest_info.rest_advantage - away_rest_info.travel_penalty
    
    return home_travel_adj, away_travel_adj


def simple_travel_adjustment(home_team: str, away_team: str, 
                           home_rest: Optional[float] = None,
                           away_rest: Optional[float] = None) -> float:
    """
    Calculate travel adjustment based on rest days and distance.
    
    Args:
        home_team: Home team name
        away_team: Away team name
        home_rest: Home team's rest days
        away_rest: Away team's rest days
        
    Returns:
        Travel adjustment in rating points
    """
    # TODO: Implement travel adjustment based on:
    # - Distance between cities
    # - Time zone changes
    # - Rest day differential
    # - Historical travel performance
    
    # For now, return 0
    return 0.0


def weather_adjustment(game_id: str, temperature: Optional[float] = None,
                      wind_speed: Optional[float] = None,
                      precipitation: Optional[float] = None) -> float:
    """
    Calculate weather adjustment for outdoor games.
    
    Args:
        game_id: Game identifier
        temperature: Temperature in Fahrenheit
        wind_speed: Wind speed in mph
        precipitation: Precipitation amount
        
    Returns:
        Weather adjustment in rating points
    """
    # TODO: Implement weather adjustment based on:
    # - Extreme temperatures
    # - High wind speeds
    # - Precipitation
    # - Historical weather performance
    
    # For now, return 0
    return 0.0


def injury_adjustment(home_team: str, away_team: str,
                     home_injuries: Optional[Dict[str, Any]] = None,
                     away_injuries: Optional[Dict[str, Any]] = None) -> tuple[float, float]:
    """
    Calculate injury adjustments for both teams.
    
    Args:
        home_team: Home team name
        away_team: Away team name
        home_injuries: Home team injury report
        away_injuries: Away team injury report
        
    Returns:
        Tuple of (home_adjustment, away_adjustment) in rating points
    """
    # TODO: Implement injury adjustment based on:
    # - Key player injuries (QB, star players)
    # - Position group depth
    # - Historical injury impact
    # - Market-based injury values
    
    # For now, return 0 for both teams
    return 0.0, 0.0


def momentum_adjustment(team: str, recent_games: pd.DataFrame,
                       weeks_back: int = 3) -> float:
    """
    Calculate momentum adjustment based on recent performance.
    
    Args:
        team: Team name
        recent_games: DataFrame of recent games
        weeks_back: Number of weeks to look back
        
    Returns:
        Momentum adjustment in rating points
    """
    # TODO: Implement momentum adjustment based on:
    # - Recent win/loss record
    # - Point differential in recent games
    # - Performance vs expectations
    # - Streak effects
    
    # For now, return 0
    return 0.0


def market_adjustment(home_team: str, away_team: str,
                     spread: Optional[float] = None,
                     total: Optional[float] = None) -> float:
    """
    Calculate market-based adjustment using betting lines.
    
    Args:
        home_team: Home team name
        away_team: Away team name
        spread: Point spread
        total: Total points
        
    Returns:
        Market adjustment in rating points
    """
    # TODO: Implement market adjustment based on:
    # - Point spread vs model prediction
    # - Total vs model prediction
    # - Market efficiency over time
    # - Shrinkage toward market consensus
    
    # For now, return 0
    return 0.0


def apply_all_adjustments(row: pd.Series, config: Dict[str, Any], 
                         qb_tracker: Optional[QBPerformanceTracker] = None) -> tuple[float, float]:
    """
    Apply all available adjustments to a game.
    
    Args:
        row: Game row with all available information
        config: Configuration for which adjustments to apply
        qb_tracker: QB performance tracker instance
        
    Returns:
        Tuple of (home_adjustment, away_adjustment) in rating points
    """
    home_adj = 0.0
    away_adj = 0.0
    
    # QB adjustments
    if config.get("use_qb_adjustment", False):
        if config.get("use_advanced_qb_adjustment", False) and qb_tracker is not None:
            # Use advanced QB adjustment with performance tracking
            qb_home, qb_away = qb_adjustment_advanced(row, qb_tracker)
            home_adj += qb_home
            away_adj += qb_away
        else:
            # Use simple QB adjustment
            home_adj += qb_delta_stub(row)
            away_adj += qb_delta_stub(row)
    
    # QB change adjustments
    if config.get("use_qb_change_adjustment", False) and qb_tracker is not None:
        qb_change_home, qb_change_away = qb_change_adjustment(
            row.get("home_team", ""),
            row.get("away_team", ""),
            row.get("season", 0),
            row.get("week", 0),
            qb_tracker
        )
        home_adj += qb_change_home
        away_adj += qb_change_away
    
    # Travel adjustments
    if config.get("use_travel_adjustment", False):
        home_travel_adj, away_travel_adj = travel_adjustment(
            row.get("home_team"), row.get("away_team"),
            row.get("home_rest"), row.get("away_rest"),
            row.get("home_previous_opponent"), row.get("away_previous_opponent")
        )
        home_adj += home_travel_adj
        away_adj += away_travel_adj
    
    # Weather adjustments
    if config.get("use_weather_adjustment", False):
        weather_adj = weather_adjustment(
            row.get("game_id"),
            row.get("temperature"),
            row.get("wind_speed"),
            row.get("precipitation")
        )
        home_adj += weather_adj
        away_adj -= weather_adj
    
    # Injury adjustments
    if config.get("use_injury_adjustment", False):
        inj_home, inj_away = injury_adjustment(
            row.get("home_team"), row.get("away_team"),
            row.get("home_injuries"), row.get("away_injuries")
        )
        home_adj += inj_home
        away_adj += inj_away
    
    # Momentum adjustments
    if config.get("use_momentum_adjustment", False):
        # Would need recent games data
        pass
    
    # Market adjustments
    if config.get("use_market_adjustment", False):
        market_adj = market_adjustment(
            row.get("home_team"), row.get("away_team"),
            row.get("spread"), row.get("total")
        )
        home_adj += market_adj
        away_adj -= market_adj
    
    return home_adj, away_adj
