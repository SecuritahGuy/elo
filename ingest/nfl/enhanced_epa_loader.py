"""Enhanced EPA data loader with weather and travel context."""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from .epa_data_loader import load_epa_data
from .weather_loader import load_weather_data_with_retry
from .travel_calculator import TravelCalculator
from .stadium_database import StadiumDatabase


def load_epa_with_weather_context(years: List[int], sample_size: Optional[int] = None) -> pd.DataFrame:
    """
    Load EPA data with weather context for each play.
    
    Args:
        years: List of years to load data for
        sample_size: Optional limit on number of plays to load (for testing)
        
    Returns:
        DataFrame with EPA data and weather context
    """
    print("Loading EPA data with weather context...")
    
    # Load base EPA data
    epa_data = load_epa_data(years, sample_size)
    print(f"Loaded {len(epa_data)} EPA plays")
    
    if epa_data.empty:
        return epa_data
    
    # Create games DataFrame for weather loading
    print("Creating games DataFrame for weather loading...")
    games_df = create_games_df_from_epa(epa_data)
    print(f"Created games DataFrame with {len(games_df)} games")
    
    # Load weather data for the games
    print("Loading weather data...")
    weather_data = load_weather_data_with_retry(games_df)
    print(f"Loaded weather data for {len(weather_data)} games")
    
    # Add weather context to EPA data
    epa_with_weather = add_weather_context_to_epa(epa_data, weather_data)
    
    return epa_with_weather


def load_epa_with_weather_and_travel_context(years: List[int], sample_size: Optional[int] = None) -> pd.DataFrame:
    """
    Load EPA data with both weather and travel context for each play.
    
    Args:
        years: List of years to load data for
        sample_size: Optional limit on number of plays to load (for testing)
        
    Returns:
        DataFrame with EPA data, weather context, and travel context
    """
    print("Loading EPA data with weather and travel context...")
    
    # Load base EPA data
    epa_data = load_epa_data(years, sample_size)
    print(f"Loaded {len(epa_data)} EPA plays")
    
    if epa_data.empty:
        return epa_data
    
    # Create games DataFrame for weather loading
    print("Creating games DataFrame for weather loading...")
    games_df = create_games_df_from_epa(epa_data)
    print(f"Created games DataFrame with {len(games_df)} games")
    
    # Load weather data for the games
    print("Loading weather data...")
    weather_data = load_weather_data_with_retry(games_df)
    print(f"Loaded weather data for {len(weather_data)} games")
    
    # Load travel data for the games
    print("Loading travel data...")
    travel_data = load_travel_data_for_games(games_df)
    print(f"Loaded travel data for {len(travel_data)} games")
    
    # Add weather and travel context to EPA data
    epa_with_context = add_weather_context_to_epa(epa_data, weather_data)
    epa_with_context = add_travel_context_to_epa(epa_with_context, travel_data)
    
    # Calculate adjusted EPA values
    epa_with_context = calculate_adjusted_epa_values(epa_with_context)
    
    return epa_with_context


def create_games_df_from_epa(epa_data: pd.DataFrame) -> pd.DataFrame:
    """
    Create a games DataFrame from EPA data for weather loading.
    
    Args:
        epa_data: DataFrame with EPA play data
        
    Returns:
        DataFrame with game information for weather loading
    """
    # Get unique games from EPA data
    games = epa_data.groupby(['season', 'week', 'home_team', 'away_team']).agg({
        'epa': 'count'  # Just to get one row per game
    }).reset_index()
    
    # Rename the count column
    games = games.rename(columns={'epa': 'play_count'})
    
    # Add required columns for weather loading
    games['gameday'] = '2023-09-01'  # Placeholder date - will be updated by weather loader
    games['home_score'] = 0  # Placeholder
    games['away_score'] = 0  # Placeholder
    games['result'] = 0  # Placeholder
    
    return games


