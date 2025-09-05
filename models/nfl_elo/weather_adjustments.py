"""Weather adjustment calculations for NFL Elo system."""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class WeatherConditions:
    """Weather conditions for a game."""
    temperature: float  # Celsius
    wind_speed: float   # km/h
    precipitation: float  # mm
    humidity: float     # %
    is_dome: bool = False
    wind_gust: float = 0.0  # km/h
    snow: float = 0.0       # mm
    pressure: float = 0.0   # hPa


def calculate_weather_impact(weather: WeatherConditions) -> float:
    """
    Calculate weather impact on NFL game performance.
    
    Args:
        weather: Weather conditions for the game
        
    Returns:
        Weather impact score (negative = bad for offense)
    """
    if weather.is_dome:
        return 0.0
    
    impact = 0.0
    
    # Temperature impact (optimal around 20°C / 68°F)
    temp = weather.temperature
    if temp < 0:  # Below freezing
        impact -= 3.0
    elif temp < 5:  # Very cold
        impact -= 2.5
    elif temp < 10:  # Cold
        impact -= 2.0
    elif temp < 15:  # Cool
        impact -= 1.0
    elif temp > 35:  # Very hot
        impact -= 1.5
    elif temp > 30:  # Hot
        impact -= 1.0
    elif temp > 25:  # Warm
        impact -= 0.5
    
    # Wind impact (exponential) - use max of sustained wind and gust
    effective_wind = max(weather.wind_speed, weather.wind_gust)
    if effective_wind > 40:  # Very windy with gusts
        impact -= 4.0
    elif effective_wind > 30:  # Very windy
        impact -= 3.0
    elif effective_wind > 25:  # Windy
        impact -= 2.5
    elif effective_wind > 20:  # Moderate wind
        impact -= 2.0
    elif effective_wind > 15:  # Light wind
        impact -= 1.5
    elif effective_wind > 10:  # Breeze
        impact -= 1.0
    elif effective_wind > 5:   # Light breeze
        impact -= 0.5
    
    # Precipitation impact
    precip = weather.precipitation
    if precip > 15:  # Heavy rain
        impact -= 3.0
    elif precip > 10:  # Moderate rain
        impact -= 2.5
    elif precip > 5:   # Light rain
        impact -= 2.0
    elif precip > 2:   # Drizzle
        impact -= 1.5
    elif precip > 0:   # Trace precipitation
        impact -= 1.0
    
    # Snow impact (additional penalty)
    if weather.snow > 50:  # Heavy snow
        impact -= 2.0
    elif weather.snow > 25:  # Moderate snow
        impact -= 1.5
    elif weather.snow > 10:  # Light snow
        impact -= 1.0
    elif weather.snow > 0:   # Trace snow
        impact -= 0.5
    
    # Humidity impact (moderate)
    humidity = weather.humidity
    if humidity > 90:  # Very humid
        impact -= 0.8
    elif humidity > 80:  # Humid
        impact -= 0.5
    elif humidity < 30:  # Very dry
        impact -= 0.3
    elif humidity < 40:  # Dry
        impact -= 0.2
    
    # Pressure impact (barometric pressure affects ball flight)
    if weather.pressure > 0:  # Only if pressure data available
        if weather.pressure < 1000:  # Low pressure (stormy)
            impact -= 0.5
        elif weather.pressure > 1030:  # High pressure (stable)
            impact += 0.2
    
    return impact


def get_weather_adjustment(home_team: str, away_team: str, 
                          stadium_db: Optional[Dict] = None) -> Tuple[float, float]:
    """
    Get weather adjustments for home and away teams.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        stadium_db: Optional stadium database
        
    Returns:
        Tuple of (home_adjustment, away_adjustment)
    """
    # For now, return neutral adjustments
    # In a full implementation, this would look up actual weather data
    return 0.0, 0.0


