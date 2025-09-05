"""Team mapping utilities for Action Network integration."""

import sqlite3
from typing import Dict, List, Optional, Tuple
import logging


class ActionNetworkTeamMapper:
    """Maps Action Network team IDs to existing NFL team references."""
    
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        """
        Initialize team mapper.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # NFL team mapping (Action Network ID -> Standard Name)
        self.nfl_team_mapping = {
            # This mapping will be populated from the database
        }
        
        # Load team mappings from database
        self._load_team_mappings()
    
    def _load_team_mappings(self):
        """Load team mappings from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT an_team_id, full_name, abbr, league_name
                FROM action_network_teams
                WHERE league_name = 'nfl'
            ''')
            
            for row in cursor.fetchall():
                an_id, full_name, abbr, league = row
                self.nfl_team_mapping[an_id] = {
                    'full_name': full_name,
                    'abbr': abbr,
                    'league': league
                }
            
            self.logger.info(f"Loaded {len(self.nfl_team_mapping)} NFL team mappings")
            
        except Exception as e:
            self.logger.error(f"Error loading team mappings: {e}")
        finally:
            conn.close()
    
    def get_nfl_team_by_an_id(self, an_team_id: int) -> Optional[Dict[str, str]]:
        """
        Get NFL team info by Action Network team ID.
        
        Args:
            an_team_id: Action Network team ID
            
        Returns:
            Team information or None if not found
        """
        return self.nfl_team_mapping.get(an_team_id)
    
    def get_an_id_by_team_name(self, team_name: str) -> Optional[int]:
        """
        Get Action Network team ID by team name.
        
        Args:
            team_name: Team name to search for
            
        Returns:
            Action Network team ID or None if not found
        """
        for an_id, team_info in self.nfl_team_mapping.items():
            if (team_info['full_name'].lower() == team_name.lower() or 
                team_info['abbr'].lower() == team_name.lower()):
                return an_id
        return None
    
    def map_nfl_teams_to_standard(self) -> Dict[int, str]:
        """
        Create mapping from Action Network team IDs to standard NFL team names.
        
        Returns:
            Dictionary mapping AN team ID to standard team name
        """
        # Standard NFL team names (as used in the existing system)
        standard_team_names = {
            'ARI': 'Arizona Cardinals',
            'ATL': 'Atlanta Falcons', 
            'BAL': 'Baltimore Ravens',
            'BUF': 'Buffalo Bills',
            'CAR': 'Carolina Panthers',
            'CHI': 'Chicago Bears',
            'CIN': 'Cincinnati Bengals',
            'CLE': 'Cleveland Browns',
            'DAL': 'Dallas Cowboys',
            'DEN': 'Denver Broncos',
            'DET': 'Detroit Lions',
            'GB': 'Green Bay Packers',
            'HOU': 'Houston Texans',
            'IND': 'Indianapolis Colts',
            'JAX': 'Jacksonville Jaguars',
            'KC': 'Kansas City Chiefs',
            'LV': 'Las Vegas Raiders',
            'LAC': 'Los Angeles Chargers',
            'LAR': 'Los Angeles Rams',
            'MIA': 'Miami Dolphins',
            'MIN': 'Minnesota Vikings',
            'NE': 'New England Patriots',
            'NO': 'New Orleans Saints',
            'NYG': 'New York Giants',
            'NYJ': 'New York Jets',
            'PHI': 'Philadelphia Eagles',
            'PIT': 'Pittsburgh Steelers',
            'SF': 'San Francisco 49ers',
            'SEA': 'Seattle Seahawks',
            'TB': 'Tampa Bay Buccaneers',
            'TEN': 'Tennessee Titans',
            'WAS': 'Washington Commanders'
        }
        
        mapping = {}
        for an_id, team_info in self.nfl_team_mapping.items():
            abbr = team_info['abbr']
            if abbr in standard_team_names:
                mapping[an_id] = standard_team_names[abbr]
        
        return mapping
    
    def get_nfl_games_with_teams(self) -> List[Dict[str, any]]:
        """
        Get NFL games with mapped team information.
        
        Returns:
            List of NFL games with team details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT g.an_game_id, g.season, g.start_time, g.game_status,
                       g.home_score, g.away_score, g.winning_team_id,
                       ht.full_name as home_team_name, ht.abbr as home_team_abbr,
                       at.full_name as away_team_name, at.abbr as away_team_abbr
                FROM action_network_games g
                LEFT JOIN action_network_teams ht ON g.home_team_id = ht.an_team_id
                LEFT JOIN action_network_teams at ON g.away_team_id = at.an_team_id
                WHERE g.league_name = 'nfl'
                ORDER BY g.start_time DESC
            ''')
            
            columns = [desc[0] for desc in cursor.description]
            games = []
            for row in cursor.fetchall():
                game = dict(zip(columns, row))
                games.append(game)
            
            return games
            
        except Exception as e:
            self.logger.error(f"Error fetching NFL games: {e}")
            return []
        finally:
            conn.close()
    
    def get_nfl_picks_with_team_info(self, limit: int = 100) -> List[Dict[str, any]]:
        """
        Get NFL picks with team information.
        
        Args:
            limit: Maximum number of picks to return
            
        Returns:
            List of NFL picks with team details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.an_pick_id, e.name as expert_name, p.play_description,
                       p.value, p.odds, p.units, p.units_net, p.result,
                       p.created_at, p.trend, p.social_likes, p.social_copies,
                       g.an_game_id, g.start_time, g.game_status,
                       ht.full_name as home_team_name, ht.abbr as home_team_abbr,
                       at.full_name as away_team_name, at.abbr as away_team_abbr
                FROM action_network_picks p
                JOIN action_network_experts e ON p.expert_id = e.id
                LEFT JOIN action_network_games g ON p.game_id = g.an_game_id
                LEFT JOIN action_network_teams ht ON g.home_team_id = ht.an_team_id
                LEFT JOIN action_network_teams at ON g.away_team_id = at.an_team_id
                WHERE p.league_name = 'nfl'
                ORDER BY p.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            picks = []
            for row in cursor.fetchall():
                pick = dict(zip(columns, row))
                picks.append(pick)
            
            return picks
            
        except Exception as e:
            self.logger.error(f"Error fetching NFL picks with team info: {e}")
            return []
        finally:
            conn.close()
    
    def get_expert_nfl_performance(self, expert_name: str) -> Dict[str, any]:
        """
        Get NFL-specific performance for an expert.
        
        Args:
            expert_name: Name of the expert
            
        Returns:
            Expert NFL performance summary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get expert ID
            cursor.execute('''
                SELECT id FROM action_network_experts WHERE name = ?
            ''', (expert_name,))
            expert_result = cursor.fetchone()
            
            if not expert_result:
                return {'error': 'Expert not found'}
            
            expert_id = expert_result[0]
            
            # Get NFL picks for this expert
            cursor.execute('''
                SELECT result, units_net, odds, units, created_at
                FROM action_network_picks
                WHERE expert_id = ? AND league_name = 'nfl'
                ORDER BY created_at DESC
            ''', (expert_id,))
            
            picks = cursor.fetchall()
            
            if not picks:
                return {'error': 'No NFL picks found for this expert'}
            
            # Calculate performance metrics
            total_picks = len(picks)
            winning_picks = len([p for p in picks if p[0] == 'win'])
            losing_picks = len([p for p in picks if p[0] == 'loss'])
            pending_picks = len([p for p in picks if p[0] == 'pending'])
            
            total_units_net = sum(p[1] for p in picks if p[1] is not None)
            avg_odds = sum(p[2] for p in picks if p[2] is not None) / max(len([p for p in picks if p[2] is not None]), 1)
            avg_units = sum(p[3] for p in picks if p[3] is not None) / max(len([p for p in picks if p[3] is not None]), 1)
            
            win_rate = (winning_picks / max(winning_picks + losing_picks, 1)) * 100
            
            return {
                'expert_name': expert_name,
                'total_picks': total_picks,
                'winning_picks': winning_picks,
                'losing_picks': losing_picks,
                'pending_picks': pending_picks,
                'win_rate': win_rate,
                'total_units_net': total_units_net,
                'avg_odds': avg_odds,
                'avg_units': avg_units
            }
            
        except Exception as e:
            self.logger.error(f"Error getting expert NFL performance: {e}")
            return {'error': str(e)}
        finally:
            conn.close()


def main():
    """Test the team mapper functionality."""
    mapper = ActionNetworkTeamMapper()
    
    print("NFL Team Mappings:")
    nfl_mapping = mapper.map_nfl_teams_to_standard()
    for an_id, team_name in nfl_mapping.items():
        print(f"  AN ID {an_id}: {team_name}")
    
    print(f"\nTotal NFL teams mapped: {len(nfl_mapping)}")
    
    print("\nNFL Games:")
    games = mapper.get_nfl_games_with_teams()
    for game in games[:5]:  # Show first 5 games
        print(f"  {game['away_team_name']} @ {game['home_team_name']} - {game['game_status']}")
    
    print(f"\nTotal NFL games: {len(games)}")
    
    print("\nNFL Picks with Team Info:")
    picks = mapper.get_nfl_picks_with_team_info(limit=5)
    for pick in picks:
        print(f"  {pick['expert_name']}: {pick['play_description']} - {pick['result']}")


if __name__ == "__main__":
    main()