def load_travel_data_for_games(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Load travel data for games using the travel calculator.
    
    Args:
        games_df: DataFrame with game data
        
    Returns:
        DataFrame with travel information for each game
    """
    print("Calculating travel data for games...")
    
    travel_calculator = TravelCalculator()
    travel_data = games_df.copy()
    
    # Initialize travel columns
    travel_columns = [
        'home_travel_distance', 'away_travel_distance',
        'home_travel_timezones', 'away_travel_timezones',
        'home_travel_direction', 'away_travel_direction',
        'home_travel_fatigue', 'away_travel_fatigue',
        'home_travel_recovery', 'away_travel_recovery',
        'travel_epa_factor', 'travel_pass_factor', 'travel_rush_factor'
    ]
    
    for col in travel_columns:
        travel_data[col] = 0.0
    
    # Calculate travel information for each game
    for idx, game in travel_data.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get travel info for both teams
        home_travel_info = travel_calculator.get_travel_info(home_team, away_team)
        away_travel_info = travel_calculator.get_travel_info(away_team, home_team)
        
        # Home team travel (usually minimal for home games)
        travel_data.loc[idx, 'home_travel_distance'] = home_travel_info.distance_miles
        travel_data.loc[idx, 'home_travel_timezones'] = home_travel_info.time_zones_crossed
        travel_data.loc[idx, 'home_travel_direction'] = 1.0 if home_travel_info.travel_direction == 'east' else -1.0 if home_travel_info.travel_direction == 'west' else 0.0
        travel_data.loc[idx, 'home_travel_fatigue'] = home_travel_info.fatigue_factor
        travel_data.loc[idx, 'home_travel_recovery'] = home_travel_info.recovery_days
        
        # Away team travel (usually significant for away games)
        travel_data.loc[idx, 'away_travel_distance'] = away_travel_info.distance_miles
        travel_data.loc[idx, 'away_travel_timezones'] = away_travel_info.time_zones_crossed
        travel_data.loc[idx, 'away_travel_direction'] = 1.0 if away_travel_info.travel_direction == 'east' else -1.0 if away_travel_info.travel_direction == 'west' else 0.0
        travel_data.loc[idx, 'away_travel_fatigue'] = away_travel_info.fatigue_factor
        travel_data.loc[idx, 'away_travel_recovery'] = away_travel_info.recovery_days
    
    print(f"Travel data calculated for {len(travel_data)} games")
    return travel_data


def add_travel_context_to_epa(epa_data: pd.DataFrame, travel_data: pd.DataFrame) -> pd.DataFrame:
    """
    Add travel context to EPA data by merging with game travel information.
    
    Args:
        epa_data: DataFrame with EPA play data and weather context
        travel_data: DataFrame with travel data by game
        
    Returns:
        DataFrame with EPA data, weather context, and travel context
    """
    print("Adding travel context to EPA data...")
    
    # Create a copy to avoid modifying original
    epa_with_travel = epa_data.copy()
    
    # Initialize travel columns
    travel_columns = [
        'game_travel_distance', 'game_travel_timezones', 'game_travel_direction',
        'game_travel_fatigue', 'game_travel_recovery',
        'travel_epa_factor', 'travel_pass_factor', 'travel_rush_factor'
    ]
    
    for col in travel_columns:
        epa_with_travel[col] = 0.0
    
    # Create game identifier for merging
    epa_with_travel['game_key'] = epa_with_travel['season'].astype(str) + '_' + \
                                 epa_with_travel['week'].astype(str) + '_' + \
                                 epa_with_travel['home_team'] + '_' + \
                                 epa_with_travel['away_team']
    
    travel_data['game_key'] = travel_data['season'].astype(str) + '_' + \
                             travel_data['week'].astype(str) + '_' + \
                             travel_data['home_team'] + '_' + \
                             travel_data['away_team']
    
    # Merge travel data with EPA data
    travel_cols_to_merge = ['game_key'] + [col for col in travel_data.columns if 'travel' in col]
    available_travel_cols = [col for col in travel_cols_to_merge if col in travel_data.columns]
    
    if available_travel_cols:
        # Rename travel columns to avoid conflicts
        travel_data_renamed = travel_data[available_travel_cols].copy()
        travel_cols_rename = {col: f'travel_{col}' for col in travel_data_renamed.columns if col != 'game_key'}
        travel_data_renamed = travel_data_renamed.rename(columns=travel_cols_rename)
        
        epa_with_travel = epa_with_travel.merge(
            travel_data_renamed,
            on='game_key',
            how='left'
        )
        
        # Map travel data to plays based on team
        for idx, play in epa_with_travel.iterrows():
            team = play['posteam']
            is_home = team == play['home_team']
            
            if is_home:
                # Home team travel (usually minimal)
                epa_with_travel.loc[idx, 'game_travel_distance'] = play.get('travel_home_travel_distance', 0.0)
                epa_with_travel.loc[idx, 'game_travel_timezones'] = play.get('travel_home_travel_timezones', 0.0)
                epa_with_travel.loc[idx, 'game_travel_direction'] = play.get('travel_home_travel_direction', 0.0)
                epa_with_travel.loc[idx, 'game_travel_fatigue'] = play.get('travel_home_travel_fatigue', 0.0)
                epa_with_travel.loc[idx, 'game_travel_recovery'] = play.get('travel_home_travel_recovery', 7.0)
            else:
                # Away team travel (usually significant)
                epa_with_travel.loc[idx, 'game_travel_distance'] = play.get('travel_away_travel_distance', 0.0)
                epa_with_travel.loc[idx, 'game_travel_timezones'] = play.get('travel_away_travel_timezones', 0.0)
                epa_with_travel.loc[idx, 'game_travel_direction'] = play.get('travel_away_travel_direction', 0.0)
                epa_with_travel.loc[idx, 'game_travel_fatigue'] = play.get('travel_away_travel_fatigue', 0.0)
                epa_with_travel.loc[idx, 'game_travel_recovery'] = play.get('travel_away_travel_recovery', 7.0)
    
    # Calculate travel factors for EPA adjustment
    epa_with_travel = calculate_travel_epa_factors(epa_with_travel)
    
    # Clean up temporary columns
    epa_with_travel = epa_with_travel.drop(columns=['game_key'], errors='ignore')
    
    print(f"Travel context added to {len(epa_with_travel)} plays")
    return epa_with_travel


def add_weather_context_to_epa(epa_data: pd.DataFrame, weather_data: pd.DataFrame) -> pd.DataFrame:
    """
    Add weather context to EPA data by merging with game weather information.
    
    Args:
        epa_data: DataFrame with EPA play data
        weather_data: DataFrame with weather data by game
        
    Returns:
        DataFrame with EPA data and weather context
    """
    print("Adding weather context to EPA data...")
    
    # Create a copy to avoid modifying original
    epa_with_weather = epa_data.copy()
    
    # Initialize weather columns
    weather_columns = [
        'game_temperature', 'game_wind_speed', 'game_precipitation', 'game_humidity',
        'game_wind_gust', 'game_snow', 'game_pressure', 'game_is_dome',
        'weather_epa_factor', 'weather_pass_factor', 'weather_rush_factor'
    ]
    
    for col in weather_columns:
        epa_with_weather[col] = 0.0
    
    # Create game identifier for merging
    epa_with_weather['game_key'] = epa_with_weather['season'].astype(str) + '_' + \
                                  epa_with_weather['week'].astype(str) + '_' + \
                                  epa_with_weather['home_team'] + '_' + \
                                  epa_with_weather['away_team']
    
    weather_data['game_key'] = weather_data['season'].astype(str) + '_' + \
                              weather_data['week'].astype(str) + '_' + \
                              weather_data['home_team'] + '_' + \
                              weather_data['away_team']
    
    # Merge weather data with EPA data
    weather_cols_to_merge = ['game_key'] + [col for col in weather_data.columns if 'home_' in col or 'away_' in col]
    available_weather_cols = [col for col in weather_cols_to_merge if col in weather_data.columns]
    
    if available_weather_cols:
        # Rename weather columns to avoid conflicts with EPA data
        weather_data_renamed = weather_data[available_weather_cols].copy()
        weather_cols_rename = {col: f'weather_{col}' for col in weather_data_renamed.columns if col != 'game_key'}
        weather_data_renamed = weather_data_renamed.rename(columns=weather_cols_rename)
        
        epa_with_weather = epa_with_weather.merge(
            weather_data_renamed,
            on='game_key',
            how='left'
        )
        
        
        # Map weather data to plays based on team
        for idx, play in epa_with_weather.iterrows():
            team = play['posteam']
            is_home = team == play['home_team']
            
            if is_home:
                # Home team weather
                epa_with_weather.loc[idx, 'game_temperature'] = play.get('weather_home_temp', 20.0)
                epa_with_weather.loc[idx, 'game_wind_speed'] = play.get('weather_home_wind', 0.0)
                epa_with_weather.loc[idx, 'game_precipitation'] = play.get('weather_home_precip', 0.0)
                epa_with_weather.loc[idx, 'game_humidity'] = play.get('weather_home_humidity', 50.0)
                epa_with_weather.loc[idx, 'game_wind_gust'] = play.get('weather_home_wind_gust', 0.0)
                epa_with_weather.loc[idx, 'game_snow'] = play.get('weather_home_snow', 0.0)
                epa_with_weather.loc[idx, 'game_pressure'] = play.get('weather_home_pressure', 1013.25)
                epa_with_weather.loc[idx, 'game_is_dome'] = False  # Will be determined by stadium type
            else:
                # Away team weather (same as home for neutral site games)
                epa_with_weather.loc[idx, 'game_temperature'] = play.get('weather_away_temp', 20.0)
                epa_with_weather.loc[idx, 'game_wind_speed'] = play.get('weather_away_wind', 0.0)
                epa_with_weather.loc[idx, 'game_precipitation'] = play.get('weather_away_precip', 0.0)
                epa_with_weather.loc[idx, 'game_humidity'] = play.get('weather_away_humidity', 50.0)
                epa_with_weather.loc[idx, 'game_wind_gust'] = play.get('weather_away_wind_gust', 0.0)
                epa_with_weather.loc[idx, 'game_snow'] = play.get('weather_away_snow', 0.0)
                epa_with_weather.loc[idx, 'game_pressure'] = play.get('weather_away_pressure', 1013.25)
                epa_with_weather.loc[idx, 'game_is_dome'] = False  # Will be determined by stadium type
    
    # Calculate weather factors for EPA adjustment
    epa_with_weather = calculate_weather_epa_factors(epa_with_weather)
    
    # Clean up temporary columns
    epa_with_weather = epa_with_weather.drop(columns=['game_key'], errors='ignore')
    
    print(f"Weather context added to {len(epa_with_weather)} plays")
    return epa_with_weather


def calculate_travel_epa_factors(epa_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate travel factors that affect EPA performance.
    
    Args:
        epa_data: DataFrame with EPA data and travel context
        
    Returns:
        DataFrame with travel EPA factors added
    """
    print("Calculating travel EPA factors...")
    
    for idx, play in epa_data.iterrows():
        # Calculate travel impact on EPA
        travel_factor = calculate_travel_epa_factor(
            distance=play['game_travel_distance'],
            timezones=play['game_travel_timezones'],
            fatigue=play['game_travel_fatigue'],
            recovery=play['game_travel_recovery'],
            play_type=play.get('play_type', 'pass')
        )
        
        epa_data.loc[idx, 'travel_epa_factor'] = travel_factor
        
        # Calculate play-type specific factors
        if play.get('play_type') == 'pass':
            pass_factor = calculate_pass_travel_factor(
                distance=play['game_travel_distance'],
                timezones=play['game_travel_timezones'],
                fatigue=play['game_travel_fatigue']
            )
            epa_data.loc[idx, 'travel_pass_factor'] = pass_factor
            epa_data.loc[idx, 'travel_rush_factor'] = 1.0  # No impact on rush plays
        elif play.get('play_type') == 'run':
            rush_factor = calculate_rush_travel_factor(
                distance=play['game_travel_distance'],
                fatigue=play['game_travel_fatigue']
            )
            epa_data.loc[idx, 'travel_rush_factor'] = rush_factor
            epa_data.loc[idx, 'travel_pass_factor'] = 1.0  # No impact on pass plays
        else:
            epa_data.loc[idx, 'travel_pass_factor'] = 1.0
            epa_data.loc[idx, 'travel_rush_factor'] = 1.0
    
    return epa_data


def calculate_travel_epa_factor(distance: float, timezones: float, fatigue: float, 
                              recovery: float, play_type: str) -> float:
    """
    Calculate travel factor that affects EPA performance.
    
    Args:
        distance: Travel distance in miles
        timezones: Number of timezones crossed
        fatigue: Travel fatigue factor (0.0-1.0)
        recovery: Recovery days available
        play_type: Type of play (pass, run, etc.)
        
    Returns:
        Travel factor (1.0 = no impact, <1.0 = negative impact, >1.0 = positive impact)
    """
    factor = 1.0
    
    # Distance impact (exponential)
    if distance > 2000:  # Very long travel
        factor *= 0.85
    elif distance > 1500:  # Long travel
        factor *= 0.90
    elif distance > 1000:  # Medium travel
        factor *= 0.95
    elif distance > 500:   # Short travel
        factor *= 0.98
    
    # Timezone impact (more significant for passing)
    if timezones >= 3:  # Cross-country
        if play_type == 'pass':
            factor *= 0.85
        else:
            factor *= 0.90
    elif timezones >= 2:  # Multiple timezones
        if play_type == 'pass':
            factor *= 0.90
        else:
            factor *= 0.95
    elif timezones >= 1:  # One timezone
        if play_type == 'pass':
            factor *= 0.95
        else:
            factor *= 0.98
    
    # Fatigue impact
    if fatigue > 0.8:  # High fatigue
        factor *= 0.80
    elif fatigue > 0.6:  # Moderate fatigue
        factor *= 0.85
    elif fatigue > 0.4:  # Light fatigue
        factor *= 0.90
    elif fatigue > 0.2:  # Minimal fatigue
        factor *= 0.95
    
    # Recovery impact
    if recovery < 3:  # Short recovery
        factor *= 0.85
    elif recovery < 5:  # Moderate recovery
        factor *= 0.90
    elif recovery < 7:  # Normal recovery
        factor *= 0.95
    
    return max(0.5, min(1.2, factor))  # Cap between 0.5 and 1.2


def calculate_pass_travel_factor(distance: float, timezones: float, fatigue: float) -> float:
    """
    Calculate travel factor specifically for passing plays.
    
    Args:
        distance: Travel distance in miles
        timezones: Number of timezones crossed
        fatigue: Travel fatigue factor (0.0-1.0)
        
    Returns:
        Travel factor for passing plays
    """
    factor = 1.0
    
    # Passing is more affected by travel than running
    if distance > 2000:
        factor *= 0.80
    elif distance > 1500:
        factor *= 0.85
    elif distance > 1000:
        factor *= 0.90
    
    # Timezone changes affect passing more
    if timezones >= 3:
        factor *= 0.80
    elif timezones >= 2:
        factor *= 0.85
    elif timezones >= 1:
        factor *= 0.90
    
    # Fatigue affects passing more
    if fatigue > 0.8:
        factor *= 0.75
    elif fatigue > 0.6:
        factor *= 0.80
    elif fatigue > 0.4:
        factor *= 0.85
    
    return max(0.5, min(1.2, factor))


def calculate_rush_travel_factor(distance: float, fatigue: float) -> float:
    """
    Calculate travel factor specifically for rushing plays.
    
    Args:
        distance: Travel distance in miles
        fatigue: Travel fatigue factor (0.0-1.0)
        
    Returns:
        Travel factor for rushing plays
    """
    factor = 1.0
    
    # Running is less affected by travel than passing
    if distance > 2000:
        factor *= 0.90
    elif distance > 1500:
        factor *= 0.93
    elif distance > 1000:
        factor *= 0.96
    
    # Fatigue affects running less than passing
    if fatigue > 0.8:
        factor *= 0.85
    elif fatigue > 0.6:
        factor *= 0.90
    elif fatigue > 0.4:
        factor *= 0.95
    
    return max(0.5, min(1.2, factor))


def calculate_weather_epa_factors(epa_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate weather factors that affect EPA performance.
    
    Args:
        epa_data: DataFrame with EPA data and weather context
        
    Returns:
        DataFrame with weather EPA factors added
    """
    print("Calculating weather EPA factors...")
    
    for idx, play in epa_data.iterrows():
        # Calculate weather impact on EPA
        weather_factor = calculate_weather_epa_factor(
            temperature=play['game_temperature'],
            wind_speed=play['game_wind_speed'],
            precipitation=play['game_precipitation'],
            humidity=play['game_humidity'],
            wind_gust=play['game_wind_gust'],
            snow=play['game_snow'],
            pressure=play['game_pressure'],
            is_dome=play['game_is_dome'],
            play_type=play.get('play_type', 'pass')
        )
        
        epa_data.loc[idx, 'weather_epa_factor'] = weather_factor
        
        # Calculate play-type specific factors
        if play.get('play_type') == 'pass':
            pass_factor = calculate_pass_weather_factor(
                temperature=play['game_temperature'],
                wind_speed=play['game_wind_speed'],
                precipitation=play['game_precipitation'],
                is_dome=play['game_is_dome']
            )
            epa_data.loc[idx, 'weather_pass_factor'] = pass_factor
            epa_data.loc[idx, 'weather_rush_factor'] = 1.0  # No impact on rush plays
        elif play.get('play_type') == 'run':
            rush_factor = calculate_rush_weather_factor(
                temperature=play['game_temperature'],
                precipitation=play['game_precipitation'],
                snow=play['game_snow'],
                is_dome=play['game_is_dome']
            )
            epa_data.loc[idx, 'weather_rush_factor'] = rush_factor
            epa_data.loc[idx, 'weather_pass_factor'] = 1.0  # No impact on pass plays
        else:
            epa_data.loc[idx, 'weather_pass_factor'] = 1.0
            epa_data.loc[idx, 'weather_rush_factor'] = 1.0
    
    return epa_data


def calculate_weather_epa_factor(temperature: float, wind_speed: float, precipitation: float,
                               humidity: float, wind_gust: float, snow: float, pressure: float,
                               is_dome: bool, play_type: str) -> float:
    """
    Calculate weather factor that affects EPA performance.
    
    Args:
        temperature: Game temperature in Celsius
        wind_speed: Wind speed in km/h
        precipitation: Precipitation in mm
        humidity: Humidity percentage
        wind_gust: Wind gust in km/h
        snow: Snow depth in mm
        pressure: Atmospheric pressure in hPa
        is_dome: Whether game is in a dome
        play_type: Type of play (pass, run, etc.)
        
    Returns:
        Weather factor (1.0 = no impact, <1.0 = negative impact, >1.0 = positive impact)
    """
    if is_dome:
        return 1.0
    
    factor = 1.0
    
    # Temperature impact (optimal around 20°C)
    temp = temperature
    if temp < 0:  # Below freezing
        factor *= 0.85
    elif temp < 5:  # Very cold
        factor *= 0.90
    elif temp < 10:  # Cold
        factor *= 0.95
    elif temp > 35:  # Very hot
        factor *= 0.90
    elif temp > 30:  # Hot
        factor *= 0.95
    
    # Wind impact (exponential for passing)
    effective_wind = max(wind_speed, wind_gust)
    if play_type == 'pass':
        if effective_wind > 40:  # Very windy
            factor *= 0.70
        elif effective_wind > 30:  # Windy
            factor *= 0.80
        elif effective_wind > 20:  # Moderate wind
            factor *= 0.90
        elif effective_wind > 15:  # Light wind
            factor *= 0.95
    else:  # Running plays less affected by wind
        if effective_wind > 40:
            factor *= 0.95
        elif effective_wind > 30:
            factor *= 0.98
    
    # Precipitation impact
    if precipitation > 15:  # Heavy rain
        factor *= 0.80
    elif precipitation > 10:  # Moderate rain
        factor *= 0.85
    elif precipitation > 5:   # Light rain
        factor *= 0.90
    elif precipitation > 2:   # Drizzle
        factor *= 0.95
    
    # Snow impact
    if snow > 50:  # Heavy snow
        factor *= 0.75
    elif snow > 25:  # Moderate snow
        factor *= 0.85
    elif snow > 10:  # Light snow
        factor *= 0.90
    
    # Humidity impact (moderate)
    if humidity > 90:  # Very humid
        factor *= 0.95
    elif humidity < 20:  # Very dry
        factor *= 0.98
    
    # Pressure impact (minimal)
    if pressure < 1000:  # Low pressure (stormy)
        factor *= 0.98
    elif pressure > 1030:  # High pressure (stable)
        factor *= 1.01
    
    return max(0.5, min(1.5, factor))  # Cap between 0.5 and 1.5


def calculate_pass_weather_factor(temperature: float, wind_speed: float, 
                                precipitation: float, is_dome: bool) -> float:
    """
    Calculate weather factor specifically for passing plays.
    
    Args:
        temperature: Game temperature in Celsius
        wind_speed: Wind speed in km/h
        precipitation: Precipitation in mm
        is_dome: Whether game is in a dome
        
    Returns:
        Weather factor for passing plays
    """
    if is_dome:
        return 1.0
    
    factor = 1.0
    
    # Wind has more impact on passing
    if wind_speed > 40:
        factor *= 0.65
    elif wind_speed > 30:
        factor *= 0.75
    elif wind_speed > 20:
        factor *= 0.85
    elif wind_speed > 15:
        factor *= 0.90
    
    # Precipitation affects passing more than running
    if precipitation > 15:
        factor *= 0.75
    elif precipitation > 10:
        factor *= 0.80
    elif precipitation > 5:
        factor *= 0.85
    
    # Cold weather affects passing more
    if temperature < 0:
        factor *= 0.80
    elif temperature < 5:
        factor *= 0.85
    elif temperature < 10:
        factor *= 0.90
    
    return max(0.5, min(1.5, factor))


def calculate_rush_weather_factor(temperature: float, precipitation: float, 
                                snow: float, is_dome: bool) -> float:
    """
    Calculate weather factor specifically for rushing plays.
    
    Args:
        temperature: Game temperature in Celsius
        precipitation: Precipitation in mm
        snow: Snow depth in mm
        is_dome: Whether game is in a dome
        
    Returns:
        Weather factor for rushing plays
    """
    if is_dome:
        return 1.0
    
    factor = 1.0
    
    # Snow has more impact on running
    if snow > 50:
        factor *= 0.70
    elif snow > 25:
        factor *= 0.80
    elif snow > 10:
        factor *= 0.90
    
    # Precipitation affects running less than passing
    if precipitation > 15:
        factor *= 0.90
    elif precipitation > 10:
        factor *= 0.95
    
    # Cold weather affects running less than passing
    if temperature < 0:
        factor *= 0.90
    elif temperature < 5:
        factor *= 0.95
    
    return max(0.5, min(1.5, factor))


def calculate_adjusted_epa_values(epa_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate adjusted EPA values using environmental factors.
    
    Args:
        epa_data: DataFrame with EPA data and environmental context
        
    Returns:
        DataFrame with adjusted EPA values
    """
    print("Calculating adjusted EPA values...")
    
    # Initialize adjusted EPA columns
    adjusted_columns = [
        'adjusted_epa', 'adjusted_qb_epa', 'adjusted_air_epa', 'adjusted_yac_epa',
        'environmental_epa_impact', 'environmental_qb_epa_impact',
        'environmental_air_epa_impact', 'environmental_yac_epa_impact'
    ]
    
    for col in adjusted_columns:
        epa_data[col] = 0.0
    
    # Calculate adjusted EPA for each play
    for idx, play in epa_data.iterrows():
        # Get environmental factors
        weather_factor = play.get('weather_epa_factor', 1.0)
        travel_factor = play.get('travel_epa_factor', 1.0)
        
        # Calculate play-type specific factors
        play_type = play.get('play_type', 'pass')
        if play_type == 'pass':
            weather_play_factor = play.get('weather_pass_factor', 1.0)
            travel_play_factor = play.get('travel_pass_factor', 1.0)
        elif play_type == 'run':
            weather_play_factor = play.get('weather_rush_factor', 1.0)
            travel_play_factor = play.get('travel_rush_factor', 1.0)
        else:
            weather_play_factor = 1.0
            travel_play_factor = 1.0
        
        # Combined environmental factor for this play
        play_environmental_factor = weather_play_factor * travel_play_factor
        
        # Get raw EPA values
        raw_epa = play.get('epa', 0.0)
        raw_qb_epa = play.get('qb_epa', 0.0)
        raw_air_epa = play.get('air_epa', 0.0)
        raw_yac_epa = play.get('yac_epa', 0.0)
        
        # Calculate adjusted EPA values
        adjusted_epa = raw_epa * play_environmental_factor
        adjusted_qb_epa = raw_qb_epa * play_environmental_factor
        adjusted_air_epa = raw_air_epa * play_environmental_factor
        adjusted_yac_epa = raw_yac_epa * play_environmental_factor
        
        # Store adjusted values
        epa_data.loc[idx, 'adjusted_epa'] = adjusted_epa
        epa_data.loc[idx, 'adjusted_qb_epa'] = adjusted_qb_epa
        epa_data.loc[idx, 'adjusted_air_epa'] = adjusted_air_epa
        epa_data.loc[idx, 'adjusted_yac_epa'] = adjusted_yac_epa
        
        # Calculate environmental impacts
        epa_data.loc[idx, 'environmental_epa_impact'] = adjusted_epa - raw_epa
        epa_data.loc[idx, 'environmental_qb_epa_impact'] = adjusted_qb_epa - raw_qb_epa
        epa_data.loc[idx, 'environmental_air_epa_impact'] = adjusted_air_epa - raw_air_epa
        epa_data.loc[idx, 'environmental_yac_epa_impact'] = adjusted_yac_epa - raw_yac_epa
    
    print(f"Adjusted EPA values calculated for {len(epa_data)} plays")
    return epa_data


def test_enhanced_epa_loader():
    """Test the enhanced EPA loader with weather context."""
    print("Testing Enhanced EPA Loader with Weather Context...")
    
    # Load a small sample of EPA data with weather context
    epa_data = load_epa_with_weather_context([2023], sample_size=1000)
    
    print(f"\nLoaded {len(epa_data)} plays with weather context")
    
    # Check weather columns
    weather_cols = [col for col in epa_data.columns if 'weather' in col or 'game_' in col]
    print(f"Weather columns: {weather_cols}")
    
    # Show sample data
    if not epa_data.empty:
        print("\nSample EPA data with weather context:")
        sample_cols = ['season', 'week', 'posteam', 'play_type', 'epa', 'game_temperature', 
                      'game_wind_speed', 'weather_epa_factor', 'weather_pass_factor']
        available_cols = [col for col in sample_cols if col in epa_data.columns]
        print(epa_data[available_cols].head(10).to_string())
        
        # Show weather factor distribution
        print(f"\nWeather EPA factor distribution:")
        print(f"  Mean: {epa_data['weather_epa_factor'].mean():.3f}")
        print(f"  Std: {epa_data['weather_epa_factor'].std():.3f}")
        print(f"  Min: {epa_data['weather_epa_factor'].min():.3f}")
        print(f"  Max: {epa_data['weather_epa_factor'].max():.3f}")
        
        # Show play-type specific factors
        pass_plays = epa_data[epa_data['play_type'] == 'pass']
        run_plays = epa_data[epa_data['play_type'] == 'run']
        
        if not pass_plays.empty:
            print(f"\nPass play weather factors:")
            print(f"  Mean: {pass_plays['weather_pass_factor'].mean():.3f}")
            print(f"  Std: {pass_plays['weather_pass_factor'].std():.3f}")
        
        if not run_plays.empty:
            print(f"\nRun play weather factors:")
            print(f"  Mean: {run_plays['weather_rush_factor'].mean():.3f}")
            print(f"  Std: {run_plays['weather_rush_factor'].std():.3f}")
    
    print("\nEnhanced EPA loader test complete!")


def test_enhanced_epa_loader_with_travel():
    """Test the enhanced EPA loader with both weather and travel context."""
    print("Testing Enhanced EPA Loader with Weather and Travel Context...")
    
    # Load a small sample of EPA data with weather and travel context
    epa_data = load_epa_with_weather_and_travel_context([2023], sample_size=1000)
    
    print(f"\nLoaded {len(epa_data)} plays with weather and travel context")
    
    # Check weather and travel columns
    weather_cols = [col for col in epa_data.columns if 'weather' in col or 'game_temp' in col or 'game_wind' in col]
    travel_cols = [col for col in epa_data.columns if 'travel' in col or 'game_travel' in col]
    print(f"Weather columns: {len(weather_cols)}")
    print(f"Travel columns: {len(travel_cols)}")
    
    # Show sample data
    if not epa_data.empty:
        print("\nSample EPA data with weather and travel context:")
        sample_cols = ['season', 'week', 'posteam', 'play_type', 'epa', 'game_temperature', 
                      'game_wind_speed', 'game_travel_distance', 'weather_epa_factor', 
                      'travel_epa_factor', 'weather_pass_factor', 'travel_pass_factor']
        available_cols = [col for col in sample_cols if col in epa_data.columns]
        print(epa_data[available_cols].head(10).to_string())
        
        # Show weather factor distribution
        print(f"\nWeather EPA factor distribution:")
        print(f"  Mean: {epa_data['weather_epa_factor'].mean():.3f}")
        print(f"  Std: {epa_data['weather_epa_factor'].std():.3f}")
        print(f"  Min: {epa_data['weather_epa_factor'].min():.3f}")
        print(f"  Max: {epa_data['weather_epa_factor'].max():.3f}")
        
        # Show travel factor distribution
        print(f"\nTravel EPA factor distribution:")
        print(f"  Mean: {epa_data['travel_epa_factor'].mean():.3f}")
        print(f"  Std: {epa_data['travel_epa_factor'].std():.3f}")
        print(f"  Min: {epa_data['travel_epa_factor'].min():.3f}")
        print(f"  Max: {epa_data['travel_epa_factor'].max():.3f}")
        
        # Show combined environmental impact
        epa_data['combined_environmental_factor'] = epa_data['weather_epa_factor'] * epa_data['travel_epa_factor']
        print(f"\nCombined Environmental EPA factor distribution:")
        print(f"  Mean: {epa_data['combined_environmental_factor'].mean():.3f}")
        print(f"  Std: {epa_data['combined_environmental_factor'].std():.3f}")
        print(f"  Min: {epa_data['combined_environmental_factor'].min():.3f}")
        print(f"  Max: {epa_data['combined_environmental_factor'].max():.3f}")
        
        # Show play-type specific factors
        pass_plays = epa_data[epa_data['play_type'] == 'pass']
        run_plays = epa_data[epa_data['play_type'] == 'run']
        
        if not pass_plays.empty:
            print(f"\nPass play environmental factors:")
            print(f"  Weather: {pass_plays['weather_pass_factor'].mean():.3f}")
            print(f"  Travel: {pass_plays['travel_pass_factor'].mean():.3f}")
            print(f"  Combined: {(pass_plays['weather_pass_factor'] * pass_plays['travel_pass_factor']).mean():.3f}")
        
        if not run_plays.empty:
            print(f"\nRun play environmental factors:")
            print(f"  Weather: {run_plays['weather_rush_factor'].mean():.3f}")
            print(f"  Travel: {run_plays['travel_rush_factor'].mean():.3f}")
            print(f"  Combined: {(run_plays['weather_rush_factor'] * run_plays['travel_rush_factor']).mean():.3f}")
    
    print("\nEnhanced EPA loader with travel test complete!")


if __name__ == "__main__":
    test_enhanced_epa_loader()