def apply_weather_adjustments(games_df: pd.DataFrame, 
                            weather_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Apply weather adjustments to games DataFrame.
    
    Args:
        games_df: DataFrame with game data
        weather_data: Optional DataFrame with weather data
        
    Returns:
        DataFrame with weather adjustments added
    """
    games_with_weather = games_df.copy()
    
    # Add weather adjustment columns
    games_with_weather['home_weather_adj'] = 0.0
    games_with_weather['away_weather_adj'] = 0.0
    games_with_weather['weather_impact'] = 0.0
    
    # Add comprehensive weather columns
    weather_columns = [
        'home_temp', 'home_temp_min', 'home_temp_max', 'home_wind', 'home_wind_dir',
        'home_wind_gust', 'home_precip', 'home_snow', 'home_humidity', 'home_pressure',
        'home_cloud_cover', 'home_visibility',
        'away_temp', 'away_temp_min', 'away_temp_max', 'away_wind', 'away_wind_dir',
        'away_wind_gust', 'away_precip', 'away_snow', 'away_humidity', 'away_pressure',
        'away_cloud_cover', 'away_visibility'
    ]
    
    for col in weather_columns:
        games_with_weather[col] = 0.0
    
    if weather_data is not None:
        # Merge weather data with games
        weather_cols = ['home_team', 'away_team', 'gameday'] + weather_columns
        
        available_weather_cols = [col for col in weather_cols if col in weather_data.columns]
        if available_weather_cols:
            # Merge on common columns
            merge_cols = ['home_team', 'away_team', 'gameday']
            common_merge_cols = [col for col in merge_cols if col in games_df.columns and col in weather_data.columns]
            
            if common_merge_cols:
                games_with_weather = games_with_weather.merge(
                    weather_data[available_weather_cols], 
                    on=common_merge_cols, 
                    how='left'
                )
                
                # Calculate weather adjustments
                for idx, game in games_with_weather.iterrows():
                    # Handle merged weather data (may have _x and _y suffixes)
                    home_temp = game.get('home_temp', game.get('home_temp_x', game.get('home_temp_y', 20.0)))
                    home_wind = game.get('home_wind', game.get('home_wind_x', game.get('home_wind_y', 0.0)))
                    home_precip = game.get('home_precip', game.get('home_precip_x', game.get('home_precip_y', 0.0)))
                    home_humidity = game.get('home_humidity', game.get('home_humidity_x', game.get('home_humidity_y', 50.0)))
                    home_wind_gust = game.get('home_wind_gust', game.get('home_wind_gust_x', game.get('home_wind_gust_y', 0.0)))
                    home_snow = game.get('home_snow', game.get('home_snow_x', game.get('home_snow_y', 0.0)))
                    home_pressure = game.get('home_pressure', game.get('home_pressure_x', game.get('home_pressure_y', 0.0)))
                    
                    away_temp = game.get('away_temp', game.get('away_temp_x', game.get('away_temp_y', 20.0)))
                    away_wind = game.get('away_wind', game.get('away_wind_x', game.get('away_wind_y', 0.0)))
                    away_precip = game.get('away_precip', game.get('away_precip_x', game.get('away_precip_y', 0.0)))
                    away_humidity = game.get('away_humidity', game.get('away_humidity_x', game.get('away_humidity_y', 50.0)))
                    away_wind_gust = game.get('away_wind_gust', game.get('away_wind_gust_x', game.get('away_wind_gust_y', 0.0)))
                    away_snow = game.get('away_snow', game.get('away_snow_x', game.get('away_snow_y', 0.0)))
                    away_pressure = game.get('away_pressure', game.get('away_pressure_x', game.get('away_pressure_y', 0.0)))
                    
                    # Home team weather
                    home_weather = WeatherConditions(
                        temperature=home_temp,
                        wind_speed=home_wind,
                        precipitation=home_precip,
                        humidity=home_humidity,
                        is_dome=game.get('home_stadium_type', 'outdoor') == 'dome',
                        wind_gust=home_wind_gust,
                        snow=home_snow,
                        pressure=home_pressure
                    )
                    
                    # Away team weather (same as home for neutral site games)
                    away_weather = WeatherConditions(
                        temperature=away_temp,
                        wind_speed=away_wind,
                        precipitation=away_precip,
                        humidity=away_humidity,
                        is_dome=game.get('away_stadium_type', 'outdoor') == 'dome',
                        wind_gust=away_wind_gust,
                        snow=away_snow,
                        pressure=away_pressure
                    )
                    
                    home_adj = calculate_weather_impact(home_weather)
                    away_adj = calculate_weather_impact(away_weather)
                    
                    games_with_weather.loc[idx, 'home_weather_adj'] = home_adj
                    games_with_weather.loc[idx, 'away_weather_adj'] = away_adj
                    games_with_weather.loc[idx, 'weather_impact'] = abs(home_adj) + abs(away_adj)
    
    return games_with_weather


def create_sample_weather_data(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create sample weather data for testing purposes.
    
    Args:
        games_df: DataFrame with game data
        
    Returns:
        DataFrame with sample weather data
    """
    weather_data = games_df[['home_team', 'away_team', 'gameday']].copy()
    
    # Add sample weather data based on team and season
    np.random.seed(42)  # For reproducible results
    
    # Sample weather patterns by team (outdoor vs dome)
    outdoor_teams = ['GB', 'CHI', 'BUF', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT', 
                    'JAX', 'TEN', 'DEN', 'KC', 'PHI', 'WAS', 'CAR', 'TB', 'SF', 'SEA']
    
    for idx, game in games_df.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Determine if teams play in outdoor stadiums
        home_outdoor = home_team in outdoor_teams
        away_outdoor = away_team in outdoor_teams
        
        # Generate weather data
        if home_outdoor:
            # Outdoor stadium weather
            temp = np.random.normal(15, 10)  # Mean 15°C, std 10°C
            wind = np.random.exponential(8)  # Exponential wind
            precip = np.random.exponential(2) if np.random.random() < 0.3 else 0  # 30% chance of rain
            humidity = np.random.normal(60, 20)  # Mean 60%, std 20%
        else:
            # Dome stadium weather
            temp = 21.0  # 70°F
            wind = 0.0
            precip = 0.0
            humidity = 50.0
        
        weather_data.loc[idx, 'home_temp'] = max(-10, min(40, temp))  # Clamp temperature
        weather_data.loc[idx, 'home_wind'] = max(0, min(50, wind))    # Clamp wind
        weather_data.loc[idx, 'home_precip'] = max(0, min(50, precip))  # Clamp precipitation
        weather_data.loc[idx, 'home_humidity'] = max(0, min(100, humidity))  # Clamp humidity
        
        # Away team gets same weather (neutral site games)
        weather_data.loc[idx, 'away_temp'] = weather_data.loc[idx, 'home_temp']
        weather_data.loc[idx, 'away_wind'] = weather_data.loc[idx, 'home_wind']
        weather_data.loc[idx, 'away_precip'] = weather_data.loc[idx, 'home_precip']
        weather_data.loc[idx, 'away_humidity'] = weather_data.loc[idx, 'home_humidity']
    
    return weather_data


def test_weather_adjustments():
    """Test weather adjustment calculations."""
    print("Testing Weather Adjustments...")
    
    # Test various weather conditions
    test_conditions = [
        WeatherConditions(20, 0, 0, 50, False),  # Perfect weather
        WeatherConditions(-5, 25, 10, 80, False),  # Terrible weather
        WeatherConditions(15, 15, 5, 60, False),  # Moderate weather
        WeatherConditions(25, 5, 0, 40, False),   # Good weather
        WeatherConditions(21, 0, 0, 50, True),    # Dome weather
    ]
    
    for i, weather in enumerate(test_conditions):
        impact = calculate_weather_impact(weather)
        print(f"Test {i+1}: Temp={weather.temperature}°C, Wind={weather.wind_speed}km/h, "
              f"Precip={weather.precipitation}mm, Humidity={weather.humidity}%, "
              f"Dome={weather.is_dome} -> Impact: {impact:.2f}")
    
    print("Weather adjustments working!")


if __name__ == "__main__":
    test_weather_adjustments()
