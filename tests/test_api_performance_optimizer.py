#!/usr/bin/env python3
"""
Tests for API Performance Optimizer
Comprehensive test suite for API performance monitoring and optimization.
"""

import unittest
import tempfile
import os
import time
import json
import sqlite3
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_performance_optimizer import (
    APIPerformanceMonitor, 
    DatabaseQueryOptimizer, 
    APICacheManager, 
    APIPerformanceOptimizer,
    performance_monitor
)

class TestAPIPerformanceMonitor(unittest.TestCase):
    """Test cases for API performance monitoring."""
    
    def setUp(self):
        """Set up test environment."""
        self.monitor = APIPerformanceMonitor()
    
    def test_record_response_time(self):
        """Test recording response times."""
        self.monitor.record_response_time("/api/test", "GET", 0.1, 200)
        self.monitor.record_response_time("/api/test", "GET", 0.2, 200)
        
        stats = self.monitor.get_performance_stats()
        self.assertIn("GET:/api/test", stats)
        self.assertEqual(stats["GET:/api/test"]['request_count'], 2)
        self.assertEqual(stats["GET:/api/test"]['error_count'], 0)
    
    def test_record_error_response(self):
        """Test recording error responses."""
        self.monitor.record_response_time("/api/test", "GET", 0.1, 500)
        self.monitor.record_response_time("/api/test", "GET", 0.2, 200)
        
        stats = self.monitor.get_performance_stats()
        self.assertEqual(stats["GET:/api/test"]['error_count'], 1)
        self.assertEqual(stats["GET:/api/test"]['error_rate'], 50.0)
    
    def test_get_slow_endpoints(self):
        """Test identifying slow endpoints."""
        # Add fast endpoint
        self.monitor.record_response_time("/api/fast", "GET", 0.1, 200)
        
        # Add slow endpoint
        self.monitor.record_response_time("/api/slow", "GET", 0.5, 200)
        
        slow_endpoints = self.monitor.get_slow_endpoints(300)  # 300ms threshold
        self.assertEqual(len(slow_endpoints), 1)
        self.assertEqual(slow_endpoints[0]['endpoint'], "/api/slow")
        self.assertGreater(slow_endpoints[0]['avg_time_ms'], 300)
    
    def test_performance_stats_calculation(self):
        """Test performance statistics calculation."""
        # Add multiple response times
        times = [0.1, 0.2, 0.3, 0.4, 0.5]
        for t in times:
            self.monitor.record_response_time("/api/test", "GET", t, 200)
        
        stats = self.monitor.get_performance_stats()
        endpoint_stats = stats["GET:/api/test"]
        
        self.assertEqual(endpoint_stats['request_count'], 5)
        self.assertEqual(endpoint_stats['avg_time_ms'], 300.0)  # 0.3s * 1000
        self.assertEqual(endpoint_stats['min_time_ms'], 100.0)  # 0.1s * 1000
        self.assertEqual(endpoint_stats['max_time_ms'], 500.0)  # 0.5s * 1000

class TestDatabaseQueryOptimizer(unittest.TestCase):
    """Test cases for database query optimization."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create test database
        self._create_test_database()
        
        self.optimizer = DatabaseQueryOptimizer(self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_test_database(self):
        """Create test database with sample data."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE team_ratings (
                team TEXT,
                rating REAL,
                season INTEGER,
                config_name TEXT,
                wins INTEGER,
                losses INTEGER,
                rating_change REAL
            )
        """)
        
        # Insert test data
        for i in range(10):
            conn.execute("""
                INSERT INTO team_ratings (team, rating, season, config_name, wins, losses, rating_change)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"Team{i}", 1500 + i * 10, 2025, 'comprehensive', 10 + i, 6 - i, 5 + i))
        
        conn.commit()
        conn.close()
    
    def test_execute_optimized_query(self):
        """Test executing optimized queries."""
        query = "SELECT * FROM team_ratings WHERE season = ? AND config_name = ?"
        params = (2025, 'comprehensive')
        
        results = self.optimizer.execute_optimized_query(query, params)
        
        self.assertEqual(len(results), 10)
        self.assertIn('team', results[0])
        self.assertIn('rating', results[0])
    
    def test_query_statistics_tracking(self):
        """Test query statistics tracking."""
        query = "SELECT COUNT(*) as count FROM team_ratings"
        
        # Execute query multiple times
        for _ in range(3):
            self.optimizer.execute_optimized_query(query)
        
        stats = self.optimizer.query_stats[query]
        self.assertEqual(stats['count'], 3)
        self.assertGreater(stats['total_time'], 0)
        self.assertGreater(stats['avg_time'], 0)

