"""Action Network data collection system."""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from models.nfl_elo.action_network_storage import ActionNetworkStorage


class ActionNetworkCollector:
    """Collects data from Action Network APIs and stores in database."""
    
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        """
        Initialize Action Network collector.
        
        Args:
            db_path: Path to SQLite database
        """
        self.storage = ActionNetworkStorage(db_path)
        self.session = requests.Session()
        
        # Set up headers with proper user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.expert_picks_url = "https://api.actionnetwork.com/web/v1/users/experts/with_picks?includeSocialReactions=true"
        self.all_picks_url = "https://api.actionnetwork.com/web/v2/scoreboard/picks/all"
    
    def collect_expert_picks(self) -> Dict[str, Any]:
        """
        Collect expert picks data from Action Network API.
        
        Returns:
            Dictionary with collection results
        """
        self.logger.info("Starting expert picks collection...")
        
        try:
            response = self.session.get(self.expert_picks_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            profiles = data.get('profiles', [])
            
            self.logger.info(f"Retrieved {len(profiles)} expert profiles")
            
            # Process each expert profile
            processed_experts = 0
            processed_picks = 0
            
            for profile in profiles:
                try:
                    # Store expert data
                    expert_id = self.storage.store_expert(profile)
                    processed_experts += 1
                    
                    # Store performance data
                    self.storage.store_expert_performance(expert_id, profile)
                    
                    # Process picks
                    picks = profile.get('picks', [])
                    for pick in picks:
                        try:
                            self.storage.store_pick(pick, expert_id)
                            processed_picks += 1
                        except Exception as e:
                            self.logger.warning(f"Error storing pick {pick.get('id', 'Unknown')}: {e}")
                    
                    # Process other pick types if available
                    for pick_type in ['competition_picks', 'custom_picks', 'group_picks']:
                        additional_picks = profile.get(pick_type, [])
                        for pick in additional_picks:
                            try:
                                self.storage.store_pick(pick, expert_id)
                                processed_picks += 1
                            except Exception as e:
                                self.logger.warning(f"Error storing {pick_type} pick {pick.get('id', 'Unknown')}: {e}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing expert {profile.get('name', 'Unknown')}: {e}")
                    continue
            
            result = {
                'success': True,
                'experts_processed': processed_experts,
                'picks_processed': processed_picks,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Expert picks collection completed: {processed_experts} experts, {processed_picks} picks")
            return result
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching expert picks data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error in expert picks collection: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def collect_all_picks(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect all picks data from Action Network API.
        
        Args:
            date: Date in YYYYMMDD format (defaults to today)
            
        Returns:
            Dictionary with collection results
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        self.logger.info(f"Starting all picks collection for date {date}...")
        
        try:
            url = f"{self.all_picks_url}?date={date}&periods=event"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            all_games = data.get('all_games', [])
            
            self.logger.info(f"Retrieved {len(all_games)} league groups")
            
            processed_games = 0
            processed_teams = 0
            
            for league_group in all_games:
                league_name = league_group.get('league_name', 'unknown')
                games = league_group.get('games', [])
                
                self.logger.info(f"Processing {len(games)} games for {league_name}")
                
                for game in games:
                    try:
                        # Store game data
                        game_id = self.storage.store_game(game)
                        processed_games += 1
                        
                        # Process teams
                        teams = game.get('teams', [])
                        for team in teams:
                            try:
                                # Add league name to team data
                                team['league_name'] = league_name
                                self.storage.store_team(team)
                                processed_teams += 1
                            except Exception as e:
                                self.logger.warning(f"Error storing team {team.get('full_name', 'Unknown')}: {e}")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing game {game.get('id', 'Unknown')}: {e}")
                        continue
            
            result = {
                'success': True,
                'games_processed': processed_games,
                'teams_processed': processed_teams,
                'date': date,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"All picks collection completed: {processed_games} games, {processed_teams} teams")
            return result
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching all picks data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error in all picks collection: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def collect_all_data(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect all Action Network data.
        
        Args:
            date: Date in YYYYMMDD format (defaults to today)
            
        Returns:
            Dictionary with collection results
        """
        self.logger.info("Starting complete Action Network data collection...")
        
        results = {
            'expert_picks': self.collect_expert_picks(),
            'all_picks': self.collect_all_picks(date),
            'collection_timestamp': datetime.now().isoformat()
        }
        
        # Determine overall success
        results['overall_success'] = (
            results['expert_picks'].get('success', False) and 
            results['all_picks'].get('success', False)
        )
        
        self.logger.info(f"Complete data collection finished. Overall success: {results['overall_success']}")
        return results
    
    def get_nfl_experts_performance(self) -> List[Dict[str, Any]]:
        """
        Get NFL expert performance summary.
        
        Returns:
            List of expert performance data
        """
        conn = self.storage.storage.db_path
        # This would need to be implemented in the storage class
        # For now, return empty list
        return []
    
    def get_nfl_picks_summary(self) -> Dict[str, Any]:
        """
        Get NFL picks summary.
        
        Returns:
            Dictionary with NFL picks summary
        """
        try:
            nfl_picks = self.storage.get_nfl_picks(limit=1000)
            
            # Calculate summary statistics
            total_picks = len(nfl_picks)
            pending_picks = len([p for p in nfl_picks if p['result'] == 'pending'])
            winning_picks = len([p for p in nfl_picks if p['result'] == 'win'])
            losing_picks = len([p for p in nfl_picks if p['result'] == 'loss'])
            
            # Calculate average metrics
            avg_odds = sum(p['odds'] for p in nfl_picks if p['odds']) / max(len([p for p in nfl_picks if p['odds']]), 1)
            avg_units = sum(p['units'] for p in nfl_picks if p['units']) / max(len([p for p in nfl_picks if p['units']]), 1)
            
            return {
                'total_picks': total_picks,
                'pending_picks': pending_picks,
                'winning_picks': winning_picks,
                'losing_picks': losing_picks,
                'win_rate': winning_picks / max(winning_picks + losing_picks, 1) * 100,
                'avg_odds': avg_odds,
                'avg_units': avg_units,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error generating NFL picks summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def main():
    """Main function for testing data collection."""
    collector = ActionNetworkCollector()
    
    print("Starting Action Network data collection...")
    results = collector.collect_all_data()
    
    print("\nCollection Results:")
    print(f"Expert Picks: {results['expert_picks']}")
    print(f"All Picks: {results['all_picks']}")
    print(f"Overall Success: {results['overall_success']}")
    
    # Get NFL picks summary
    nfl_summary = collector.get_nfl_picks_summary()
    print(f"\nNFL Picks Summary: {nfl_summary}")


if __name__ == "__main__":
    main()
