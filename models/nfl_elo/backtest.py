"""Walk-forward backtesting system for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from .config import EloConfig
from .ratings import RatingBook
from .updater import apply_game_update, apply_offdef_update
from .evaluator import calculate_all_metrics
from .qb_performance import QBPerformanceTracker
from .features import apply_all_adjustments
import warnings


def preseason_reset(ratings: RatingBook, cfg: EloConfig) -> None:
    """
    Apply preseason regression to all team ratings.
    
    Args:
        ratings: RatingBook to update
        cfg: Elo configuration
    """
    ratings.regress_preseason(cfg.preseason_regress)


def run_backtest(games: pd.DataFrame, cfg: EloConfig, qb_data: Optional[pd.DataFrame] = None, epa_data: Optional[pd.DataFrame] = None, weather_data: Optional[pd.DataFrame] = None) -> Dict:
    """
    Run walk-forward backtest on game data.
    
    Args:
        games: DataFrame with game data
        cfg: Elo configuration
        qb_data: Optional QB data for QB adjustments
        epa_data: Optional EPA data for advanced QB adjustments
        weather_data: Optional weather data for weather adjustments
        
    Returns:
        Dictionary with metrics and game history
    """
    # Validate input data
    required_columns = ["season", "week", "home_team", "away_team", "home_score", "away_score"]
    missing_columns = [col for col in required_columns if col not in games.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Initialize rating book
    ratings = RatingBook(base=cfg.base_rating)
    
    # Initialize QB performance tracker if QB adjustments are enabled
    qb_tracker = None
    if cfg.use_qb_adjustment and qb_data is not None:
        qb_tracker = QBPerformanceTracker(qb_data, games, epa_data)
        print(f"Initialized QB performance tracker with {len(qb_data)} QB records")
        if epa_data is not None:
            print(f"EPA data included: {len(epa_data)} plays")
    
    # Apply weather adjustments if enabled
    if cfg.use_weather_adjustment and weather_data is not None:
        from .weather_adjustments import apply_weather_adjustments
        games = apply_weather_adjustments(games, weather_data)
        print(f"Weather adjustments applied to {len(games)} games")
    
    # Initialize offense/defense ratings if enabled
    if cfg.use_offdef_split:
        # Get all unique teams
        all_teams = set(games["home_team"].unique()) | set(games["away_team"].unique())
        for team in all_teams:
            ratings.set_offdef(team, cfg.base_rating, cfg.base_rating)
    
    # Store game results
    game_results = []
    
    # Process each season
    for season in sorted(games["season"].unique()):
        if season < cfg.start_season or season > cfg.end_season:
            continue
            
        # Apply preseason regression
        preseason_reset(ratings, cfg)
        
        # Get games for this season, sorted by week and game_id
        season_games = games[games["season"] == season].copy()
        season_games = season_games.sort_values(["week", "game_id"])
        
        # Process each game in the season
        for _, game in season_games.iterrows():
            try:
                # Get current ratings
                home_rating = ratings.get(game["home_team"])
                away_rating = ratings.get(game["away_team"])
                
                # Get rest days (handle missing values)
                home_rest = game.get("home_rest") if pd.notna(game.get("home_rest")) else None
                away_rest = game.get("away_rest") if pd.notna(game.get("away_rest")) else None
                
                # Calculate all adjustments
                qb_home_delta = 0.0
                qb_away_delta = 0.0
                travel_home_delta = 0.0
                travel_away_delta = 0.0
                
                # Calculate travel adjustments separately
                if cfg.use_travel_adjustment:
                    from .features import travel_adjustment
                    travel_home_delta, travel_away_delta = travel_adjustment(
                        game["home_team"], game["away_team"],
                        game.get("home_rest"), game.get("away_rest")
                    )
                    
                    # Apply travel adjustment weight
                    travel_home_delta *= cfg.travel_adjustment_weight
                    travel_away_delta *= cfg.travel_adjustment_weight
                    
                    # Cap travel adjustments
                    travel_home_delta = max(-cfg.travel_max_delta, min(cfg.travel_max_delta, travel_home_delta))
                    travel_away_delta = max(-cfg.travel_max_delta, min(cfg.travel_max_delta, travel_away_delta))
                
                if cfg.use_qb_adjustment and qb_tracker is not None:
                    # Create config dict for feature adjustments (without travel)
                    feature_config = {
                        "use_qb_adjustment": cfg.use_qb_adjustment,
                        "use_advanced_qb_adjustment": cfg.use_advanced_qb_adjustment,
                        "use_qb_change_adjustment": cfg.use_qb_change_adjustment,
                        "use_travel_adjustment": False,  # Calculate separately above
                        "use_weather_adjustment": cfg.use_weather_adjustment,
                        "use_injury_adjustment": False,
                        "use_momentum_adjustment": False,
                        "use_market_adjustment": False
                    }
                    
                    # Apply QB adjustments
                    qb_home_delta, qb_away_delta = apply_all_adjustments(game, feature_config, qb_tracker)
                    
                    # Apply QB adjustment weight
                    qb_home_delta *= cfg.qb_adjustment_weight
                    qb_away_delta *= cfg.qb_adjustment_weight
                
                # Calculate weather adjustments
                weather_home_delta = 0.0
                weather_away_delta = 0.0
                if cfg.use_weather_adjustment:
                    weather_home_delta = game.get('home_weather_adj', 0.0) * cfg.weather_adjustment_weight
                    weather_away_delta = game.get('away_weather_adj', 0.0) * cfg.weather_adjustment_weight
                    
                    # Cap weather adjustments
                    weather_home_delta = max(-cfg.weather_max_delta, min(cfg.weather_max_delta, weather_home_delta))
                    weather_away_delta = max(-cfg.weather_max_delta, min(cfg.weather_max_delta, weather_away_delta))
                
                # Calculate injury adjustments
                injury_home_delta = 0.0
                injury_away_delta = 0.0
                if cfg.use_injury_adjustment:
                    # Get injury impacts
                    home_injury_impact = game.get('home_injury_impact', 0.0)
                    away_injury_impact = game.get('away_injury_impact', 0.0)
                    home_key_impact = game.get('home_key_position_injury_impact', 0.0)
                    away_key_impact = game.get('away_key_position_injury_impact', 0.0)

                    # Calculate adjustments (negative for injured team)
                    injury_home_delta = -(home_injury_impact + home_key_impact * 0.5) * cfg.injury_adjustment_weight
                    injury_away_delta = -(away_injury_impact + away_key_impact * 0.5) * cfg.injury_adjustment_weight

                    # Cap injury adjustments
                    injury_home_delta = max(-cfg.injury_max_delta, min(cfg.injury_max_delta, injury_home_delta))
                    injury_away_delta = max(-cfg.injury_max_delta, min(cfg.injury_max_delta, injury_away_delta))
        
                # Calculate red zone adjustments
                redzone_home_delta = 0.0
                redzone_away_delta = 0.0
                if cfg.use_redzone_adjustment:
                    # Get red zone impacts
                    home_redzone_impact = game.get('home_redzone_impact', 0.0)
                    away_redzone_impact = game.get('away_redzone_impact', 0.0)

                    # Calculate adjustments
                    redzone_home_delta = home_redzone_impact * cfg.redzone_adjustment_weight
                    redzone_away_delta = away_redzone_impact * cfg.redzone_adjustment_weight

                    # Cap red zone adjustments
                    redzone_home_delta = max(-cfg.redzone_max_delta, min(cfg.redzone_max_delta, redzone_home_delta))
                    redzone_away_delta = max(-cfg.redzone_max_delta, min(cfg.redzone_max_delta, redzone_away_delta))
                
                # Calculate down efficiency adjustments
                downs_home_delta = 0.0
                downs_away_delta = 0.0
                if cfg.use_downs_adjustment:
                    # Get down efficiency impacts
                    home_downs_impact = game.get('home_downs_impact', 0.0)
                    away_downs_impact = game.get('away_downs_impact', 0.0)

                    # Calculate adjustments
                    downs_home_delta = home_downs_impact * cfg.downs_adjustment_weight
                    downs_away_delta = away_downs_impact * cfg.downs_adjustment_weight

                    # Cap down efficiency adjustments
                    downs_home_delta = max(-cfg.downs_max_delta, min(cfg.downs_max_delta, downs_home_delta))
                    downs_away_delta = max(-cfg.downs_max_delta, min(cfg.downs_max_delta, downs_away_delta))
                
                # Calculate clock management adjustments
                clock_management_home_delta = 0.0
                clock_management_away_delta = 0.0
                if cfg.use_clock_management_adjustment:
                    # Get clock management impacts
                    home_clock_impact = game.get('home_clock_management_impact', 0.0)
                    away_clock_impact = game.get('away_clock_management_impact', 0.0)

                    # Calculate adjustments
                    clock_management_home_delta = home_clock_impact * cfg.clock_management_adjustment_weight
                    clock_management_away_delta = away_clock_impact * cfg.clock_management_adjustment_weight

                    # Cap clock management adjustments
                    clock_management_home_delta = max(-cfg.clock_management_max_delta, min(cfg.clock_management_max_delta, clock_management_home_delta))
                    clock_management_away_delta = max(-cfg.clock_management_max_delta, min(cfg.clock_management_max_delta, clock_management_away_delta))
                
                # Apply game update
                if cfg.use_offdef_split:
                    # Use offense/defense split
                    home_off, home_def = ratings.get_offdef(game["home_team"])
                    away_off, away_def = ratings.get_offdef(game["away_team"])
                    
                    new_home_off, new_home_def, new_away_off, new_away_def, p_home = apply_offdef_update(
                        home_off, home_def, away_off, away_def,
                        int(game["home_score"]), int(game["away_score"]), cfg
                    )
                    
                    # Update offense/defense ratings
                    ratings.set_offdef(game["home_team"], new_home_off, new_home_def)
                    ratings.set_offdef(game["away_team"], new_away_off, new_away_def)
                    
                    # Calculate overall rating for compatibility
                    new_home_rating = (new_home_off + new_home_def) / 2
                    new_away_rating = (new_away_off + new_away_def) / 2
                    
                else:
                    # Use standard Elo
                                    new_home_rating, new_away_rating, p_home = apply_game_update(
                    home_rating, away_rating,
                    int(game["home_score"]), int(game["away_score"]), cfg,
                    home_rest_days=home_rest, away_rest_days=away_rest,
                    qb_home_delta=qb_home_delta, qb_away_delta=qb_away_delta,
                    weather_home_delta=weather_home_delta, weather_away_delta=weather_away_delta,
                    travel_home_delta=travel_home_delta, travel_away_delta=travel_away_delta,
                    injury_home_delta=injury_home_delta, injury_away_delta=injury_away_delta,
                    redzone_home_delta=redzone_home_delta, redzone_away_delta=redzone_away_delta,
                    downs_home_delta=downs_home_delta, downs_away_delta=downs_away_delta,
                    clock_management_home_delta=clock_management_home_delta, clock_management_away_delta=clock_management_away_delta
                )
                
                # Update team ratings
                ratings.set(game["home_team"], new_home_rating)
                ratings.set(game["away_team"], new_away_rating)
                
                # Record game result
                game_result = {
                    "season": int(game["season"]),
                    "week": int(game["week"]),
                    "game_id": game.get("game_id", f"{season}_{game['week']}_{game['home_team']}_{game['away_team']}"),
                    "home_team": game["home_team"],
                    "away_team": game["away_team"],
                    "home_score": int(game["home_score"]),
                    "away_score": int(game["away_score"]),
                    "p_home": p_home,
                    "home_win": 1 if game["home_score"] > game["away_score"] else 0,
                    "home_rating_pre": home_rating,
                    "away_rating_pre": away_rating,
                    "home_rating_post": new_home_rating,
                    "away_rating_post": new_away_rating,
                    "home_rest": home_rest,
                    "away_rest": away_rest,
                    "qb_home_delta": qb_home_delta,
                    "qb_away_delta": qb_away_delta,
                    "weather_home_delta": weather_home_delta,
                    "weather_away_delta": weather_away_delta,
                    "travel_home_delta": travel_home_delta,
                    "travel_away_delta": travel_away_delta
                }
                
                # Add offense/defense ratings if enabled
                if cfg.use_offdef_split:
                    game_result.update({
                        "home_off_pre": home_off,
                        "home_def_pre": home_def,
                        "away_off_pre": away_off,
                        "away_def_pre": away_def,
                        "home_off_post": new_home_off,
                        "home_def_post": new_home_def,
                        "away_off_post": new_away_off,
                        "away_def_post": new_away_def
                    })
                
                game_results.append(game_result)
                
            except Exception as e:
                warnings.warn(f"Error processing game {game.get('game_id', 'unknown')}: {e}")
                continue
    
    # Convert to DataFrame
    results_df = pd.DataFrame(game_results)
    
    if len(results_df) == 0:
        return {"error": "No games processed successfully"}
    
    # Calculate metrics
    metrics = calculate_all_metrics(results_df)
    
    # Add season-specific metrics
    season_metrics = {}
    for season in results_df["season"].unique():
        season_data = results_df[results_df["season"] == season]
        season_metrics[f"season_{season}"] = calculate_all_metrics(season_data)
    
    return {
        "metrics": metrics,
        "season_metrics": season_metrics,
        "history": results_df,
        "final_ratings": ratings.get_rating_summary(),
        "final_offdef_ratings": ratings.get_offdef_summary() if cfg.use_offdef_split else {}
    }


def run_comparison_backtest(games: pd.DataFrame, configs: Dict[str, EloConfig]) -> Dict:
    """
    Run backtest with multiple configurations for comparison.
    
    Args:
        games: DataFrame with game data
        configs: Dictionary mapping config names to EloConfig objects
        
    Returns:
        Dictionary with comparison results
    """
    results = {}
    
    for config_name, config in configs.items():
        print(f"Running backtest for {config_name}...")
        try:
            result = run_backtest(games, config)
            results[config_name] = result
        except Exception as e:
            print(f"Error running backtest for {config_name}: {e}")
            results[config_name] = {"error": str(e)}
    
    return results


def analyze_rating_trajectories(results: Dict) -> pd.DataFrame:
    """
    Analyze how team ratings change over time.
    
    Args:
        results: Results from run_backtest
        
    Returns:
        DataFrame with rating trajectories
    """
    if "history" not in results:
        return pd.DataFrame()
    
    history = results["history"]
    
    # Get all unique teams
    all_teams = set(history["home_team"].unique()) | set(history["away_team"].unique())
    
    trajectories = []
    
    for team in all_teams:
        # Get games where team played
        team_games = history[
            (history["home_team"] == team) | (history["away_team"] == team)
        ].copy()
        
        # Sort by season and week
        team_games = team_games.sort_values(["season", "week"])
        
        for _, game in team_games.iterrows():
            if game["home_team"] == team:
                rating_pre = game["home_rating_pre"]
                rating_post = game["home_rating_post"]
                opponent = game["away_team"]
                is_home = True
            else:
                rating_pre = game["away_rating_pre"]
                rating_post = game["away_rating_post"]
                opponent = game["home_team"]
                is_home = False
            
            trajectories.append({
                "team": team,
                "season": game["season"],
                "week": game["week"],
                "opponent": opponent,
                "is_home": is_home,
                "rating_pre": rating_pre,
                "rating_post": rating_post,
                "rating_change": rating_post - rating_pre
            })
    
    return pd.DataFrame(trajectories)


def calculate_rating_volatility(results: Dict) -> pd.DataFrame:
    """
    Calculate rating volatility for each team.
    
    Args:
        results: Results from run_backtest
        
    Returns:
        DataFrame with volatility metrics per team
    """
    trajectories = analyze_rating_trajectories(results)
    
    if len(trajectories) == 0:
        return pd.DataFrame()
    
    volatility_data = []
    
    for team in trajectories["team"].unique():
        team_data = trajectories[trajectories["team"] == team]
        
        # Calculate volatility metrics
        rating_changes = team_data["rating_change"].values
        rating_std = team_data["rating_post"].std()
        change_std = np.std(rating_changes)
        max_change = np.max(np.abs(rating_changes))
        
        volatility_data.append({
            "team": team,
            "n_games": len(team_data),
            "rating_std": rating_std,
            "change_std": change_std,
            "max_change": max_change,
            "final_rating": team_data["rating_post"].iloc[-1] if len(team_data) > 0 else np.nan
        })
    
    return pd.DataFrame(volatility_data).sort_values("change_std", ascending=False)