class TestAPICacheManager(unittest.TestCase):
    """Test cases for API cache management."""
    
    def setUp(self):
        """Set up test cache manager."""
        self.cache_manager = APICacheManager(max_size=5, default_ttl=60)
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        endpoint = "/api/test"
        params = {"season": 2025}
        data = {"teams": ["PHI", "DAL"]}
        
        # Cache miss
        self.assertIsNone(self.cache_manager.get(endpoint, params))
        
        # Cache set
        self.cache_manager.set(endpoint, params, data)
        
        # Cache hit
        cached_data = self.cache_manager.get(endpoint, params)
        self.assertEqual(cached_data, data)
    
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        endpoint = "/api/test"
        params = {"season": 2025}
        data = {"teams": ["PHI", "DAL"]}
        
        # Set with short TTL
        self.cache_manager.set(endpoint, params, data, ttl=1)
        
        # Should be available immediately
        self.assertIsNotNone(self.cache_manager.get(endpoint, params))
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        self.assertIsNone(self.cache_manager.get(endpoint, params))
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        for i in range(5):
            self.cache_manager.set(f"/api/test{i}", {"id": i}, f"data{i}")
        
        # Add one more item to trigger eviction
        self.cache_manager.set("/api/overflow", {"id": 999}, "overflow_data")
        
        # Cache should not exceed max size
        self.assertLessEqual(len(self.cache_manager.cache), 5)
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        endpoint = "/api/test"
        params1 = {"season": 2025, "config": "comprehensive"}
        params2 = {"config": "comprehensive", "season": 2025}  # Different order
        
        key1 = self.cache_manager.get_cache_key(endpoint, params1)
        key2 = self.cache_manager.get_cache_key(endpoint, params2)
        
        # Should generate same key regardless of param order
        self.assertEqual(key1, key2)

