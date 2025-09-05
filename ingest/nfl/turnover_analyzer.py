"""Turnover analysis for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class TurnoverAnalyzer:
    """Analyzes turnover data and its impact on game outcomes."""
    
    def __init__(self):
        """Initialize turnover analyzer."""
        self.turnover_data = None
        self.correlation_metrics = None
    
    def load_turnover_data(self, years: List[int]) -> pd.DataFrame:
        """
        Load turnover data for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with turnover data
        """
        import nfl_data_py as nfl
        
        print(f"Loading turnover data for years {years}...")
        
        # Load play-by-play data
        pbp = nfl.import_pbp_data(years, downcast=True)
        print(f"Loaded {len(pbp)} plays")
        
        # Calculate offensive turnovers (giveaways)
        offensive_turnovers = pbp.groupby(['posteam', 'season']).agg({
            'interception': 'sum',
            'fumble_lost': 'sum',
            'play_id': 'count'
        }).rename(columns={'play_id': 'total_plays'})
        
        offensive_turnovers['giveaways'] = offensive_turnovers['interception'] + offensive_turnovers['fumble_lost']
        offensive_turnovers['giveaway_rate'] = offensive_turnovers['giveaways'] / offensive_turnovers['total_plays']
        
        # Calculate defensive turnovers (takeaways)
        defensive_turnovers = pbp.groupby(['defteam', 'season']).agg({
            'interception': 'sum',
            'fumble_lost': 'sum',
            'play_id': 'count'
        }).rename(columns={'play_id': 'total_plays'})
        
        defensive_turnovers['takeaways'] = defensive_turnovers['interception'] + defensive_turnovers['fumble_lost']
        defensive_turnovers['takeaway_rate'] = defensive_turnovers['takeaways'] / defensive_turnovers['total_plays']
        
        # Combine offensive and defensive data
        turnover_data = pd.DataFrame()
        
        for team in offensive_turnovers.index.get_level_values('posteam').unique():
            if pd.isna(team):
                continue
                
            for season in offensive_turnovers.index.get_level_values('season').unique():
                if pd.isna(season):
                    continue
                
                # Get offensive data
                off_data = offensive_turnovers.loc[(team, season)]
                def_data = defensive_turnovers.loc[(team, season)]
                
                turnover_data = pd.concat([turnover_data, pd.DataFrame({
                    'team': team,
                    'season': season,
                    'giveaways': off_data['giveaways'],
                    'takeaways': def_data['takeaways'],
                    'turnover_differential': def_data['takeaways'] - off_data['giveaways'],
                    'giveaway_rate': off_data['giveaway_rate'],
                    'takeaway_rate': def_data['takeaway_rate'],
                    'total_plays': off_data['total_plays']
                }, index=[0])], ignore_index=True)
        
        self.turnover_data = turnover_data
        print(f"Calculated turnover data for {len(turnover_data)} team-seasons")
        
        return turnover_data
    
    def analyze_turnover_impact(self, games_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the impact of turnovers on game outcomes.
        
        Args:
            games_data: Games DataFrame with results
            
        Returns:
            Dictionary with analysis results
        """
        print("Analyzing turnover impact on game outcomes...")
        
        if self.turnover_data is None:
            raise ValueError("Turnover data not loaded. Call load_turnover_data() first.")
        
        # Merge turnover data with games
        games_with_turnovers = self._merge_turnover_data_with_games(games_data)
        
        # Calculate turnover differentials for each game
        games_with_turnovers['home_turnover_diff'] = (
            games_with_turnovers['home_takeaways'] - games_with_turnovers['home_giveaways']
        )
        games_with_turnovers['away_turnover_diff'] = (
            games_with_turnovers['away_takeaways'] - games_with_turnovers['away_giveaways']
        )
        games_with_turnovers['net_turnover_diff'] = (
            games_with_turnovers['home_turnover_diff'] - games_with_turnovers['away_turnover_diff']
        )
        
        # Analyze correlation with game outcomes
        correlation_analysis = self._analyze_turnover_correlation(games_with_turnovers)
        
        # Analyze turnover differential impact
        differential_analysis = self._analyze_turnover_differential_impact(games_with_turnovers)
        
        # Analyze team turnover performance
        team_analysis = self._analyze_team_turnover_performance()
        
        self.correlation_metrics = {
            'correlation_analysis': correlation_analysis,
            'differential_analysis': differential_analysis,
            'team_analysis': team_analysis
        }
        
        return self.correlation_metrics
    
    def _merge_turnover_data_with_games(self, games_data: pd.DataFrame) -> pd.DataFrame:
        """Merge turnover data with games data."""
        games_with_turnovers = games_data.copy()
        
        # Add turnover columns
        games_with_turnovers['home_giveaways'] = 0.0
        games_with_turnovers['home_takeaways'] = 0.0
        games_with_turnovers['away_giveaways'] = 0.0
        games_with_turnovers['away_takeaways'] = 0.0
        
        # Map turnover data to games
        for idx, game in games_with_turnovers.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            season = game['season']
            
            # Get home team turnover data
            home_turnover = self.turnover_data[
                (self.turnover_data['team'] == home_team) & 
                (self.turnover_data['season'] == season)
            ]
            if len(home_turnover) > 0:
                games_with_turnovers.at[idx, 'home_giveaways'] = home_turnover.iloc[0]['giveaways']
                games_with_turnovers.at[idx, 'home_takeaways'] = home_turnover.iloc[0]['takeaways']
            
            # Get away team turnover data
            away_turnover = self.turnover_data[
                (self.turnover_data['team'] == away_team) & 
                (self.turnover_data['season'] == season)
            ]
            if len(away_turnover) > 0:
                games_with_turnovers.at[idx, 'away_giveaways'] = away_turnover.iloc[0]['giveaways']
                games_with_turnovers.at[idx, 'away_takeaways'] = away_turnover.iloc[0]['takeaways']
        
        return games_with_turnovers
    
    def _analyze_turnover_correlation(self, games_data: pd.DataFrame) -> Dict[str, float]:
        """Analyze correlation between turnovers and game outcomes."""
        # Calculate win probability based on turnover differential
        games_data['home_won'] = (games_data['home_score'] > games_data['away_score']).astype(int)
        
        # Correlation between net turnover differential and home team winning
        turnover_correlation = games_data['net_turnover_diff'].corr(games_data['home_won'])
        
        # Analyze by turnover differential ranges
        differential_ranges = {
            'strong_advantage': games_data[games_data['net_turnover_diff'] >= 2],
            'moderate_advantage': games_data[(games_data['net_turnover_diff'] >= 1) & (games_data['net_turnover_diff'] < 2)],
            'even': games_data[games_data['net_turnover_diff'] == 0],
            'moderate_disadvantage': games_data[(games_data['net_turnover_diff'] <= -1) & (games_data['net_turnover_diff'] > -2)],
            'strong_disadvantage': games_data[games_data['net_turnover_diff'] <= -2]
        }
        
        win_rates = {}
        for range_name, range_data in differential_ranges.items():
            if len(range_data) > 0:
                win_rates[range_name] = range_data['home_won'].mean()
            else:
                win_rates[range_name] = 0.0
        
        return {
            'turnover_correlation': turnover_correlation,
            'win_rates_by_differential': win_rates,
            'total_games_analyzed': len(games_data)
        }
    
    def _analyze_turnover_differential_impact(self, games_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the impact of turnover differentials on game outcomes."""
        # Group by turnover differential
        differential_impact = games_data.groupby('net_turnover_diff').agg({
            'home_won': ['count', 'mean'],
            'home_score': 'mean',
            'away_score': 'mean'
        }).round(3)
        
        # Flatten column names
        differential_impact.columns = ['games', 'win_rate', 'avg_home_score', 'avg_away_score']
        differential_impact = differential_impact.reset_index()
        
        # Calculate expected vs actual win rates
        differential_impact['expected_win_rate'] = 0.5  # Baseline expectation
        differential_impact['win_rate_advantage'] = differential_impact['win_rate'] - differential_impact['expected_win_rate']
        
        return {
            'differential_impact': differential_impact,
            'strongest_advantage': differential_impact.loc[differential_impact['win_rate_advantage'].idxmax()],
            'strongest_disadvantage': differential_impact.loc[differential_impact['win_rate_advantage'].idxmin()]
        }
    
    def _analyze_team_turnover_performance(self) -> Dict[str, Any]:
        """Analyze team turnover performance over time."""
        if self.turnover_data is None:
            return {}
        
        # Calculate team averages
        team_avg = self.turnover_data.groupby('team').agg({
            'giveaway_rate': 'mean',
            'takeaway_rate': 'mean',
            'turnover_differential': 'mean',
            'total_plays': 'sum'
        }).round(4)
        
        # Sort by turnover differential
        team_avg = team_avg.sort_values('turnover_differential', ascending=False)
        
        # Identify best and worst teams
        best_teams = team_avg.head(10)
        worst_teams = team_avg.tail(10)
        
        return {
            'team_averages': team_avg,
            'best_turnover_teams': best_teams,
            'worst_turnover_teams': worst_teams,
            'overall_stats': {
                'avg_giveaway_rate': team_avg['giveaway_rate'].mean(),
                'avg_takeaway_rate': team_avg['takeaway_rate'].mean(),
                'avg_turnover_differential': team_avg['turnover_differential'].mean(),
                'std_turnover_differential': team_avg['turnover_differential'].std()
            }
        }
    
    def generate_turnover_report(self) -> None:
        """Generate comprehensive turnover analysis report."""
        if self.correlation_metrics is None:
            print("No analysis data available. Run analyze_turnover_impact() first.")
            return
        
        print("\\n" + "="*80)
        print("TURNOVER ANALYSIS REPORT")
        print("="*80)
        
        # Correlation analysis
        corr = self.correlation_metrics['correlation_analysis']
        print(f"\\n📊 CORRELATION ANALYSIS:")
        print(f"Turnover Differential Correlation: {corr['turnover_correlation']:.4f}")
        print(f"Games Analyzed: {corr['total_games_analyzed']}")
        
        print(f"\\nWin Rates by Turnover Differential:")
        for range_name, win_rate in corr['win_rates_by_differential'].items():
            print(f"  {range_name}: {win_rate:.3f}")
        
        # Differential analysis
        diff = self.correlation_metrics['differential_analysis']
        print(f"\\n📈 TURNOVER DIFFERENTIAL IMPACT:")
        print(f"Strongest Advantage: {diff['strongest_advantage']['net_turnover_diff']} differential, {diff['strongest_advantage']['win_rate']:.3f} win rate")
        print(f"Strongest Disadvantage: {diff['strongest_disadvantage']['net_turnover_diff']} differential, {diff['strongest_disadvantage']['win_rate']:.3f} win rate")
        
        # Team analysis
        team = self.correlation_metrics['team_analysis']
        if team:
            print(f"\\n🏈 TEAM TURNOVER PERFORMANCE:")
            print(f"Average Giveaway Rate: {team['overall_stats']['avg_giveaway_rate']:.4f}")
            print(f"Average Takeaway Rate: {team['overall_stats']['avg_takeaway_rate']:.4f}")
            print(f"Average Turnover Differential: {team['overall_stats']['avg_turnover_differential']:.2f}")
            print(f"Standard Deviation: {team['overall_stats']['std_turnover_differential']:.2f}")
            
            print(f"\\nTop 5 Turnover Teams:")
            for team_name, stats in team['best_turnover_teams'].head(5).iterrows():
                print(f"  {team_name}: {stats['turnover_differential']:.2f} differential")
            
            print(f"\\nBottom 5 Turnover Teams:")
            for team_name, stats in team['worst_turnover_teams'].tail(5).iterrows():
                print(f"  {team_name}: {stats['turnover_differential']:.2f} differential")


def test_turnover_analyzer():
    """Test the turnover analyzer."""
    print("📊 TESTING TURNOVER ANALYZER")
    print("="*80)
    
    analyzer = TurnoverAnalyzer()
    
    # Load turnover data
    turnover_data = analyzer.load_turnover_data([2024])
    print(f"\\nTurnover data loaded: {len(turnover_data)} team-seasons")
    
    # Load games data for analysis
    from ingest.nfl.data_loader import load_games
    games = load_games([2024])
    
    # Analyze turnover impact
    analysis = analyzer.analyze_turnover_impact(games)
    
    # Generate report
    analyzer.generate_turnover_report()
    
    return analyzer, analysis


if __name__ == "__main__":
    analyzer, analysis = test_turnover_analyzer()
