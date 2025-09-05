"""Game update logic for Elo ratings."""

import math
from typing import Tuple, Optional
from .config import EloConfig


def logistic_expectation(rating_a: float, rating_b: float, scale: float) -> float:
    """
    Calculate the probability that team A beats team B.
    
    Args:
        rating_a: Rating of team A
        rating_b: Rating of team B  
        scale: Logistic scale parameter
        
    Returns:
        Probability that team A wins (0 to 1)
    """
    if scale <= 0:
        raise ValueError(f"Scale must be positive: {scale}")
    
    return 1.0 / (1.0 + 10 ** (-(rating_a - rating_b) / scale))


def mov_multiplier(point_diff: int, rdiff_pre: float, cfg: EloConfig) -> float:
    """
    Calculate margin of victory multiplier (FiveThirtyEight style).
    
    Args:
        point_diff: Point difference in the game
        rdiff_pre: Pre-game rating difference
        cfg: Elo configuration
        
    Returns:
        MOV multiplier
    """
    if not cfg.mov_enabled:
        return 1.0
    
    if cfg.mov_mult_a <= 0 or cfg.mov_mult_b < 0:
        raise ValueError(f"Invalid MOV parameters: a={cfg.mov_mult_a}, b={cfg.mov_mult_b}")
    
    # FiveThirtyEight formula: ln(|PD|+1) * (A / (B*|rdiff| + A))
    abs_point_diff = abs(point_diff)
    abs_rdiff = abs(rdiff_pre)
    
    return math.log(abs_point_diff + 1.0) * (cfg.mov_mult_a / (cfg.mov_mult_b * abs_rdiff + cfg.mov_mult_a))


def apply_game_update(
    home_rating: float,
    away_rating: float,
    home_points: int,
    away_points: int,
    cfg: EloConfig,
    home_rest_days: Optional[float] = None,
    away_rest_days: Optional[float] = None,
    qb_home_delta: float = 0.0,
    qb_away_delta: float = 0.0,
    weather_home_delta: float = 0.0,
    weather_away_delta: float = 0.0,
    travel_home_delta: float = 0.0,
    travel_away_delta: float = 0.0,
    injury_home_delta: float = 0.0,
    injury_away_delta: float = 0.0,
    redzone_home_delta: float = 0.0,
    redzone_away_delta: float = 0.0,
    downs_home_delta: float = 0.0,
    downs_away_delta: float = 0.0,
    clock_management_home_delta: float = 0.0,
    clock_management_away_delta: float = 0.0,
    turnover_home_delta: float = 0.0,
    turnover_away_delta: float = 0.0
) -> Tuple[float, float, float]:
    """
    Apply a single game update to Elo ratings.
    
    Args:
        home_rating: Home team's current rating
        away_rating: Away team's current rating
        home_points: Home team's points scored
        away_points: Away team's points scored
        cfg: Elo configuration
        home_rest_days: Home team's rest days (optional)
        away_rest_days: Away team's rest days (optional)
        qb_home_delta: QB adjustment for home team
        qb_away_delta: QB adjustment for away team
        
    Returns:
        Tuple of (new_home_rating, new_away_rating, home_win_probability)
    """
    # Validate inputs
    if home_points < 0 or away_points < 0:
        raise ValueError(f"Points cannot be negative: {home_points}, {away_points}")
    
    if cfg.k <= 0:
        raise ValueError(f"K-factor must be positive: {cfg.k}")
    
    if cfg.scale <= 0:
        raise ValueError(f"Scale must be positive: {cfg.scale}")
    
    # Pre-game adjustments
    hfa = cfg.hfa_points
    adj_home = home_rating + hfa + qb_home_delta + weather_home_delta + travel_home_delta + injury_home_delta + redzone_home_delta + downs_home_delta + clock_management_home_delta + turnover_home_delta
    adj_away = away_rating + qb_away_delta + weather_away_delta + travel_away_delta + injury_away_delta + redzone_away_delta + downs_away_delta + clock_management_away_delta + turnover_away_delta
    
    # Rest advantage adjustment
    if home_rest_days is not None and away_rest_days is not None:
        rest_edge = (home_rest_days - away_rest_days) * cfg.rest_per_day_pts
        adj_home += rest_edge / 2.0
        adj_away -= rest_edge / 2.0
    
    # Calculate expected win probability
    exp_home = logistic_expectation(adj_home, adj_away, cfg.scale)
    
    # Determine actual outcome
    home_win = 1 if home_points > away_points else 0
    margin = home_points - away_points
    
    # Calculate rating difference and MOV multiplier
    rdiff_pre = adj_home - adj_away
    mult = mov_multiplier(margin, rdiff_pre, cfg)
    
    # Calculate rating change
    delta = cfg.k * mult * (home_win - exp_home)
    
    # Apply safety rails
    delta = max(min(delta, cfg.max_rating_shift_per_game), -cfg.max_rating_shift_per_game)
    
    # Update ratings (home gets +delta, away gets -delta)
    new_home = home_rating + delta
    new_away = away_rating - delta
    
    return new_home, new_away, exp_home


def apply_offdef_update(
    home_off: float,
    home_def: float,
    away_off: float,
    away_def: float,
    home_points: int,
    away_points: int,
    cfg: EloConfig
) -> Tuple[float, float, float, float, float]:
    """
    Apply offense/defense split update.
    
    Args:
        home_off: Home team's offense rating
        home_def: Home team's defense rating
        away_off: Away team's offense rating
        away_def: Away team's defense rating
        home_points: Home team's points scored
        away_points: Away team's points scored
        cfg: Elo configuration
        
    Returns:
        Tuple of (new_home_off, new_home_def, new_away_off, new_away_def, home_win_prob)
    """
    if not cfg.use_offdef_split:
        raise ValueError("Offense/defense split not enabled in configuration")
    
    # Predict point margin
    pm_hat = (home_off - away_def) - (away_off - home_def) + cfg.hfa_points
    
    # Convert to win probability using offdef scale
    home_win_prob = logistic_expectation(pm_hat, 0, cfg.offdef_scale)
    
    # Calculate expected points for each team
    home_exp_points = (home_off - away_def) + cfg.hfa_points / 2
    away_exp_points = (away_off - home_def) - cfg.hfa_points / 2
    
    # Update offense ratings based on points scored vs expected
    home_off_delta = cfg.k_off * (home_points - home_exp_points)
    away_off_delta = cfg.k_off * (away_points - away_exp_points)
    
    # Update defense ratings based on points allowed vs expected
    home_def_delta = cfg.k_def * (home_exp_points - away_points)  # Flipped because lower is better for defense
    away_def_delta = cfg.k_def * (away_exp_points - home_points)
    
    # Apply safety rails
    home_off_delta = max(min(home_off_delta, cfg.max_rating_shift_per_game), -cfg.max_rating_shift_per_game)
    away_off_delta = max(min(away_off_delta, cfg.max_rating_shift_per_game), -cfg.max_rating_shift_per_game)
    home_def_delta = max(min(home_def_delta, cfg.max_rating_shift_per_game), -cfg.max_rating_shift_per_game)
    away_def_delta = max(min(away_def_delta, cfg.max_rating_shift_per_game), -cfg.max_rating_shift_per_game)
    
    # Update ratings
    new_home_off = home_off + home_off_delta
    new_home_def = home_def + home_def_delta
    new_away_off = away_off + away_off_delta
    new_away_def = away_def + away_def_delta
    
    return new_home_off, new_home_def, new_away_off, new_away_def, home_win_prob
