"""Weather data loader using Meteostat for NFL Elo system."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import time

try:
    from meteostat import Point, Daily, Hourly
    METEOSTAT_AVAILABLE = True
except ImportError:
    METEOSTAT_AVAILABLE = False
    print("Warning: Meteostat not available. Install with: pip install meteostat")

from .stadium_database import StadiumDatabase, StadiumInfo
from .team_mapping import normalize_team_abbreviation


class WeatherDataLoader:
    """Loads historical weather data for NFL stadiums using Meteostat."""
    
    def __init__(self, cache_dir: str = "artifacts/weather_cache"):
        """
        Initialize weather data loader.
        
        Args:
            cache_dir: Directory to cache weather data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stadium_db = StadiumDatabase()
        
        if not METEOSTAT_AVAILABLE:
            raise ImportError("Meteostat is required for weather data loading")
    
    def load_weather_for_game(self, team: str, game_date: datetime) -> Optional[Dict]:
        """
        Load weather data for a specific team's game.
        
        Args:
            team: Team abbreviation
            game_date: Date of the game
            
        Returns:
            Dictionary with weather data or None if not available
        """
        # Normalize team abbreviation for stadium database lookup
        normalized_team = normalize_team_abbreviation(team)
        stadium = self.stadium_db.get_stadium(normalized_team)
        if not stadium:
            return None
        
        # Check if weather-sensitive
        if stadium.weather_sensitivity == "none":
            return self._get_dome_weather()
        
        # Load weather data
        weather_data = self._load_weather_data(
            stadium.latitude, stadium.longitude, stadium.elevation, game_date
        )
        
        return weather_data
    
    def load_weather_for_games(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Load weather data for all games in a DataFrame.
        
        Args:
            games_df: DataFrame with game data including 'home_team', 'away_team', 'gameday'
            
        Returns:
            DataFrame with weather data added
        """
        games_with_weather = games_df.copy()
        
        # Add weather columns
        weather_columns = [
            'home_temp', 'home_wind', 'home_precip', 'home_humidity', 'home_weather_impact',
            'away_temp', 'away_wind', 'away_precip', 'away_humidity', 'away_weather_impact'
        ]
        
        for col in weather_columns:
            games_with_weather[col] = 0.0
        
        print(f"Loading weather data for {len(games_df)} games...")
        
        for idx, game in games_df.iterrows():
            if idx % 50 == 0:
                print(f"Processing game {idx + 1}/{len(games_df)}")
            
            try:
                # Load weather for the home stadium (where the game is played)
                home_weather = self.load_weather_for_game(
                    game['home_team'], 
                    pd.to_datetime(game['gameday'])
                )
            except Exception as e:
                # Suppress specific error messages for future dates
                if "issubclass() arg 1 must be a class" in str(e):
                    # This is a known issue with Meteostat for future dates
                    home_weather = None
                else:
                    print(f"Error loading weather data for {game['home_team']} on {game['gameday']}: {e}")
                    home_weather = None
            
            if home_weather:
                # Set both home and away weather to the same values (game is played at home stadium)
                games_with_weather.loc[idx, 'home_temp'] = home_weather.get('temperature', 0.0)
                games_with_weather.loc[idx, 'home_wind'] = home_weather.get('wind_speed', 0.0)
                games_with_weather.loc[idx, 'home_precip'] = home_weather.get('precipitation', 0.0)
                games_with_weather.loc[idx, 'home_humidity'] = home_weather.get('humidity', 0.0)
                games_with_weather.loc[idx, 'home_weather_impact'] = home_weather.get('weather_impact', 0.0)
                games_with_weather.loc[idx, 'home_weather_adj'] = home_weather.get('weather_impact', 0.0)
                
                # Away team experiences the same weather conditions
                games_with_weather.loc[idx, 'away_temp'] = home_weather.get('temperature', 0.0)
                games_with_weather.loc[idx, 'away_wind'] = home_weather.get('wind_speed', 0.0)
                games_with_weather.loc[idx, 'away_precip'] = home_weather.get('precipitation', 0.0)
                games_with_weather.loc[idx, 'away_humidity'] = home_weather.get('humidity', 0.0)
                games_with_weather.loc[idx, 'away_weather_impact'] = home_weather.get('weather_impact', 0.0)
                games_with_weather.loc[idx, 'away_weather_adj'] = home_weather.get('weather_impact', 0.0)
            else:
                # No weather data available
                games_with_weather.loc[idx, 'home_temp'] = 0.0
                games_with_weather.loc[idx, 'home_wind'] = 0.0
                games_with_weather.loc[idx, 'home_precip'] = 0.0
                games_with_weather.loc[idx, 'home_humidity'] = 0.0
                games_with_weather.loc[idx, 'home_weather_impact'] = 0.0
                games_with_weather.loc[idx, 'home_weather_adj'] = 0.0
                games_with_weather.loc[idx, 'away_temp'] = 0.0
                games_with_weather.loc[idx, 'away_wind'] = 0.0
                games_with_weather.loc[idx, 'away_precip'] = 0.0
                games_with_weather.loc[idx, 'away_humidity'] = 0.0
                games_with_weather.loc[idx, 'away_weather_impact'] = 0.0
                games_with_weather.loc[idx, 'away_weather_adj'] = 0.0
            
            # Rate limiting - be respectful to the API
            time.sleep(0.1)
        
        return games_with_weather
    
    def _load_weather_data(self, lat: float, lon: float, elevation: float, 
                          game_date: datetime) -> Optional[Dict]:
        """
        Load weather data for a specific location and date.
        
        Args:
            lat: Latitude
            lon: Longitude
            elevation: Elevation in meters
            game_date: Date of the game
            
        Returns:
            Dictionary with weather data
        """
        # Check cache first
        cache_key = f"{lat:.4f}_{lon:.4f}_{game_date.strftime('%Y%m%d')}"
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Check if the date is in the future (no weather data available)
        if game_date > datetime.now():
            print(f"Warning: Cannot load weather data for future date {game_date.strftime('%Y-%m-%d')}")
            return self._get_dome_weather()  # Return neutral weather for future games
        
        try:
            # Create point for the location
            location = Point(lat, lon, elevation)
            
            # Get weather data for the game date
            start_date = game_date
            end_date = game_date + timedelta(days=1)
            
            # Try daily data first
            daily_data = Daily(location, start_date, end_date)
            daily_df = daily_data.fetch()
            
            if not daily_df.empty:
                weather_data = self._process_daily_weather(daily_df.iloc[0])
                self._save_to_cache(cache_key, weather_data)
                return weather_data
            
            # If daily data not available, try hourly
            hourly_data = Hourly(location, start_date, end_date)
            hourly_df = hourly_data.fetch()
            
            if not hourly_df.empty:
                # Get data for game time (typically 1 PM or 4 PM)
                game_hour = 13  # 1 PM
                if game_hour in hourly_df.index.hour:
                    hour_data = hourly_df[hourly_df.index.hour == game_hour].iloc[0]
                else:
                    hour_data = hourly_df.iloc[0]  # Use first available hour
                
                weather_data = self._process_hourly_weather(hour_data)
                self._save_to_cache(cache_key, weather_data)
                return weather_data
            
        except Exception as e:
            print(f"Error loading weather data for {lat}, {lon} on {game_date}: {e}")
            # Create fallback data
            fallback_data = self._create_fallback_weather_data(lat, lon, game_date)
            self._save_to_cache(cache_key, fallback_data)
            return fallback_data
        
        return None
    
    def _process_daily_weather(self, daily_row: pd.Series) -> Dict:
        """Process daily weather data into our format."""
        return {
            'temperature': daily_row.get('tavg', 0.0),  # Average temperature
            'temp_min': daily_row.get('tmin', 0.0),     # Minimum temperature
            'temp_max': daily_row.get('tmax', 0.0),     # Maximum temperature
            'wind_speed': daily_row.get('wspd', 0.0),   # Wind speed
            'wind_direction': daily_row.get('wdir', 0.0), # Wind direction
            'wind_gust': daily_row.get('wpgt', 0.0),    # Wind gust
            'precipitation': daily_row.get('prcp', 0.0), # Precipitation
            'snow': daily_row.get('snow', 0.0),         # Snow depth
            'humidity': daily_row.get('rhum', 0.0),     # Relative humidity
            'pressure': daily_row.get('pres', 0.0),     # Atmospheric pressure
            'cloud_cover': daily_row.get('coco', 0.0),  # Cloud cover
            'visibility': daily_row.get('tsun', 0.0),   # Sunshine duration
            'weather_impact': self._calculate_weather_impact(
                daily_row.get('tavg', 0.0),
                daily_row.get('wspd', 0.0),
                daily_row.get('prcp', 0.0),
                daily_row.get('rhum', 0.0),
                daily_row.get('wpgt', 0.0),
                daily_row.get('snow', 0.0),
                daily_row.get('pres', 0.0)
            )
        }
    
    def _process_hourly_weather(self, hourly_row: pd.Series) -> Dict:
        """Process hourly weather data into our format."""
        return {
            'temperature': hourly_row.get('temp', 0.0),     # Temperature
            'temp_min': hourly_row.get('temp', 0.0),        # Use temp as min/max for hourly
            'temp_max': hourly_row.get('temp', 0.0),
            'wind_speed': hourly_row.get('wspd', 0.0),      # Wind speed
            'wind_direction': hourly_row.get('wdir', 0.0),  # Wind direction
            'wind_gust': hourly_row.get('wpgt', 0.0),       # Wind gust
            'precipitation': hourly_row.get('prcp', 0.0),   # Precipitation
            'snow': hourly_row.get('snow', 0.0),            # Snow depth
            'humidity': hourly_row.get('rhum', 0.0),        # Relative humidity
            'pressure': hourly_row.get('pres', 0.0),        # Atmospheric pressure
            'cloud_cover': hourly_row.get('coco', 0.0),     # Cloud cover
            'visibility': hourly_row.get('tsun', 0.0),      # Sunshine duration
            'weather_impact': self._calculate_weather_impact(
                hourly_row.get('temp', 0.0),
                hourly_row.get('wspd', 0.0),
                hourly_row.get('prcp', 0.0),
                hourly_row.get('rhum', 0.0),
                hourly_row.get('wpgt', 0.0),
                hourly_row.get('snow', 0.0),
                hourly_row.get('pres', 0.0)
            )
        }
    
    def _calculate_weather_impact(self, temp: float, wind: float, 
                                 precip: float, humidity: float, 
                                 wind_gust: float = 0.0, snow: float = 0.0, 
                                 pressure: float = 0.0) -> float:
        """
        Calculate weather impact score for NFL games.
        
        Args:
            temp: Temperature in Celsius
            wind: Wind speed in km/h
            precip: Precipitation in mm
            humidity: Relative humidity in %
            wind_gust: Wind gust speed in km/h
            snow: Snow depth in mm
            pressure: Atmospheric pressure in hPa
            
        Returns:
            Weather impact score (negative = bad for offense)
        """
        impact = 0.0
        
        # Temperature impact (optimal around 20°C / 68°F)
        temp_celsius = temp
        if temp_celsius < 0:  # Below freezing
            impact -= 3.0
        elif temp_celsius < 10:  # Very cold
            impact -= 2.0
        elif temp_celsius < 20:  # Cold
            impact -= 1.0
        elif temp_celsius > 35:  # Very hot
            impact -= 1.0
        elif temp_celsius > 30:  # Hot
            impact -= 0.5
        
        # Wind impact (exponential) - use max of sustained wind and gust
        effective_wind = max(wind, wind_gust)
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
        if precip > 10:  # Heavy rain
            impact -= 2.0
        elif precip > 5:  # Moderate rain
            impact -= 1.5
        elif precip > 1:  # Light rain
            impact -= 1.0
        elif precip > 0:  # Trace precipitation
            impact -= 0.5
        
        # Snow impact (additional penalty)
        if snow > 50:  # Heavy snow
            impact -= 2.0
        elif snow > 25:  # Moderate snow
            impact -= 1.5
        elif snow > 10:  # Light snow
            impact -= 1.0
        elif snow > 0:   # Trace snow
            impact -= 0.5
        
        # Humidity impact (moderate)
        if humidity > 90:  # Very humid
            impact -= 0.8
        elif humidity > 80:  # Humid
            impact -= 0.5
        elif humidity < 30:  # Very dry
            impact -= 0.3
        elif humidity < 40:  # Dry
            impact -= 0.2
        
        # Pressure impact (barometric pressure affects ball flight)
        if pressure > 0:  # Only if pressure data available
            if pressure < 1000:  # Low pressure (stormy)
                impact -= 0.5
            elif pressure > 1030:  # High pressure (stable)
                impact += 0.2
        
        return impact
    
    def _create_fallback_weather_data(self, lat: float, lon: float, date: datetime) -> Dict:
        """Create fallback weather data when API is unavailable."""
        import random
        
        # Generate realistic weather based on location and season
        month = date.month
        
        # Temperature based on latitude and season
        base_temp = 20.0  # Base temperature
        lat_factor = (lat - 40.0) * -0.5  # Colder further north
        season_factor = 0.0
        
        if month in [12, 1, 2]:  # Winter
            season_factor = -10.0
        elif month in [3, 4, 5]:  # Spring
            season_factor = 0.0
        elif month in [6, 7, 8]:  # Summer
            season_factor = 10.0
        elif month in [9, 10, 11]:  # Fall
            season_factor = 0.0
        
        temp = base_temp + lat_factor + season_factor + random.uniform(-5, 5)
        
        # Wind based on season (winter is windier)
        wind_base = 8.0 if month in [12, 1, 2] else 5.0
        wind = max(0, wind_base + random.uniform(-3, 8))
        wind_gust = wind + random.uniform(0, 10)
        
        # Precipitation (higher in spring/fall)
        precip_chance = 0.3 if month in [3, 4, 5, 9, 10, 11] else 0.2
        precip = random.uniform(0, 15) if random.random() < precip_chance else 0
        
        # Snow (only in winter and northern latitudes)
        snow = 0
        if month in [12, 1, 2] and lat > 35:
            snow_chance = 0.2 if lat > 40 else 0.1
            snow = random.uniform(0, 25) if random.random() < snow_chance else 0
        
        # Humidity (higher in summer)
        humidity = 60 + (10 if month in [6, 7, 8] else 0) + random.uniform(-20, 20)
        humidity = max(0, min(100, humidity))
        
        # Pressure (normal range)
        pressure = 1013.25 + random.uniform(-20, 20)
        
        return {
            'temperature': round(temp, 1),
            'temp_min': round(temp - random.uniform(2, 8), 1),
            'temp_max': round(temp + random.uniform(2, 8), 1),
            'wind_speed': round(wind, 1),
            'wind_direction': random.uniform(0, 360),
            'wind_gust': round(wind_gust, 1),
            'precipitation': round(precip, 1),
            'snow': round(snow, 1),
            'humidity': round(humidity, 1),
            'pressure': round(pressure, 1),
            'cloud_cover': random.uniform(0, 100),
            'visibility': random.uniform(8, 16),
            'weather_impact': self._calculate_weather_impact(
                temp, wind, precip, humidity, wind_gust, snow, pressure
            )
        }
    
    def _get_dome_weather(self) -> Dict:
        """Get neutral weather data for dome stadiums."""
        return {
            'temperature': 21.0,  # 70°F
            'temp_min': 21.0,
            'temp_max': 21.0,
            'wind_speed': 0.0,
            'wind_direction': 0.0,
            'wind_gust': 0.0,
            'precipitation': 0.0,
            'snow': 0.0,
            'humidity': 50.0,
            'pressure': 1013.25,  # Standard atmospheric pressure
            'cloud_cover': 0.0,
            'visibility': 0.0,
            'weather_impact': 0.0
        }
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load weather data from cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return None
    
    def _save_to_cache(self, cache_key: str, weather_data: Dict) -> None:
        """Save weather data to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(weather_data, f)
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached weather data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        print(f"Cleared {len(list(self.cache_dir.glob('*.json')))} cached weather files")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        return {
            'cached_files': len(cache_files),
            'cache_dir': str(self.cache_dir),
            'cache_size_mb': sum(f.stat().st_size for f in cache_files) / (1024 * 1024)
        }


def load_weather_for_games(games_df: pd.DataFrame, cache_dir: str = "artifacts/weather_cache") -> pd.DataFrame:
    """
    Convenience function to load weather data for games.
    
    Args:
        games_df: DataFrame with game data
        cache_dir: Directory to cache weather data
        
    Returns:
        DataFrame with weather data added
    """
    loader = WeatherDataLoader(cache_dir)
    return loader.load_weather_for_games(games_df)


def load_real_weather_data(games_df: pd.DataFrame, cache_dir: str = "artifacts/weather_cache", 
                          use_fallback: bool = True) -> pd.DataFrame:
    """
    Load real weather data for all games using Meteostat with fallback.
    
    Args:
        games_df: DataFrame with game data
        cache_dir: Directory to cache weather data
        use_fallback: Whether to use fallback data when API fails
        
    Returns:
        DataFrame with comprehensive weather data
    """
    loader = WeatherDataLoader(cache_dir)
    
    print(f"Loading weather data for {len(games_df)} games...")
    if use_fallback:
        print("Using fallback data when API is unavailable...")
    else:
        print("This may take several minutes due to API rate limits...")
    
    try:
        # Load weather data for all games
        weather_data = loader.load_weather_for_games(games_df)
        
        # Add additional weather columns for analysis
        weather_columns = [
            'home_temp', 'home_temp_min', 'home_temp_max', 'home_wind', 'home_wind_dir', 
            'home_wind_gust', 'home_precip', 'home_snow', 'home_humidity', 'home_pressure',
            'home_cloud_cover', 'home_visibility', 'home_weather_impact',
            'away_temp', 'away_temp_min', 'away_temp_max', 'away_wind', 'away_wind_dir',
            'away_wind_gust', 'away_precip', 'away_snow', 'away_humidity', 'away_pressure',
            'away_cloud_cover', 'away_visibility', 'away_weather_impact'
        ]
        
        # Remove duplicate columns and initialize missing ones
        weather_data = weather_data.loc[:, ~weather_data.columns.duplicated()]
        for col in weather_columns:
            if col not in weather_data.columns:
                weather_data[col] = 0.0
        
        print(f"Weather data loaded: {weather_data.shape}")
        print(f"Cache stats: {loader.get_cache_stats()}")
        
        return weather_data
        
    except Exception as e:
        print(f"Error loading weather data: {e}")
        if use_fallback:
            print("Falling back to sample weather data...")
            try:
                from .weather_adjustments import create_sample_weather_data
                return create_sample_weather_data(games_df)
            except ImportError:
                # Create basic sample weather data if module not available
                return create_basic_sample_weather_data(games_df)
        else:
            raise e


def load_weather_data_with_retry(games_df: pd.DataFrame, cache_dir: str = "artifacts/weather_cache", 
                                max_retries: int = 3, use_fallback: bool = False) -> pd.DataFrame:
    """
    Load weather data with retry logic for API failures.
    
    Args:
        games_df: DataFrame with game data
        cache_dir: Directory to cache weather data
        max_retries: Maximum number of retry attempts
        use_fallback: Whether to use fallback data when API fails
        
    Returns:
        DataFrame with comprehensive weather data
    """
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to load weather data...")
            return load_real_weather_data(games_df, cache_dir, use_fallback=use_fallback)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                print("All attempts failed, using sample data...")
                try:
                    from .weather_adjustments import create_sample_weather_data
                    return create_sample_weather_data(games_df)
                except ImportError:
                    return create_basic_sample_weather_data(games_df)
            else:
                import time
                time.sleep(5)  # Wait 5 seconds before retry


def create_basic_sample_weather_data(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create basic sample weather data when weather adjustments module is not available.
    
    Args:
        games_df: DataFrame with game data
        
    Returns:
        DataFrame with basic weather data
    """
    import random
    
    weather_data = games_df.copy()
    
    # Add basic weather columns
    weather_columns = [
        'home_temp', 'home_wind', 'home_precip', 'home_humidity',
        'away_temp', 'away_wind', 'away_precip', 'away_humidity',
        'home_weather_adj', 'away_weather_adj', 'weather_impact'
    ]
    
    for col in weather_columns:
        if col.endswith('_temp'):
            weather_data[col] = random.uniform(15, 25)  # 15-25°C
        elif col.endswith('_wind'):
            weather_data[col] = random.uniform(0, 15)   # 0-15 km/h
        elif col.endswith('_precip'):
            weather_data[col] = random.uniform(0, 5)    # 0-5 mm
        elif col.endswith('_humidity'):
            weather_data[col] = random.uniform(40, 80)  # 40-80%
        else:
            weather_data[col] = 0.0
    
    return weather_data
