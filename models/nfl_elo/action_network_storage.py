"""Action Network data storage system for tracking expert picks and performance."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging

from .config import EloConfig


class ActionNetworkStorage:
    """Storage system for Action Network expert picks and performance data."""
    
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        """
        Initialize Action Network storage system.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database tables
        self._init_database()
    
    def _init_database(self):
        """Initialize Action Network tables in the existing database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create Action Network experts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_network_experts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    an_expert_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    username TEXT,
                    is_verified BOOLEAN,
                    followers INTEGER,
                    bio TEXT,
                    picture_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create expert performance tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_network_expert_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expert_id INTEGER,
                    window_period TEXT,
                    wins INTEGER,
                    losses INTEGER,
                    pushes INTEGER,
                    total_picks INTEGER,
                    units_net REAL,
                    roi REAL,
                    win_streak_type TEXT,
                    win_streak_value INTEGER,
                    win_streak_start_date TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (expert_id) REFERENCES action_network_experts(id)
                )
            ''')
            
            # Create picks tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_network_picks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    an_pick_id INTEGER UNIQUE NOT NULL,
                    expert_id INTEGER,
                    game_id INTEGER,
                    league_name TEXT,
                    pick_type TEXT,
                    play_description TEXT,
                    value REAL,
                    odds INTEGER,
                    units REAL,
                    units_net REAL,
                    money REAL,
                    money_net REAL,
                    result TEXT,
                    created_at TIMESTAMP,
                    starts_at TIMESTAMP,
                    ends_at TIMESTAMP,
                    settled_at TIMESTAMP,
                    player_id INTEGER,
                    trend TEXT,
                    social_likes INTEGER DEFAULT 0,
                    social_copies INTEGER DEFAULT 0,
                    custom_pick_type TEXT,
                    custom_pick_name TEXT,
                    verified BOOLEAN,
                    FOREIGN KEY (expert_id) REFERENCES action_network_experts(id)
                )
            ''')
            
            # Create games tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_network_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    an_game_id INTEGER UNIQUE NOT NULL,
                    league_name TEXT,
                    season INTEGER,
                    home_team_id INTEGER,
                    away_team_id INTEGER,
                    winning_team_id INTEGER,
                    game_status TEXT,
                    real_status TEXT,
                    status_display TEXT,
                    start_time TIMESTAMP,
                    attendance INTEGER,
                    home_score INTEGER,
                    away_score INTEGER,
                    is_free BOOLEAN,
                    trending BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create team mapping table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_network_teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    an_team_id INTEGER UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    display_name TEXT,
                    short_name TEXT,
                    location TEXT,
                    abbr TEXT,
                    league_name TEXT,
                    conference_type TEXT,
                    division_type TEXT,
                    url_slug TEXT,
                    logo_url TEXT,
                    primary_color TEXT,
                    secondary_color TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_picks_expert_id ON action_network_picks(expert_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_picks_game_id ON action_network_picks(game_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_picks_league ON action_network_picks(league_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_picks_result ON action_network_picks(result)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_picks_created_at ON action_network_picks(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_games_league ON action_network_games(league_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_games_season ON action_network_games(season)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_an_experts_an_id ON action_network_experts(an_expert_id)')
            
            conn.commit()
            self.logger.info("Action Network database tables initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing Action Network database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def store_expert(self, expert_data: Dict[str, Any]) -> int:
        """
        Store or update expert data.
        
        Args:
            expert_data: Expert profile data from Action Network API
            
        Returns:
            Expert ID in local database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if expert already exists
            cursor.execute(
                'SELECT id FROM action_network_experts WHERE an_expert_id = ?',
                (expert_data['id'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing expert
                cursor.execute('''
                    UPDATE action_network_experts 
                    SET name = ?, username = ?, is_verified = ?, followers = ?, 
                        bio = ?, picture_url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE an_expert_id = ?
                ''', (
                    expert_data['name'],
                    expert_data.get('username'),
                    expert_data.get('is_verified', False),
                    expert_data.get('followers', 0),
                    expert_data.get('bio'),
                    expert_data.get('picture_url'),
                    expert_data['id']
                ))
                expert_id = existing[0]
            else:
                # Insert new expert
                cursor.execute('''
                    INSERT INTO action_network_experts 
                    (an_expert_id, name, username, is_verified, followers, bio, picture_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    expert_data['id'],
                    expert_data['name'],
                    expert_data.get('username'),
                    expert_data.get('is_verified', False),
                    expert_data.get('followers', 0),
                    expert_data.get('bio'),
                    expert_data.get('picture_url')
                ))
                expert_id = cursor.lastrowid
            
            conn.commit()
            return expert_id
            
        except Exception as e:
            self.logger.error(f"Error storing expert {expert_data.get('name', 'Unknown')}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def store_expert_performance(self, expert_id: int, performance_data: Dict[str, Any]) -> None:
        """
        Store expert performance data.
        
        Args:
            expert_id: Local expert ID
            performance_data: Performance metrics from Action Network API
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Store record data
            if 'record' in performance_data:
                record = performance_data['record']
                cursor.execute('''
                    INSERT INTO action_network_expert_performance 
                    (expert_id, window_period, wins, losses, pushes, total_picks, 
                     units_net, roi, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    expert_id,
                    record.get('window', 'unknown'),
                    record.get('win', 0),
                    record.get('loss', 0),
                    record.get('push', 0),
                    record.get('count', 0),
                    record.get('units_net', 0.0),
                    record.get('roi', 0.0)
                ))
            
            # Store win streak data
            if 'win_streak' in performance_data:
                streak = performance_data['win_streak']
                cursor.execute('''
                    UPDATE action_network_expert_performance 
                    SET win_streak_type = ?, win_streak_value = ?, win_streak_start_date = ?
                    WHERE expert_id = ? AND recorded_at = (
                        SELECT MAX(recorded_at) FROM action_network_expert_performance 
                        WHERE expert_id = ?
                    )
                ''', (
                    streak.get('type'),
                    streak.get('value'),
                    streak.get('startDate'),
                    expert_id,
                    expert_id
                ))
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error storing expert performance: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def store_pick(self, pick_data: Dict[str, Any], expert_id: int) -> int:
        """
        Store pick data.
        
        Args:
            pick_data: Pick data from Action Network API
            expert_id: Local expert ID
            
        Returns:
            Pick ID in local database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if pick already exists
            cursor.execute(
                'SELECT id FROM action_network_picks WHERE an_pick_id = ?',
                (pick_data['id'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing pick
                cursor.execute('''
                    UPDATE action_network_picks 
                    SET result = ?, units_net = ?, money_net = ?, settled_at = ?,
                        social_likes = ?, social_copies = ?, trend = ?
                    WHERE an_pick_id = ?
                ''', (
                    pick_data.get('result'),
                    pick_data.get('units_net'),
                    pick_data.get('money_net'),
                    pick_data.get('settled_at'),
                    len(pick_data.get('reactions', {}).get('like', [])),
                    pick_data.get('number_of_copies', 0),
                    pick_data.get('trend'),
                    pick_data['id']
                ))
                pick_id = existing[0]
            else:
                # Insert new pick
                cursor.execute('''
                    INSERT INTO action_network_picks 
                    (an_pick_id, expert_id, game_id, league_name, pick_type, play_description,
                     value, odds, units, units_net, money, money_net, result, created_at,
                     starts_at, ends_at, settled_at, player_id, trend, social_likes,
                     social_copies, custom_pick_type, custom_pick_name, verified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pick_data['id'],
                    expert_id,
                    pick_data.get('game_id'),
                    pick_data.get('league_name'),
                    pick_data.get('type'),
                    pick_data.get('play'),
                    pick_data.get('value'),
                    pick_data.get('odds'),
                    pick_data.get('units'),
                    pick_data.get('units_net'),
                    pick_data.get('money'),
                    pick_data.get('money_net'),
                    pick_data.get('result'),
                    pick_data.get('created_at'),
                    pick_data.get('starts_at'),
                    pick_data.get('ends_at'),
                    pick_data.get('settled_at'),
                    pick_data.get('player_id'),
                    pick_data.get('trend'),
                    len(pick_data.get('reactions', {}).get('like', [])),
                    pick_data.get('number_of_copies', 0),
                    pick_data.get('custom_pick_type'),
                    pick_data.get('custom_pick_name'),
                    pick_data.get('verified', False)
                ))
                pick_id = cursor.lastrowid
            
            conn.commit()
            return pick_id
            
        except Exception as e:
            self.logger.error(f"Error storing pick {pick_data.get('id', 'Unknown')}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def store_game(self, game_data: Dict[str, Any]) -> int:
        """
        Store game data.
        
        Args:
            game_data: Game data from Action Network API
            
        Returns:
            Game ID in local database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if game already exists
            cursor.execute(
                'SELECT id FROM action_network_games WHERE an_game_id = ?',
                (game_data['id'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing game
                cursor.execute('''
                    UPDATE action_network_games 
                    SET game_status = ?, real_status = ?, status_display = ?,
                        home_score = ?, away_score = ?, winning_team_id = ?
                    WHERE an_game_id = ?
                ''', (
                    game_data.get('status'),
                    game_data.get('real_status'),
                    game_data.get('status_display'),
                    game_data.get('boxscore', {}).get('total_home_points'),
                    game_data.get('boxscore', {}).get('total_away_points'),
                    game_data.get('winning_team_id'),
                    game_data['id']
                ))
                game_id = existing[0]
            else:
                # Insert new game
                cursor.execute('''
                    INSERT INTO action_network_games 
                    (an_game_id, league_name, season, home_team_id, away_team_id,
                     winning_team_id, game_status, real_status, status_display,
                     start_time, attendance, home_score, away_score, is_free, trending)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game_data['id'],
                    game_data.get('league_name'),
                    game_data.get('season'),
                    game_data.get('home_team_id'),
                    game_data.get('away_team_id'),
                    game_data.get('winning_team_id'),
                    game_data.get('status'),
                    game_data.get('real_status'),
                    game_data.get('status_display'),
                    game_data.get('start_time'),
                    game_data.get('attendance'),
                    game_data.get('boxscore', {}).get('total_home_points'),
                    game_data.get('boxscore', {}).get('total_away_points'),
                    game_data.get('is_free', False),
                    game_data.get('trending', False)
                ))
                game_id = cursor.lastrowid
            
            conn.commit()
            return game_id
            
        except Exception as e:
            self.logger.error(f"Error storing game {game_data.get('id', 'Unknown')}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def store_team(self, team_data: Dict[str, Any]) -> int:
        """
        Store team data.
        
        Args:
            team_data: Team data from Action Network API
            
        Returns:
            Team ID in local database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if team already exists
            cursor.execute(
                'SELECT id FROM action_network_teams WHERE an_team_id = ?',
                (team_data['id'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            else:
                # Insert new team
                cursor.execute('''
                    INSERT INTO action_network_teams 
                    (an_team_id, full_name, display_name, short_name, location, abbr,
                     league_name, conference_type, division_type, url_slug, logo_url,
                     primary_color, secondary_color)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    team_data['id'],
                    team_data.get('full_name'),
                    team_data.get('display_name'),
                    team_data.get('short_name'),
                    team_data.get('location'),
                    team_data.get('abbr'),
                    team_data.get('league_name'),
                    team_data.get('conference_type'),
                    team_data.get('division_type'),
                    team_data.get('url_slug'),
                    team_data.get('logo'),
                    team_data.get('primary_color'),
                    team_data.get('secondary_color')
                ))
                team_id = cursor.lastrowid
                conn.commit()
                return team_id
                
        except Exception as e:
            self.logger.error(f"Error storing team {team_data.get('full_name', 'Unknown')}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_expert_by_an_id(self, an_expert_id: int) -> Optional[int]:
        """
        Get local expert ID by Action Network expert ID.
        
        Args:
            an_expert_id: Action Network expert ID
            
        Returns:
            Local expert ID or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id FROM action_network_experts WHERE an_expert_id = ?',
                (an_expert_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()
    
    def get_expert_performance_summary(self, expert_id: int) -> Optional[Dict[str, Any]]:
        """
        Get latest performance summary for an expert.
        
        Args:
            expert_id: Local expert ID
            
        Returns:
            Performance summary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT window_period, wins, losses, pushes, total_picks, units_net, roi,
                       win_streak_type, win_streak_value, win_streak_start_date
                FROM action_network_expert_performance 
                WHERE expert_id = ? 
                ORDER BY recorded_at DESC 
                LIMIT 1
            ''', (expert_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'window_period': result[0],
                    'wins': result[1],
                    'losses': result[2],
                    'pushes': result[3],
                    'total_picks': result[4],
                    'units_net': result[5],
                    'roi': result[6],
                    'win_streak_type': result[7],
                    'win_streak_value': result[8],
                    'win_streak_start_date': result[9]
                }
            return None
        finally:
            conn.close()
    
    def get_picks_by_expert(self, expert_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get picks for a specific expert.
        
        Args:
            expert_id: Local expert ID
            limit: Maximum number of picks to return
            
        Returns:
            List of pick data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT an_pick_id, league_name, play_description, value, odds, units,
                       units_net, result, created_at, starts_at, ends_at, trend,
                       social_likes, social_copies
                FROM action_network_picks 
                WHERE expert_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (expert_id, limit))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        finally:
            conn.close()
    
    def get_nfl_picks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get NFL picks across all experts.
        
        Args:
            limit: Maximum number of picks to return
            
        Returns:
            List of NFL pick data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.an_pick_id, e.name as expert_name, p.play_description, 
                       p.value, p.odds, p.units, p.units_net, p.result, 
                       p.created_at, p.trend, p.social_likes, p.social_copies
                FROM action_network_picks p
                JOIN action_network_experts e ON p.expert_id = e.id
                WHERE p.league_name = 'nfl'
                ORDER BY p.created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        finally:
            conn.close()
