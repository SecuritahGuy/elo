"""Injury integration system for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .evaluator import calculate_all_metrics
from ingest.nfl.data_loader import load_games


class InjuryImpactCalculator:
    """Calculates injury impact on team performance and Elo ratings."""
    
    def __init__(self):
        """Initialize injury impact calculator."""
        # Position importance weights (based on NFL analytics research)
        self.position_weights = {
            'QB': 3.0,    # Most important position
            'T': 1.5,     # Offensive tackle (pass protection)
            'G': 1.2,     # Offensive guard
            'C': 1.3,     # Center (snap and blocking calls)
            'WR': 1.4,    # Wide receiver
            'TE': 1.1,    # Tight end
            'RB': 1.0,    # Running back
            'FB': 0.8,    # Fullback
            'DE': 1.6,    # Defensive end (pass rush)
            'DT': 1.3,    # Defensive tackle
            'LB': 1.4,    # Linebacker
            'CB': 1.5,    # Cornerback
            'S': 1.3,     # Safety
            'K': 0.3,     # Kicker
            'P': 0.2,     # Punter
            'LS': 0.1,    # Long snapper
            'FB': 0.8     # Fullback (duplicate, but keeping for clarity)
        }
        
        # Injury severity weights
        self.injury_severity_weights = {
            'Out': 1.0,           # Player definitely out
            'Doubtful': 0.8,      # Player likely out
            'Questionable': 0.5,  # Player uncertain
            'None': 0.0           # No injury report
        }
        
        # Practice participation weights
        self.practice_weights = {
            'Did Not Participate In Practice': 0.9,
            'Limited Participation in Practice': 0.6,
            'Full Participation in Practice': 0.1,
            '': 0.0  # Empty string
        }
        
        # Injury type severity (based on typical recovery time)
        self.injury_type_weights = {
            'Knee': 0.9,          # ACL, MCL, meniscus
            'Ankle': 0.7,         # Sprains, fractures
            'Hamstring': 0.6,     # Muscle strains
            'Concussion': 0.8,    # Head injuries
            'Shoulder': 0.7,      # Shoulder injuries
            'Illness': 0.4,       # Non-injury related
            'Calf': 0.5,          # Muscle strains
            'Foot': 0.6,          # Foot injuries
            'Back': 0.7,          # Back injuries
            'Groin': 0.6,         # Groin strains
            'None': 0.0           # No injury
        }
    
    def load_injury_data(self, years: List[int]) -> pd.DataFrame:
        """
        Load injury data for specified years.
        
        Args:
            years: Years to load injury data for
            
        Returns:
            DataFrame with injury data
        """
        import nfl_data_py as nfl
        
        print(f"Loading injury data for years {years}...")
        injuries = nfl.import_injuries(years)
        print(f"Loaded {len(injuries)} injury records")
        
        # Clean and standardize data
        injuries = self._clean_injury_data(injuries)
        
        return injuries
    
    def _clean_injury_data(self, injuries: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize injury data."""
        # Fill missing values
        injuries['report_status'] = injuries['report_status'].fillna('None')
        injuries['practice_status'] = injuries['practice_status'].fillna('')
        injuries['report_primary_injury'] = injuries['report_primary_injury'].fillna('None')
        
        # Convert to proper types
        injuries['week'] = pd.to_numeric(injuries['week'], errors='coerce')
        injuries['season'] = pd.to_numeric(injuries['season'], errors='coerce')
        
        # Filter for regular season games only
        injuries = injuries[injuries['game_type'] == 'REG'].copy()
        
        # Remove rows with missing essential data
        injuries = injuries.dropna(subset=['team', 'position', 'week', 'season'])
        
        print(f"Cleaned injury data: {len(injuries)} records")
        return injuries
    
    def calculate_player_injury_impact(self, player_injury: pd.Series) -> float:
        """
        Calculate injury impact for a single player.
        
        Args:
            player_injury: Series with player injury data
            
        Returns:
            Injury impact score (0.0 = no impact, 1.0 = maximum impact)
        """
        # Get position weight
        position = player_injury['position']
        position_weight = self.position_weights.get(position, 1.0)
        
        # Get injury severity weight
        report_status = player_injury['report_status']
        injury_severity = self.injury_severity_weights.get(report_status, 0.0)
        
        # Get practice participation weight
        practice_status = player_injury['practice_status']
        practice_weight = self.practice_weights.get(practice_status, 0.0)
        
        # Get injury type weight
        injury_type = player_injury['report_primary_injury']
        injury_type_weight = self.injury_type_weights.get(injury_type, 0.5)
        
        # Calculate combined impact
        # Weight the different factors
        impact = (
            position_weight * 0.4 +  # Position importance
            injury_severity * 0.3 +  # Injury severity
            practice_weight * 0.2 +  # Practice participation
            injury_type_weight * 0.1  # Injury type
        )
        
        # Normalize to [0, 1] range
        impact = min(1.0, max(0.0, impact / 3.0))  # Max position weight is 3.0
        
        return impact
    
    def calculate_team_injury_impact(self, team_injuries: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate injury impact for a team.
        
        Args:
            team_injuries: DataFrame with team's injury data for a specific week
            
        Returns:
            Dictionary with team injury impact metrics
        """
        if len(team_injuries) == 0:
            return {
                'total_impact': 0.0,
                'offensive_impact': 0.0,
                'defensive_impact': 0.0,
                'key_position_impact': 0.0,
                'injured_players': 0,
                'out_players': 0
            }
        
        # Calculate individual player impacts
        player_impacts = []
        for _, player in team_injuries.iterrows():
            impact = self.calculate_player_injury_impact(player)
            player_impacts.append({
                'player': player['full_name'],
                'position': player['position'],
                'impact': impact,
                'status': player['report_status']
            })
        
        # Calculate team metrics
        total_impact = sum(p['impact'] for p in player_impacts)
        
        # Offensive positions
        offensive_positions = {'QB', 'RB', 'WR', 'TE', 'T', 'G', 'C', 'FB'}
        offensive_impact = sum(
            p['impact'] for p in player_impacts 
            if p['position'] in offensive_positions
        )
        
        # Defensive positions
        defensive_positions = {'DE', 'DT', 'LB', 'CB', 'S'}
        defensive_impact = sum(
            p['impact'] for p in player_impacts 
            if p['position'] in defensive_positions
        )
        
        # Key positions (QB, top WR, top RB, top CB, etc.)
        key_positions = {'QB', 'WR', 'RB', 'CB', 'DE', 'LB'}
        key_position_impact = sum(
            p['impact'] for p in player_impacts 
            if p['position'] in key_positions
        )
        
        # Count injured players
        injured_players = len([p for p in player_impacts if p['impact'] > 0.1])
        out_players = len([p for p in player_impacts if p['status'] == 'Out'])
        
        return {
            'total_impact': total_impact,
            'offensive_impact': offensive_impact,
            'defensive_impact': defensive_impact,
            'key_position_impact': key_position_impact,
            'injured_players': injured_players,
            'out_players': out_players,
            'player_details': player_impacts
        }
    
    def create_team_injury_database(self, injuries: pd.DataFrame) -> pd.DataFrame:
        """
        Create a database of team injury impacts by week.
        
        Args:
            injuries: DataFrame with injury data
            
        Returns:
            DataFrame with team injury impacts by week
        """
        print("Creating team injury database...")
        
        team_injury_data = []
        
        # Group by team, season, and week
        for (team, season, week), team_injuries in injuries.groupby(['team', 'season', 'week']):
            impact_metrics = self.calculate_team_injury_impact(team_injuries)
            
            team_injury_data.append({
                'team': team,
                'season': season,
                'week': week,
                'total_impact': impact_metrics['total_impact'],
                'offensive_impact': impact_metrics['offensive_impact'],
                'defensive_impact': impact_metrics['defensive_impact'],
                'key_position_impact': impact_metrics['key_position_impact'],
                'injured_players': impact_metrics['injured_players'],
                'out_players': impact_metrics['out_players']
            })
        
        team_injury_df = pd.DataFrame(team_injury_data)
        print(f"Created team injury database with {len(team_injury_df)} records")
        
        return team_injury_df
    
    def add_injury_data_to_games(self, games: pd.DataFrame, team_injury_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add injury data to games DataFrame.
        
        Args:
            games: DataFrame with game data
            team_injury_df: DataFrame with team injury impacts
            
        Returns:
            DataFrame with injury data added
        """
        print("Adding injury data to games...")
        
        # Create a copy to avoid modifying original
        games_with_injuries = games.copy()
        
        # Add injury data for home teams
        home_injuries = team_injury_df.rename(columns={
            'team': 'home_team',
            'total_impact': 'home_injury_impact',
            'offensive_impact': 'home_offensive_injury_impact',
            'defensive_impact': 'home_defensive_injury_impact',
            'key_position_impact': 'home_key_position_injury_impact',
            'injured_players': 'home_injured_players',
            'out_players': 'home_out_players'
        })
        
        games_with_injuries = games_with_injuries.merge(
            home_injuries[['home_team', 'season', 'week', 'home_injury_impact', 
                          'home_offensive_injury_impact', 'home_defensive_injury_impact',
                          'home_key_position_injury_impact', 'home_injured_players', 
                          'home_out_players']],
            on=['home_team', 'season', 'week'],
            how='left'
        )
        
        # Add injury data for away teams
        away_injuries = team_injury_df.rename(columns={
            'team': 'away_team',
            'total_impact': 'away_injury_impact',
            'offensive_impact': 'away_offensive_injury_impact',
            'defensive_impact': 'away_defensive_injury_impact',
            'key_position_impact': 'away_key_position_injury_impact',
            'injured_players': 'away_injured_players',
            'out_players': 'away_out_players'
        })
        
        games_with_injuries = games_with_injuries.merge(
            away_injuries[['away_team', 'season', 'week', 'away_injury_impact',
                          'away_offensive_injury_impact', 'away_defensive_injury_impact',
                          'away_key_position_injury_impact', 'away_injured_players',
                          'away_out_players']],
            on=['away_team', 'season', 'week'],
            how='left'
        )
        
        # Fill missing values with 0 (no injury impact)
        injury_columns = [col for col in games_with_injuries.columns if 'injury' in col or 'injured' in col or 'out_players' in col]
        for col in injury_columns:
            games_with_injuries[col] = games_with_injuries[col].fillna(0.0)
        
        print(f"Added injury data to {len(games_with_injuries)} games")
        return games_with_injuries


class InjuryAdjustedElo:
    """Elo system with injury adjustments."""
    
    def __init__(self, config: EloConfig):
        """
        Initialize injury-adjusted Elo system.
        
        Args:
            config: Elo configuration
        """
        self.config = config
        self.injury_calculator = InjuryImpactCalculator()
    
    def calculate_injury_adjustment(self, game: pd.Series) -> Tuple[float, float]:
        """
        Calculate injury adjustments for a game.
        
        Args:
            game: Series with game data including injury information
            
        Returns:
            Tuple of (home_adjustment, away_adjustment)
        """
        # Get injury impacts
        home_injury_impact = game.get('home_injury_impact', 0.0)
        away_injury_impact = game.get('away_injury_impact', 0.0)
        
        # Get key position impacts (more important)
        home_key_impact = game.get('home_key_position_injury_impact', 0.0)
        away_key_impact = game.get('away_key_position_injury_impact', 0.0)
        
        # Calculate adjustments (negative for injured team)
        home_adjustment = -(home_injury_impact + home_key_impact * 0.5) * self.config.injury_adjustment_weight
        away_adjustment = -(away_injury_impact + away_key_impact * 0.5) * self.config.injury_adjustment_weight
        
        # Cap adjustments
        max_adjustment = self.config.injury_max_delta
        home_adjustment = max(-max_adjustment, min(max_adjustment, home_adjustment))
        away_adjustment = max(-max_adjustment, min(max_adjustment, away_adjustment))
        
        return home_adjustment, away_adjustment


def run_injury_analysis(years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
    """Run comprehensive injury analysis."""
    print("🏥 RUNNING INJURY ANALYSIS")
    print("="*60)
    
    # Load games data
    games = load_games(years)
    if sample_size:
        games = games.head(sample_size)
    
    # Create injury calculator
    injury_calc = InjuryImpactCalculator()
    
    # Load injury data
    injuries = injury_calc.load_injury_data(years)
    
    # Create team injury database
    team_injury_df = injury_calc.create_team_injury_database(injuries)
    
    # Add injury data to games
    games_with_injuries = injury_calc.add_injury_data_to_games(games, team_injury_df)
    
    # Analyze injury impact
    print("\nINJURY IMPACT ANALYSIS:")
    print(f"Games with injury data: {len(games_with_injuries)}")
    print(f"Average home injury impact: {games_with_injuries['home_injury_impact'].mean():.3f}")
    print(f"Average away injury impact: {games_with_injuries['away_injury_impact'].mean():.3f}")
    print(f"Max home injury impact: {games_with_injuries['home_injury_impact'].max():.3f}")
    print(f"Max away injury impact: {games_with_injuries['away_injury_impact'].max():.3f}")
    
    # Show games with significant injuries
    significant_injuries = games_with_injuries[
        (games_with_injuries['home_injury_impact'] > 2.0) | 
        (games_with_injuries['away_injury_impact'] > 2.0)
    ]
    
    print(f"\nGames with significant injuries (>2.0 impact): {len(significant_injuries)}")
    if len(significant_injuries) > 0:
        print("\nSample significant injury games:")
        cols = ['home_team', 'away_team', 'home_injury_impact', 'away_injury_impact', 
                'home_injured_players', 'away_injured_players']
        print(significant_injuries[cols].head())
    
    return {
        'games_with_injuries': games_with_injuries,
        'team_injury_df': team_injury_df,
        'injury_analysis': {
            'total_games': len(games_with_injuries),
            'avg_home_impact': games_with_injuries['home_injury_impact'].mean(),
            'avg_away_impact': games_with_injuries['away_injury_impact'].mean(),
            'significant_injury_games': len(significant_injuries)
        }
    }


if __name__ == "__main__":
    results = run_injury_analysis(sample_size=100)
