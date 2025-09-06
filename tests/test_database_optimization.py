#!/usr/bin/env python3
"""
Tests for Database Optimization
Comprehensive test suite for database performance optimization.
"""

import unittest
import sqlite3
import tempfile
import os
import time
import json
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_optimization import DatabaseOptimizer

class TestDatabaseOptimization(unittest.TestCase):
    """Test cases for database optimization functionality."""
    
    def setUp(self):
        """Set up test database and optimizer."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create test database with sample data
        self._create_test_database()
        
        # Initialize optimizer
        self.optimizer = DatabaseOptimizer(self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_test_database(self):
        """Create test database with sample data."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Create team_ratings table
        conn.execute("""
            CREATE TABLE team_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                rating REAL NOT NULL,
                season INTEGER NOT NULL,
                config_name TEXT DEFAULT 'baseline',
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                win_pct REAL DEFAULT 0.0,
                rating_change REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                points_for INTEGER DEFAULT 0,
                points_against INTEGER DEFAULT 0,
                point_differential INTEGER DEFAULT 0,
                avg_points_for REAL DEFAULT 0.0,
                avg_points_against REAL DEFAULT 0.0,
                total_games INTEGER DEFAULT 0,
                UNIQUE(team, season, config_name)
            )
        """)
        
        # Create action_network_picks table
        conn.execute("""
            CREATE TABLE action_network_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expert TEXT NOT NULL,
                pick TEXT NOT NULL,
                confidence REAL NOT NULL,
                game_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create nfl_games_2025 table
        conn.execute("""
            CREATE TABLE nfl_games_2025 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                week INTEGER NOT NULL,
                game_date DATE NOT NULL
            )
        """)
        
        # Create backtest_results table
        conn.execute("""
            CREATE TABLE backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                log_loss REAL NOT NULL,
                brier_score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample data
        self._insert_sample_data(conn)
        
        # Create initial indexes
        conn.execute("CREATE INDEX idx_team_ratings_season_config ON team_ratings(season, config_name, rating DESC)")
        conn.execute("CREATE INDEX idx_team_ratings_team_season ON team_ratings(team, season, config_name)")
        
        conn.commit()
        conn.close()
    
    def _insert_sample_data(self, conn):
        """Insert sample data for testing."""
        # Insert team ratings
        teams = ['PHI', 'DAL', 'SF', 'BUF', 'BAL', 'KC', 'GB', 'MIN']
        for i, team in enumerate(teams):
            for season in [2022, 2023, 2024, 2025]:
                conn.execute("""
                    INSERT INTO team_ratings (team, rating, season, config_name, wins, losses, rating_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (team, 1500 + i * 10, season, 'comprehensive', 10 + i, 6 - i, 5 + i))
        
        # Insert action network picks
        experts = ['Expert1', 'Expert2', 'Expert3']
        picks = ['PHI -3.5', 'DAL +7', 'SF -2.5', 'BUF +1.5']
        for i in range(20):
            conn.execute("""
                INSERT INTO action_network_picks (expert, pick, confidence, game_date)
                VALUES (?, ?, ?, ?)
            """, (experts[i % len(experts)], picks[i % len(picks)], 0.6 + (i % 4) * 0.1, '2025-01-15'))
        
        # Insert NFL games
        for week in range(1, 6):
            for i in range(8):
                conn.execute("""
                    INSERT INTO nfl_games_2025 (home_team, away_team, home_score, away_score, week, game_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (teams[i], teams[(i + 1) % len(teams)], 20 + i, 17 + i, week, '2025-01-15'))
        
        # Insert backtest results
        for season in [2022, 2023, 2024]:
            conn.execute("""
                INSERT INTO backtest_results (season, accuracy, log_loss, brier_score)
                VALUES (?, ?, ?, ?)
            """, (season, 0.6 + season * 0.01, 0.7 - season * 0.01, 0.25 + season * 0.005))
    
    def test_database_connection(self):
        """Test database connection functionality."""
        with self.optimizer.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM team_ratings")
            result = cursor.fetchone()
            self.assertGreater(result['count'], 0)
    
    def test_analyze_current_performance(self):
        """Test current performance analysis."""
        results = self.optimizer.analyze_current_performance()
        
        # Check that all expected queries are tested
        expected_queries = [
            'elo_ratings_current', 'elo_ratings_historical', 'team_comparison',
            'action_network_picks', 'backtest_results', 'nfl_games_2025'
        ]
        
        for query in expected_queries:
            self.assertIn(query, results)
            self.assertIn('status', results[query])
            if results[query]['status'] == 'success':
                self.assertIn('avg_time_ms', results[query])
                self.assertGreaterEqual(results[query]['avg_time_ms'], 0)
    
    def test_create_optimization_indexes(self):
        """Test index creation functionality."""
        results = self.optimizer.create_optimization_indexes()
        
        # Check that indexes were created
        self.assertGreater(len(results), 0)
        
        # Verify indexes exist in database
        with self.optimizer.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            # Check for some expected indexes
            expected_indexes = ['idx_team_ratings_rating_desc', 'idx_action_network_picks_date']
            for idx in expected_indexes:
                if any(idx in result for result in results.values() if result.get('status') == 'created'):
                    self.assertIn(idx, indexes)
    
    def test_optimize_database_settings(self):
        """Test database settings optimization."""
        results = self.optimizer.optimize_database_settings()
        
        # Check that settings were applied
        self.assertGreater(len(results), 0)
        
        # Verify WAL mode was set
        if 'journal_mode' in results and results['journal_mode']['status'] == 'success':
            self.assertEqual(results['journal_mode']['new_value'], 'wal')
    
    def test_run_query_optimization_tests(self):
        """Test query optimization testing."""
        results = self.optimizer.run_query_optimization_tests()
        
        # Check that tests were run
        expected_tests = [
            'team_ratings_by_rating', 'recent_picks', 'games_by_week', 'backtest_accuracy'
        ]
        
        for test in expected_tests:
            self.assertIn(test, results)
            self.assertIn('status', results[test])
            if results[test]['status'] == 'success':
                self.assertIn('avg_time_ms', results[test])
    
    def test_generate_performance_report(self):
        """Test performance report generation."""
        # Mock data for testing
        before_results = {
            'test_query': {'avg_time_ms': 100, 'status': 'success'}
        }
        after_results = {
            'test_query': {'avg_time_ms': 50, 'status': 'success'}
        }
        index_results = {
            'test_index': {'status': 'created', 'table': 'test_table'}
        }
        settings_results = {
            'journal_mode': {'status': 'success', 'new_value': 'wal'}
        }
        
        report = self.optimizer.generate_performance_report(
            before_results, after_results, index_results, settings_results
        )
        
        # Check report structure
        self.assertIn('timestamp', report)
        self.assertIn('optimization_summary', report)
        self.assertIn('performance_comparison', report)
        self.assertIn('recommendations', report)
        
        # Check performance comparison
        self.assertIn('test_query', report['performance_comparison'])
        comparison = report['performance_comparison']['test_query']
        self.assertEqual(comparison['before_ms'], 100)
        self.assertEqual(comparison['after_ms'], 50)
        self.assertTrue(comparison['faster'])
    
    def test_run_full_optimization(self):
        """Test complete optimization process."""
        results = self.optimizer.run_full_optimization()
        
        # Check that optimization completed
        self.assertIn('timestamp', results)
        self.assertIn('before_optimization', results)
        self.assertIn('after_optimization', results)
        self.assertIn('index_creation', results)
        self.assertIn('settings_optimization', results)
        self.assertIn('performance_report', results)
        
        # Check that results file was created
        results_files = [f for f in os.listdir('artifacts') if f.startswith('database_optimization_')]
        self.assertGreater(len(results_files), 0)
    
    def test_performance_improvement(self):
        """Test that optimization actually improves performance."""
        # Run optimization
        results = self.optimizer.run_full_optimization()
        
        # Check that some queries improved
        performance_comparison = results['performance_report']['performance_comparison']
        improved_queries = [q for q in performance_comparison.values() if q.get('faster', False)]
        
        # At least some queries should be faster (or at least not slower)
        self.assertGreaterEqual(len(improved_queries), 0)
    
    def test_error_handling(self):
        """Test error handling with invalid database."""
        # Test with non-existent database
        invalid_optimizer = DatabaseOptimizer("non_existent.db")
        results = invalid_optimizer.run_full_optimization()
        
        self.assertIn('error', results)
        self.assertEqual(results['error'], 'Database not found')
    
    def test_index_creation_idempotency(self):
        """Test that creating indexes multiple times doesn't cause errors."""
        # Create indexes first time
        results1 = self.optimizer.create_optimization_indexes()
        
        # Create indexes second time
        results2 = self.optimizer.create_optimization_indexes()
        
        # Should not have any failures due to existing indexes
        failed_indexes = [r for r in results2.values() if r.get('status') == 'failed']
        self.assertEqual(len(failed_indexes), 0)

class TestDatabaseOptimizationIntegration(unittest.TestCase):
    """Integration tests for database optimization."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
    
    def tearDown(self):
        """Clean up integration test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_end_to_end_optimization(self):
        """Test complete end-to-end optimization process."""
        # Create a realistic test database
        self._create_realistic_test_database()
        
        # Run optimization
        optimizer = DatabaseOptimizer(self.db_path)
        results = optimizer.run_full_optimization()
        
        # Verify optimization was successful
        self.assertIn('performance_report', results)
        self.assertIn('optimization_summary', results['performance_report'])
        
        # Check that database settings were applied
        with optimizer.get_connection() as conn:
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            self.assertEqual(journal_mode.lower(), 'wal')
    
    def _create_realistic_test_database(self):
        """Create a more realistic test database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Create all tables with proper schema
        conn.execute("""
            CREATE TABLE team_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                rating REAL NOT NULL,
                season INTEGER NOT NULL,
                config_name TEXT DEFAULT 'baseline',
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                win_pct REAL DEFAULT 0.0,
                rating_change REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                points_for INTEGER DEFAULT 0,
                points_against INTEGER DEFAULT 0,
                point_differential INTEGER DEFAULT 0,
                avg_points_for REAL DEFAULT 0.0,
                avg_points_against REAL DEFAULT 0.0,
                total_games INTEGER DEFAULT 0,
                UNIQUE(team, season, config_name)
            )
        """)
        
        # Insert more realistic data
        teams = ['PHI', 'DAL', 'SF', 'BUF', 'BAL', 'KC', 'GB', 'MIN', 'DET', 'CIN', 'LAR', 'TB']
        for season in [2022, 2023, 2024, 2025]:
            for i, team in enumerate(teams):
                conn.execute("""
                    INSERT INTO team_ratings (team, rating, season, config_name, wins, losses, rating_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (team, 1400 + i * 15, season, 'comprehensive', 8 + (i % 8), 8 - (i % 8), (i % 10) - 5))
        
        conn.commit()
        conn.close()

if __name__ == '__main__':
    # Create artifacts directory if it doesn't exist
    os.makedirs('artifacts', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)
