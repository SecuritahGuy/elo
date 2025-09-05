"""Stats storage system for tracking NFL Elo performance metrics."""

import pandas as pd
import numpy as np
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging

from .config import EloConfig


class StatsStorage:
    """Storage system for NFL Elo performance metrics and results."""
    
    def __init__(self, storage_dir: str = "artifacts/stats"):
        """
        Initialize stats storage system.
        
        Args:
            storage_dir: Directory to store stats data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Database file
        self.db_path = self.storage_dir / "nfl_elo_stats.db"
        
        # Initialize database
        self._init_database()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _init_database(self):
        """Initialize SQLite database for stats storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                config_name TEXT NOT NULL,
                years TEXT NOT NULL,
                sample_size INTEGER,
                brier_score REAL,
                log_loss REAL,
                accuracy REAL,
                mae REAL,
                calibration REAL,
                ece REAL,
                sharpness REAL,
                total_games INTEGER,
                environmental_impact REAL,
                config_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                team TEXT NOT NULL,
                config_name TEXT NOT NULL,
                season INTEGER,
                total_games INTEGER,
                brier_score REAL,
                accuracy REAL,
                environmental_impact REAL,
                improvement_pct REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS environmental_impacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                config_name TEXT NOT NULL,
                weather_impact REAL,
                travel_impact REAL,
                qb_impact REAL,
                epa_impact REAL,
                total_impact REAL,
                avg_impact_per_game REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weight_optimization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                optimization_type TEXT NOT NULL,
                best_brier_score REAL,
                best_params TEXT,
                total_combinations INTEGER,
                optimization_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_backtest_result(self, 
                            config_name: str,
                            years: List[int],
                            sample_size: Optional[int],
                            metrics: Dict[str, float],
                            environmental_impact: float = 0.0,
                            config: Optional[EloConfig] = None) -> int:
        """
        Store backtest results in database.
        
        Args:
            config_name: Name of the configuration tested
            years: Years tested
            sample_size: Sample size used (None for full dataset)
            metrics: Performance metrics dictionary
            environmental_impact: Total environmental impact
            config: Elo configuration object
            
        Returns:
            Database ID of stored result
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        config_json = json.dumps(config.dict()) if config else None
        
        cursor.execute('''
            INSERT INTO backtest_results 
            (timestamp, config_name, years, sample_size, brier_score, log_loss, 
             accuracy, mae, calibration, ece, sharpness, total_games, 
             environmental_impact, config_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, config_name, json.dumps(years), sample_size,
            metrics.get('brier_score', 0.0), metrics.get('log_loss', 0.0),
            metrics.get('accuracy', 0.0), metrics.get('mae', 0.0),
            metrics.get('calibration', 0.0), metrics.get('ece', 0.0),
            metrics.get('sharpness', 0.0), metrics.get('total_games', 0),
            environmental_impact, config_json
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.info(f"Stored backtest result {result_id} for {config_name}")
        return result_id
    
    def store_team_performance(self,
                             team: str,
                             config_name: str,
                             season: int,
                             total_games: int,
                             metrics: Dict[str, float],
                             environmental_impact: float = 0.0,
                             improvement_pct: float = 0.0) -> int:
        """
        Store team-specific performance metrics.
        
        Args:
            team: Team abbreviation
            config_name: Configuration name
            season: Season year
            total_games: Number of games for this team
            metrics: Performance metrics
            environmental_impact: Environmental impact for this team
            improvement_pct: Improvement percentage over baseline
            
        Returns:
            Database ID of stored result
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO team_performance 
            (timestamp, team, config_name, season, total_games, brier_score, 
             accuracy, environmental_impact, improvement_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, team, config_name, season, total_games,
            metrics.get('brier_score', 0.0), metrics.get('accuracy', 0.0),
            environmental_impact, improvement_pct
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def store_environmental_impact(self,
                                 config_name: str,
                                 weather_impact: float = 0.0,
                                 travel_impact: float = 0.0,
                                 qb_impact: float = 0.0,
                                 epa_impact: float = 0.0,
                                 total_impact: float = 0.0,
                                 avg_impact_per_game: float = 0.0) -> int:
        """
        Store environmental impact metrics.
        
        Args:
            config_name: Configuration name
            weather_impact: Weather adjustment impact
            travel_impact: Travel adjustment impact
            qb_impact: QB adjustment impact
            epa_impact: EPA adjustment impact
            total_impact: Total environmental impact
            avg_impact_per_game: Average impact per game
            
        Returns:
            Database ID of stored result
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO environmental_impacts 
            (timestamp, config_name, weather_impact, travel_impact, qb_impact, 
             epa_impact, total_impact, avg_impact_per_game)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, config_name, weather_impact, travel_impact, qb_impact,
            epa_impact, total_impact, avg_impact_per_game
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def store_weight_optimization(self,
                                optimization_type: str,
                                best_brier_score: float,
                                best_params: Dict[str, Any],
                                total_combinations: int,
                                optimization_time: float) -> int:
        """
        Store weight optimization results.
        
        Args:
            optimization_type: Type of optimization (e.g., 'enhanced', 'standard')
            best_brier_score: Best Brier score found
            best_params: Best parameters found
            total_combinations: Total combinations tested
            optimization_time: Time taken for optimization (seconds)
            
        Returns:
            Database ID of stored result
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO weight_optimization 
            (timestamp, optimization_type, best_brier_score, best_params, 
             total_combinations, optimization_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, optimization_type, best_brier_score, 
            json.dumps(best_params), total_combinations, optimization_time
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_backtest_history(self, 
                           config_name: Optional[str] = None,
                           days_back: int = 30) -> pd.DataFrame:
        """
        Get backtest history from database.
        
        Args:
            config_name: Filter by configuration name (None for all)
            days_back: Number of days to look back
            
        Returns:
            DataFrame with backtest history
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM backtest_results 
            WHERE created_at >= datetime('now', '-{} days')
        '''.format(days_back)
        
        params = []
        if config_name:
            query += " AND config_name = ?"
            params.append(config_name)
        
        query += " ORDER BY created_at DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_team_performance_history(self,
                                   team: Optional[str] = None,
                                   config_name: Optional[str] = None,
                                   days_back: int = 30) -> pd.DataFrame:
        """
        Get team performance history from database.
        
        Args:
            team: Filter by team (None for all)
            config_name: Filter by configuration name (None for all)
            days_back: Number of days to look back
            
        Returns:
            DataFrame with team performance history
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM team_performance 
            WHERE created_at >= datetime('now', '-{} days')
        '''.format(days_back)
        
        params = []
        if team:
            query += " AND team = ?"
            params.append(team)
        
        if config_name:
            query += " AND config_name = ?"
            params.append(config_name)
        
        query += " ORDER BY created_at DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_environmental_impact_history(self,
                                       config_name: Optional[str] = None,
                                       days_back: int = 30) -> pd.DataFrame:
        """
        Get environmental impact history from database.
        
        Args:
            config_name: Filter by configuration name (None for all)
            days_back: Number of days to look back
            
        Returns:
            DataFrame with environmental impact history
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM environmental_impacts 
            WHERE created_at >= datetime('now', '-{} days')
        '''.format(days_back)
        
        params = []
        if config_name:
            query += " AND config_name = ?"
            params.append(config_name)
        
        query += " ORDER BY created_at DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_performance_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get performance summary for the last N days.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with performance summary
        """
        backtest_df = self.get_backtest_history(days_back=days_back)
        team_df = self.get_team_performance_history(days_back=days_back)
        env_df = self.get_environmental_impact_history(days_back=days_back)
        
        summary = {
            'total_backtests': len(backtest_df),
            'total_team_analyses': len(team_df),
            'total_environmental_analyses': len(env_df),
            'best_brier_score': backtest_df['brier_score'].min() if len(backtest_df) > 0 else None,
            'best_config': backtest_df.loc[backtest_df['brier_score'].idxmin(), 'config_name'] if len(backtest_df) > 0 else None,
            'avg_improvement': team_df['improvement_pct'].mean() if len(team_df) > 0 else None,
            'teams_with_improvements': len(team_df[team_df['improvement_pct'] > 0]) if len(team_df) > 0 else 0,
            'environmental_impact_avg': env_df['total_impact'].mean() if len(env_df) > 0 else None
        }
        
        return summary
    
    def export_stats_to_csv(self, output_dir: str = "artifacts/stats_export"):
        """
        Export all stats to CSV files.
        
        Args:
            output_dir: Directory to save CSV files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export all tables
        backtest_df = self.get_backtest_history(days_back=365)
        team_df = self.get_team_performance_history(days_back=365)
        env_df = self.get_environmental_impact_history(days_back=365)
        
        backtest_df.to_csv(output_path / "backtest_results.csv", index=False)
        team_df.to_csv(output_path / "team_performance.csv", index=False)
        env_df.to_csv(output_path / "environmental_impacts.csv", index=False)
        
        self.logger.info(f"Exported stats to {output_path}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data to keep database size manageable.
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        tables = ['backtest_results', 'team_performance', 'environmental_impacts', 'weight_optimization']
        
        for table in tables:
            cursor.execute(f'''
                DELETE FROM {table} 
                WHERE created_at < ?
            ''', (cutoff_date.isoformat(),))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cleaned up data older than {days_to_keep} days")


# Global stats storage instance
stats_storage = StatsStorage()


def get_stats_storage() -> StatsStorage:
    """Get the global stats storage instance."""
    return stats_storage
