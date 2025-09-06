#!/usr/bin/env python3
"""
Migrate Data to Unified Database
Migrates data from existing databases to the unified multi-sport database
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedDataMigrator:
    """Migrates data from existing databases to unified database."""
    
    def __init__(self, 
                 unified_db_path: str = "sportsedge_unified.db",
                 nfl_elo_db_path: str = "nfl_elo.db",
                 stats_db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        self.unified_db_path = unified_db_path
        self.nfl_elo_db_path = nfl_elo_db_path
        self.stats_db_path = stats_db_path
        
        # Verify databases exist
        if not Path(unified_db_path).exists():
            raise FileNotFoundError(f"Unified database not found: {unified_db_path}")
        if not Path(nfl_elo_db_path).exists():
            raise FileNotFoundError(f"NFL ELO database not found: {nfl_elo_db_path}")
        if not Path(stats_db_path).exists():
            raise FileNotFoundError(f"Stats database not found: {stats_db_path}")
    
    def migrate_all_data(self) -> Dict[str, Any]:
        """Migrate all data from existing databases."""
        results = {
            'teams_migrated': 0,
            'games_migrated': 0,
            'experts_migrated': 0,
            'picks_migrated': 0,
            'ratings_migrated': 0,
            'predictions_migrated': 0,
            'errors': []
        }
        
        try:
            # Get NFL sport and league IDs
            nfl_sport_id, nfl_league_id = self._get_nfl_ids()
            results['nfl_sport_id'] = nfl_sport_id
            results['nfl_league_id'] = nfl_league_id
            
            # Migrate teams
            results['teams_migrated'] = self._migrate_teams(nfl_sport_id, nfl_league_id)
            
            # Migrate games
            results['games_migrated'] = self._migrate_games(nfl_sport_id, nfl_league_id)
            
            # Migrate experts and picks
            results['experts_migrated'] = self._migrate_experts()
            results['picks_migrated'] = self._migrate_expert_picks(nfl_sport_id)
            
            # Migrate ratings
            results['ratings_migrated'] = self._migrate_team_ratings(nfl_sport_id)
            
            # Migrate predictions
            results['predictions_migrated'] = self._migrate_predictions(nfl_sport_id)
            
            logger.info("Data migration completed successfully!")
            
        except Exception as e:
            error_msg = f"Migration failed: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def _get_nfl_ids(self) -> Tuple[int, int]:
        """Get NFL sport and league IDs from unified database."""
        conn = sqlite3.connect(self.unified_db_path)
        cursor = conn.cursor()
        
        try:
            # Get NFL sport ID
            cursor.execute("SELECT id FROM sports WHERE sport_code = 'nfl'")
            nfl_sport_id = cursor.fetchone()[0]
            
            # Get NFL league ID
            cursor.execute("SELECT id FROM leagues WHERE league_code = 'nfl' AND conference IS NULL")
            nfl_league_id = cursor.fetchone()[0]
            
            return nfl_sport_id, nfl_league_id
            
        finally:
            conn.close()
    
    def _migrate_teams(self, nfl_sport_id: int, nfl_league_id: int) -> int:
        """Migrate NFL teams data."""
        logger.info("Migrating NFL teams...")
        
        # Get teams from stats database
        stats_conn = sqlite3.connect(self.stats_db_path)
        teams_df = pd.read_sql_query("SELECT * FROM nfl_teams_2025", stats_conn)
        stats_conn.close()
        
        if teams_df.empty:
            logger.warning("No teams found in stats database")
            return 0
        
        # Prepare team data for unified database
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            teams_migrated = 0
            for _, team in teams_df.iterrows():
                # Map team data to unified schema
                team_data = {
                    'sport_id': nfl_sport_id,
                    'league_id': nfl_league_id,
                    'team_code': team.get('abbr', ''),
                    'team_name': team.get('team_name', ''),
                    'city': team.get('team_name', '').split()[0] if team.get('team_name') else '',
                    'mascot': team.get('team_nick', ''),
                    'abbreviation': team.get('abbr', ''),
                    'conference': team.get('team_conf', ''),
                    'division': team.get('team_division', ''),
                    'active': True
                }
                
                cursor.execute('''
                    INSERT OR IGNORE INTO teams 
                    (sport_id, league_id, team_code, team_name, city, mascot, abbreviation, 
                     conference, division, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    team_data['sport_id'], team_data['league_id'], team_data['team_code'],
                    team_data['team_name'], team_data['city'], team_data['mascot'],
                    team_data['abbreviation'], team_data['conference'], team_data['division'],
                    team_data['active']
                ))
                
                if cursor.rowcount > 0:
                    teams_migrated += 1
            
            unified_conn.commit()
            logger.info(f"Migrated {teams_migrated} teams")
            return teams_migrated
            
        finally:
            unified_conn.close()
    
    def _migrate_games(self, nfl_sport_id: int, nfl_league_id: int) -> int:
        """Migrate games data from both databases."""
        logger.info("Migrating games...")
        
        # Get season ID for 2025
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        cursor.execute("SELECT id FROM seasons WHERE sport_id = ? AND season_year = 2025", (nfl_sport_id,))
        season_2025_id = cursor.fetchone()[0]
        unified_conn.close()
        
        # Get games from stats database
        stats_conn = sqlite3.connect(self.stats_db_path)
        games_df = pd.read_sql_query("SELECT * FROM nfl_games_2025", stats_conn)
        stats_conn.close()
        
        if games_df.empty:
            logger.warning("No games found in stats database")
            return 0
        
        # Get team mappings
        team_mappings = self._get_team_mappings()
        
        # Migrate games
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            games_migrated = 0
            for _, game in games_df.iterrows():
                # Map team names to team IDs
                home_team_id = team_mappings.get(game.get('home_team', ''))
                away_team_id = team_mappings.get(game.get('away_team', ''))
                
                if not home_team_id or not away_team_id:
                    logger.warning(f"Could not find team IDs for game: {game.get('home_team')} vs {game.get('away_team')}")
                    continue
                
                # Determine game status
                game_status = 'scheduled'
                if pd.notna(game.get('home_score')) and pd.notna(game.get('away_score')):
                    game_status = 'final'
                
                # Map game data
                game_data = {
                    'sport_id': nfl_sport_id,
                    'season_id': season_2025_id,
                    'league_id': nfl_league_id,
                    'external_game_id': str(game.get('game_id', '')),
                    'game_type': 'regular',
                    'week': int(game.get('week', 0)),
                    'home_team_id': home_team_id,
                    'away_team_id': away_team_id,
                    'game_date': game.get('gameday'),
                    'home_score': game.get('home_score'),
                    'away_score': game.get('away_score'),
                    'home_win': game.get('result') == 1 if pd.notna(game.get('result')) else None,
                    'game_status': game_status,
                    'home_rest_days': int(game.get('home_rest', 7)),
                    'away_rest_days': int(game.get('away_rest', 7)),
                    'completed': game_status == 'final'
                }
                
                cursor.execute('''
                    INSERT OR IGNORE INTO games 
                    (sport_id, season_id, league_id, external_game_id, game_type, week,
                     home_team_id, away_team_id, game_date, home_score, away_score,
                     home_win, game_status, home_rest_days, away_rest_days, completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game_data['sport_id'], game_data['season_id'], game_data['league_id'],
                    game_data['external_game_id'], game_data['game_type'], game_data['week'],
                    game_data['home_team_id'], game_data['away_team_id'], game_data['game_date'],
                    game_data['home_score'], game_data['away_score'], game_data['home_win'],
                    game_data['game_status'], game_data['home_rest_days'], game_data['away_rest_days'],
                    game_data['completed']
                ))
                
                if cursor.rowcount > 0:
                    games_migrated += 1
            
            unified_conn.commit()
            logger.info(f"Migrated {games_migrated} games")
            return games_migrated
            
        finally:
            unified_conn.close()
    
    def _migrate_experts(self) -> int:
        """Migrate Action Network experts."""
        logger.info("Migrating experts...")
        
        # Get experts from stats database
        stats_conn = sqlite3.connect(self.stats_db_path)
        experts_df = pd.read_sql_query("SELECT * FROM action_network_experts", stats_conn)
        stats_conn.close()
        
        if experts_df.empty:
            logger.warning("No experts found in stats database")
            return 0
        
        # Migrate experts
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            experts_migrated = 0
            for _, expert in experts_df.iterrows():
                cursor.execute('''
                    INSERT OR IGNORE INTO experts 
                    (external_expert_id, name, username, is_verified, followers)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    str(expert.get('an_expert_id', '')),
                    expert.get('name', ''),
                    expert.get('username', ''),
                    expert.get('is_verified', False),
                    expert.get('followers', 0)
                ))
                
                if cursor.rowcount > 0:
                    experts_migrated += 1
            
            unified_conn.commit()
            logger.info(f"Migrated {experts_migrated} experts")
            return experts_migrated
            
        finally:
            unified_conn.close()
    
    def _migrate_expert_picks(self, nfl_sport_id: int) -> int:
        """Migrate expert picks."""
        logger.info("Migrating expert picks...")
        
        # Get picks from stats database
        stats_conn = sqlite3.connect(self.stats_db_path)
        picks_df = pd.read_sql_query("SELECT * FROM action_network_picks", stats_conn)
        stats_conn.close()
        
        if picks_df.empty:
            logger.warning("No picks found in stats database")
            return 0
        
        # Get expert and game mappings
        expert_mappings = self._get_expert_mappings()
        game_mappings = self._get_game_mappings()
        
        # Migrate picks
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            picks_migrated = 0
            for _, pick in picks_df.iterrows():
                # Map expert ID
                expert_id = expert_mappings.get(pick.get('expert_id'))
                if not expert_id:
                    continue
                
                # Map game ID (if available)
                game_id = None
                if pick.get('game_id'):
                    game_id = game_mappings.get(pick.get('game_id'))
                
                cursor.execute('''
                    INSERT OR IGNORE INTO expert_picks 
                    (external_pick_id, expert_id, game_id, sport_id, pick_type, 
                     play_description, value, odds, units, units_net, money, money_net,
                     result, pick_created_at, starts_at, ends_at, settled_at, trend,
                     social_likes, social_copies, verified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(pick.get('an_pick_id', '')),
                    expert_id,
                    game_id,
                    nfl_sport_id,
                    pick.get('pick_type', ''),
                    pick.get('play_description', ''),
                    pick.get('value'),
                    pick.get('odds'),
                    pick.get('units'),
                    pick.get('units_net'),
                    pick.get('money'),
                    pick.get('money_net'),
                    pick.get('result', 'pending'),
                    pick.get('created_at'),
                    pick.get('starts_at'),
                    pick.get('ends_at'),
                    pick.get('settled_at'),
                    pick.get('trend'),
                    pick.get('social_likes', 0),
                    pick.get('social_copies', 0),
                    pick.get('verified', False)
                ))
                
                if cursor.rowcount > 0:
                    picks_migrated += 1
            
            unified_conn.commit()
            logger.info(f"Migrated {picks_migrated} picks")
            return picks_migrated
            
        finally:
            unified_conn.close()
    
    def _migrate_team_ratings(self, nfl_sport_id: int) -> int:
        """Migrate team ratings from both databases."""
        logger.info("Migrating team ratings...")
        
        # Get team mappings
        team_mappings = self._get_team_mappings()
        
        # Get season ID for 2025
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        cursor.execute("SELECT id FROM seasons WHERE sport_id = ? AND season_year = 2025", (nfl_sport_id,))
        season_2025_id = cursor.fetchone()[0]
        unified_conn.close()
        
        # Get ratings from stats database
        stats_conn = sqlite3.connect(self.stats_db_path)
        ratings_df = pd.read_sql_query("SELECT * FROM team_ratings", stats_conn)
        stats_conn.close()
        
        if ratings_df.empty:
            logger.warning("No ratings found in stats database")
            return 0
        
        # Migrate ratings
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            ratings_migrated = 0
            for _, rating in ratings_df.iterrows():
                # Map team name to team ID
                team_id = team_mappings.get(rating.get('team', ''))
                if not team_id:
                    continue
                
                cursor.execute('''
                    INSERT OR IGNORE INTO team_ratings 
                    (team_id, sport_id, season_id, week, rating, rating_change,
                     wins, losses, win_percentage, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    team_id,
                    nfl_sport_id,
                    season_2025_id,
                    rating.get('week'),
                    rating.get('rating'),
                    rating.get('rating_change', 0.0),
                    rating.get('wins', 0),
                    rating.get('losses', 0),
                    rating.get('win_pct', 0.0),
                    rating.get('created_at')
                ))
                
                if cursor.rowcount > 0:
                    ratings_migrated += 1
            
            unified_conn.commit()
            logger.info(f"Migrated {ratings_migrated} ratings")
            return ratings_migrated
            
        finally:
            unified_conn.close()
    
    def _migrate_predictions(self, nfl_sport_id: int) -> int:
        """Migrate predictions from main database."""
        logger.info("Migrating predictions...")
        
        # Get predictions from main database
        main_conn = sqlite3.connect(self.nfl_elo_db_path)
        predictions_df = pd.read_sql_query("SELECT * FROM predictions", main_conn)
        main_conn.close()
        
        if predictions_df.empty:
            logger.warning("No predictions found in main database")
            return 0
        
        # Get team and game mappings
        team_mappings = self._get_team_mappings()
        game_mappings = self._get_game_mappings()
        
        # Migrate predictions
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            predictions_migrated = 0
            for _, pred in predictions_df.iterrows():
                # Map team names to team IDs
                home_team_id = team_mappings.get(pred.get('home_team', ''))
                away_team_id = team_mappings.get(pred.get('away_team', ''))
                predicted_winner_id = team_mappings.get(pred.get('predicted_winner', ''))
                
                if not home_team_id or not away_team_id:
                    continue
                
                # Find corresponding game
                game_id = None
                for game_mapping in game_mappings.values():
                    if (game_mapping['home_team'] == pred.get('home_team') and 
                        game_mapping['away_team'] == pred.get('away_team')):
                        game_id = game_mapping['game_id']
                        break
                
                cursor.execute('''
                    INSERT OR IGNORE INTO predictions 
                    (game_id, sport_id, prediction_type, home_team_id, away_team_id,
                     home_rating, away_rating, home_win_prob, away_win_prob,
                     predicted_winner_id, confidence, predicted_home_score,
                     predicted_away_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game_id,
                    nfl_sport_id,
                    'elo',
                    home_team_id,
                    away_team_id,
                    pred.get('home_rating'),
                    pred.get('away_rating'),
                    pred.get('home_win_prob'),
                    pred.get('away_win_prob'),
                    predicted_winner_id,
                    pred.get('confidence'),
                    pred.get('predicted_home_score'),
                    pred.get('predicted_away_score'),
                    pred.get('created_at')
                ))
                
                if cursor.rowcount > 0:
                    predictions_migrated += 1
            
            unified_conn.commit()
            logger.info(f"Migrated {predictions_migrated} predictions")
            return predictions_migrated
            
        finally:
            unified_conn.close()
    
    def _get_team_mappings(self) -> Dict[str, int]:
        """Get team name to team ID mappings."""
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            cursor.execute("SELECT team_code, team_name, id FROM teams WHERE sport_id = 1")
            teams = cursor.fetchall()
            
            mappings = {}
            for team_code, team_name, team_id in teams:
                mappings[team_code] = team_id
                mappings[team_name] = team_id
            
            return mappings
            
        finally:
            unified_conn.close()
    
    def _get_expert_mappings(self) -> Dict[int, int]:
        """Get old expert ID to new expert ID mappings."""
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            cursor.execute("SELECT external_expert_id, id FROM experts")
            experts = cursor.fetchall()
            
            mappings = {}
            for external_id, new_id in experts:
                mappings[int(external_id)] = new_id
            
            return mappings
            
        finally:
            unified_conn.close()
    
    def _get_game_mappings(self) -> Dict[int, Dict[str, Any]]:
        """Get game mappings for predictions."""
        unified_conn = sqlite3.connect(self.unified_db_path)
        cursor = unified_conn.cursor()
        
        try:
            cursor.execute('''
                SELECT g.id, ht.team_code as home_team, at.team_code as away_team
                FROM games g
                JOIN teams ht ON g.home_team_id = ht.id
                JOIN teams at ON g.away_team_id = at.id
            ''')
            games = cursor.fetchall()
            
            mappings = {}
            for game_id, home_team, away_team in games:
                mappings[game_id] = {
                    'game_id': game_id,
                    'home_team': home_team,
                    'away_team': away_team
                }
            
            return mappings
            
        finally:
            unified_conn.close()

def main():
    """Main function to run migration."""
    migrator = UnifiedDataMigrator()
    results = migrator.migrate_all_data()
    
    print("🔄 Migration Results:")
    for key, value in results.items():
        if key != 'errors':
            print(f"  {key}: {value}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    main()