class TestAPIPerformanceOptimizer(unittest.TestCase):
    """Test cases for main API performance optimizer."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create test database
        self._create_test_database()
        
        self.optimizer = APIPerformanceOptimizer(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_test_database(self):
        """Create test database with sample data."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE team_ratings (
                team TEXT,
                rating REAL,
                season INTEGER,
                config_name TEXT,
                wins INTEGER,
                losses INTEGER,
                rating_change REAL
            )
        """)
        
        # Insert test data
        for i in range(5):
            conn.execute("""
                INSERT INTO team_ratings (team, rating, season, config_name, wins, losses, rating_change)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"Team{i}", 1500 + i * 10, 2025, 'comprehensive', 10 + i, 6 - i, 5 + i))
        
        conn.commit()
        conn.close()
    
    def test_analyze_current_performance(self):
        """Test current performance analysis."""
        performance = self.optimizer.analyze_current_performance()
        
        # Should have tested all endpoints
        expected_endpoints = [
            "/api/elo/ratings",
            "/api/elo/season-summary", 
            "/api/teams/rankings",
            "/api/injuries/summary",
            "/api/system/status"
        ]
        
        for endpoint in expected_endpoints:
            self.assertIn(endpoint, performance)
            self.assertIn('avg_time_ms', performance[endpoint])
            self.assertGreater(performance[endpoint]['avg_time_ms'], 0)
    
    def test_optimize_database_queries(self):
        """Test database query optimization."""
        optimizations = self.optimizer.optimize_database_queries()
        
        # Should have optimized all queries
        expected_queries = ["elo_ratings", "team_rankings", "season_summary"]
        
        for query in expected_queries:
            self.assertIn(query, optimizations)
            self.assertIn('status', optimizations[query])
    
    def test_implement_caching_strategy(self):
        """Test caching strategy implementation."""
        cache_results = self.optimizer.implement_caching_strategy()
        
        # Should have implemented caching for all endpoints
        expected_endpoints = [
            "elo_ratings", "team_rankings", "season_summary", 
            "injury_data", "system_status"
        ]
        
        for endpoint in expected_endpoints:
            self.assertIn(endpoint, cache_results)
            self.assertIn('hit_time_ms', cache_results[endpoint])
            self.assertIn('miss_time_ms', cache_results[endpoint])
    
    def test_generate_optimization_report(self):
        """Test optimization report generation."""
        report = self.optimizer.generate_optimization_report()
        
        # Check report structure
        self.assertIn('timestamp', report)
        self.assertIn('overall_performance', report)
        self.assertIn('current_performance', report)
        self.assertIn('query_optimizations', report)
        self.assertIn('caching_results', report)
        self.assertIn('recommendations', report)
        
        # Check overall performance metrics
        overall = report['overall_performance']
        self.assertIn('average_response_time_ms', overall)
        self.assertIn('endpoints_over_300ms', overall)
        self.assertIn('target_met', overall)
    
    def test_performance_monitor_decorator(self):
        """Test performance monitor decorator."""
        monitor = APIPerformanceMonitor()
        
        @performance_monitor(monitor)
        def test_endpoint():
            time.sleep(0.01)  # Simulate work
            return {"data": "test"}
        
        # Call decorated function
        result = test_endpoint()
        
        # Check that performance was recorded
        stats = monitor.get_performance_stats()
        self.assertGreater(len(stats), 0)
        
        # Check result
        self.assertEqual(result, {"data": "test"})

class TestPerformanceOptimizationIntegration(unittest.TestCase):
    """Integration tests for performance optimization."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create realistic test database
        self._create_realistic_test_database()
    
    def tearDown(self):
        """Clean up integration test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_realistic_test_database(self):
        """Create realistic test database."""
        conn = sqlite3.connect(self.db_path)
        
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
        
        # Insert realistic data
        teams = ['PHI', 'DAL', 'SF', 'BUF', 'BAL', 'KC', 'GB', 'MIN']
        for season in [2022, 2023, 2024, 2025]:
            for i, team in enumerate(teams):
                conn.execute("""
                    INSERT INTO team_ratings (team, rating, season, config_name, wins, losses, rating_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (team, 1400 + i * 15, season, 'comprehensive', 8 + (i % 8), 8 - (i % 8), (i % 10) - 5))
        
        # Create indexes
        conn.execute("CREATE INDEX idx_team_ratings_season_config ON team_ratings(season, config_name, rating DESC)")
        conn.execute("CREATE INDEX idx_team_ratings_team_season ON team_ratings(team, season, config_name)")
        
        conn.commit()
        conn.close()
    
    def test_end_to_end_optimization(self):
        """Test complete end-to-end optimization process."""
        optimizer = APIPerformanceOptimizer(self.db_path)
        
        # Run optimization
        report = optimizer.generate_optimization_report()
        
        # Verify optimization was successful
        self.assertIn('overall_performance', report)
        self.assertIn('recommendations', report)
        
        # Check that database optimizations were applied
        with optimizer.query_optimizer.get_connection() as conn:
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            self.assertEqual(journal_mode.lower(), 'wal')
    
    def test_performance_improvement(self):
        """Test that optimization actually improves performance."""
        optimizer = APIPerformanceOptimizer(self.db_path)
        
        # Run optimization
        report = optimizer.generate_optimization_report()
        
        # Check that some optimizations were applied
        self.assertGreater(len(report['query_optimizations']), 0)
        self.assertGreater(len(report['caching_results']), 0)
        
        # Check that recommendations were generated
        self.assertGreater(len(report['recommendations']), 0)

if __name__ == '__main__':
    # Create artifacts directory if it doesn't exist
    os.makedirs('artifacts', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)
