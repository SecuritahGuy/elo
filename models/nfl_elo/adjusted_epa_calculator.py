"""Adjusted EPA calculations with weather and travel context."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AdjustedEPAMetrics:
    """Metrics for adjusted EPA calculations."""
    
    # Raw EPA metrics
    raw_epa: float
    raw_qb_epa: float
    raw_air_epa: float
    raw_yac_epa: float
    
    # Environmental factors
    weather_epa_factor: float
    travel_epa_factor: float
    combined_environmental_factor: float
    
    # Adjusted EPA metrics
    adjusted_epa: float
    adjusted_qb_epa: float
    adjusted_air_epa: float
    adjusted_yac_epa: float
    
    # Play context
    play_type: str
    is_home: bool
    team: str
    opponent: str


class AdjustedEPACalculator:
    """Calculates weather and travel adjusted EPA metrics."""
    
    def __init__(self, epa_data: pd.DataFrame):
        """
        Initialize the adjusted EPA calculator.
        
        Args:
            epa_data: DataFrame with EPA data and environmental context
        """
        self.epa_data = epa_data.copy()
        self.adjusted_metrics: List[AdjustedEPAMetrics] = []
        
    def calculate_adjusted_epa(self) -> pd.DataFrame:
        """
        Calculate adjusted EPA metrics for all plays.
        
        Returns:
            DataFrame with adjusted EPA metrics
        """
        print("Calculating adjusted EPA metrics...")
        
        # Initialize adjusted EPA columns
        adjusted_columns = [
            'adjusted_epa', 'adjusted_qb_epa', 'adjusted_air_epa', 'adjusted_yac_epa',
            'environmental_epa_impact', 'environmental_qb_epa_impact',
            'environmental_air_epa_impact', 'environmental_yac_epa_impact'
        ]
        
        for col in adjusted_columns:
            self.epa_data[col] = 0.0
        
        # Calculate adjusted EPA for each play
        for idx, play in self.epa_data.iterrows():
            adjusted_metrics = self._calculate_play_adjusted_epa(play)
            
            # Store adjusted metrics
            self.epa_data.loc[idx, 'adjusted_epa'] = adjusted_metrics.adjusted_epa
            self.epa_data.loc[idx, 'adjusted_qb_epa'] = adjusted_metrics.adjusted_qb_epa
            self.epa_data.loc[idx, 'adjusted_air_epa'] = adjusted_metrics.adjusted_air_epa
            self.epa_data.loc[idx, 'adjusted_yac_epa'] = adjusted_metrics.adjusted_yac_epa
            
            # Calculate environmental impact
            self.epa_data.loc[idx, 'environmental_epa_impact'] = (
                adjusted_metrics.adjusted_epa - adjusted_metrics.raw_epa
            )
            self.epa_data.loc[idx, 'environmental_qb_epa_impact'] = (
                adjusted_metrics.adjusted_qb_epa - adjusted_metrics.raw_qb_epa
            )
            self.epa_data.loc[idx, 'environmental_air_epa_impact'] = (
                adjusted_metrics.adjusted_air_epa - adjusted_metrics.raw_air_epa
            )
            self.epa_data.loc[idx, 'environmental_yac_epa_impact'] = (
                adjusted_metrics.adjusted_yac_epa - adjusted_metrics.raw_yac_epa
            )
            
            # Store metrics for analysis
            self.adjusted_metrics.append(adjusted_metrics)
        
        print(f"Adjusted EPA calculated for {len(self.epa_data)} plays")
        return self.epa_data
    
    def _calculate_play_adjusted_epa(self, play: pd.Series) -> AdjustedEPAMetrics:
        """
        Calculate adjusted EPA metrics for a single play.
        
        Args:
            play: Series with play data and environmental context
            
        Returns:
            AdjustedEPAMetrics object
        """
        # Extract raw EPA values
        raw_epa = play.get('epa', 0.0)
        raw_qb_epa = play.get('qb_epa', 0.0)
        raw_air_epa = play.get('air_epa', 0.0)
        raw_yac_epa = play.get('yac_epa', 0.0)
        
        # Extract environmental factors
        weather_epa_factor = play.get('weather_epa_factor', 1.0)
        travel_epa_factor = play.get('travel_epa_factor', 1.0)
        combined_environmental_factor = weather_epa_factor * travel_epa_factor
        
        # Calculate play-type specific factors
        play_type = play.get('play_type', 'pass')
        if play_type == 'pass':
            weather_factor = play.get('weather_pass_factor', 1.0)
            travel_factor = play.get('travel_pass_factor', 1.0)
        elif play_type == 'run':
            weather_factor = play.get('weather_rush_factor', 1.0)
            travel_factor = play.get('travel_rush_factor', 1.0)
        else:
            weather_factor = 1.0
            travel_factor = 1.0
        
        # Calculate play-specific environmental factor
        play_environmental_factor = weather_factor * travel_factor
        
        # Apply environmental adjustments
        adjusted_epa = raw_epa * play_environmental_factor
        adjusted_qb_epa = raw_qb_epa * play_environmental_factor
        adjusted_air_epa = raw_air_epa * play_environmental_factor
        adjusted_yac_epa = raw_yac_epa * play_environmental_factor
        
        return AdjustedEPAMetrics(
            raw_epa=raw_epa,
            raw_qb_epa=raw_qb_epa,
            raw_air_epa=raw_air_epa,
            raw_yac_epa=raw_yac_epa,
            weather_epa_factor=weather_epa_factor,
            travel_epa_factor=travel_epa_factor,
            combined_environmental_factor=combined_environmental_factor,
            adjusted_epa=adjusted_epa,
            adjusted_qb_epa=adjusted_qb_epa,
            adjusted_air_epa=adjusted_air_epa,
            adjusted_yac_epa=adjusted_yac_epa,
            play_type=play_type,
            is_home=play.get('posteam') == play.get('home_team'),
            team=play.get('posteam', ''),
            opponent=play.get('defteam', '')
        )
    
    def get_team_adjusted_epa_summary(self, team: str, season: int, week: int) -> Dict[str, float]:
        """
        Get adjusted EPA summary for a team in a specific week.
        
        Args:
            team: Team abbreviation
            season: Season year
            week: Week number
            
        Returns:
            Dictionary with adjusted EPA metrics
        """
        team_plays = self.epa_data[
            (self.epa_data['posteam'] == team) &
            (self.epa_data['season'] == season) &
            (self.epa_data['week'] == week)
        ]
        
        if team_plays.empty:
            return {
                'total_plays': 0,
                'raw_total_epa': 0.0,
                'adjusted_total_epa': 0.0,
                'raw_avg_epa': 0.0,
                'adjusted_avg_epa': 0.0,
                'environmental_impact': 0.0,
                'weather_impact': 0.0,
                'travel_impact': 0.0
            }
        
        return {
            'total_plays': len(team_plays),
            'raw_total_epa': team_plays['epa'].sum(),
            'adjusted_total_epa': team_plays['adjusted_epa'].sum(),
            'raw_avg_epa': team_plays['epa'].mean(),
            'adjusted_avg_epa': team_plays['adjusted_epa'].mean(),
            'environmental_impact': team_plays['environmental_epa_impact'].sum(),
            'weather_impact': (team_plays['weather_epa_factor'] - 1.0).sum(),
            'travel_impact': (team_plays['travel_epa_factor'] - 1.0).sum()
        }
    
    def get_qb_adjusted_epa_summary(self, qb_name: str, season: int, week: int) -> Dict[str, float]:
        """
        Get adjusted EPA summary for a QB in a specific week.
        
        Args:
            qb_name: QB name
            season: Season year
            week: Week number
            
        Returns:
            Dictionary with adjusted EPA metrics
        """
        qb_plays = self.epa_data[
            (self.epa_data['passer_player_name'] == qb_name) &
            (self.epa_data['season'] == season) &
            (self.epa_data['week'] == week)
        ]
        
        if qb_plays.empty:
            return {
                'total_plays': 0,
                'raw_total_qb_epa': 0.0,
                'adjusted_total_qb_epa': 0.0,
                'raw_avg_qb_epa': 0.0,
                'adjusted_avg_qb_epa': 0.0,
                'environmental_impact': 0.0
            }
        
        return {
            'total_plays': len(qb_plays),
            'raw_total_qb_epa': qb_plays['qb_epa'].sum(),
            'adjusted_total_qb_epa': qb_plays['adjusted_qb_epa'].sum(),
            'raw_avg_qb_epa': qb_plays['qb_epa'].mean(),
            'adjusted_avg_qb_epa': qb_plays['adjusted_qb_epa'].mean(),
            'environmental_impact': qb_plays['environmental_qb_epa_impact'].sum()
        }
    
    def get_environmental_impact_analysis(self) -> Dict[str, float]:
        """
        Get overall environmental impact analysis.
        
        Returns:
            Dictionary with environmental impact metrics
        """
        if self.epa_data.empty:
            return {}
        
        # Overall impact
        total_raw_epa = self.epa_data['epa'].sum()
        total_adjusted_epa = self.epa_data['adjusted_epa'].sum()
        total_environmental_impact = total_adjusted_epa - total_raw_epa
        
        # Weather vs Travel impact
        weather_impact = (self.epa_data['weather_epa_factor'] - 1.0).sum()
        travel_impact = (self.epa_data['travel_epa_factor'] - 1.0).sum()
        
        # Play type analysis
        pass_plays = self.epa_data[self.epa_data['play_type'] == 'pass']
        run_plays = self.epa_data[self.epa_data['play_type'] == 'run']
        
        pass_environmental_impact = 0.0
        run_environmental_impact = 0.0
        
        if not pass_plays.empty:
            pass_environmental_impact = (pass_plays['adjusted_epa'] - pass_plays['epa']).sum()
        
        if not run_plays.empty:
            run_environmental_impact = (run_plays['adjusted_epa'] - run_plays['epa']).sum()
        
        return {
            'total_plays': len(self.epa_data),
            'total_raw_epa': total_raw_epa,
            'total_adjusted_epa': total_adjusted_epa,
            'total_environmental_impact': total_environmental_impact,
            'environmental_impact_percentage': (total_environmental_impact / abs(total_raw_epa)) * 100 if total_raw_epa != 0 else 0,
            'weather_impact': weather_impact,
            'travel_impact': travel_impact,
            'pass_environmental_impact': pass_environmental_impact,
            'run_environmental_impact': run_environmental_impact,
            'avg_weather_factor': self.epa_data['weather_epa_factor'].mean(),
            'avg_travel_factor': self.epa_data['travel_epa_factor'].mean(),
            'avg_combined_factor': (self.epa_data['weather_epa_factor'] * self.epa_data['travel_epa_factor']).mean()
        }


def test_adjusted_epa_calculator():
    """Test the adjusted EPA calculator."""
    print("Testing Adjusted EPA Calculator...")
    
    # Load EPA data with environmental context
    from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context
    
    epa_data = load_epa_with_weather_and_travel_context([2023], sample_size=1000)
    print(f"Loaded {len(epa_data)} plays with environmental context")
    
    # Initialize calculator
    calculator = AdjustedEPACalculator(epa_data)
    
    # Calculate adjusted EPA
    adjusted_epa_data = calculator.calculate_adjusted_epa()
    
    # Show sample results
    print("\nSample adjusted EPA data:")
    sample_cols = ['season', 'week', 'posteam', 'play_type', 'epa', 'adjusted_epa', 
                  'weather_epa_factor', 'travel_epa_factor', 'environmental_epa_impact']
    available_cols = [col for col in sample_cols if col in adjusted_epa_data.columns]
    print(adjusted_epa_data[available_cols].head(10).to_string())
    
    # Show environmental impact analysis
    print("\nEnvironmental Impact Analysis:")
    impact_analysis = calculator.get_environmental_impact_analysis()
    for key, value in impact_analysis.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Show team example
    print("\nTeam EPA Summary Example (WAS Week 1):")
    team_summary = calculator.get_team_adjusted_epa_summary('WAS', 2023, 1)
    for key, value in team_summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    print("\nAdjusted EPA Calculator test complete!")


if __name__ == "__main__":
    test_adjusted_epa_calculator()
