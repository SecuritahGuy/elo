#!/usr/bin/env python3
"""
Test Unified Database Implementation
Comprehensive test suite for the unified multi-sport database
"""

import sqlite3
import pandas as pd
import unittest
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedDatabaseTester:
    """Test suite for unified database functionality."""
    
    def __init__(self, db_path: str = "sportsedge_unified.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all database tests."""
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': [],
            'errors': []
        }
        
        test_methods = [
            self.test_database_connection,
            self.test_schema_creation,
            self.test_initial_data,
            self.test_foreign_key_constraints,
            self.test_indexes,
            self.test_data_integrity,
            self.test_performance,
            self.test_multi_sport_support
        ]
        
        for test_method in test_methods:
            try:
                result = test_method()
                results['total_tests'] += 1
                if result['passed']:
                    results['passed_tests'] += 1
                else:
                    results['failed_tests'] += 1
                results['test_results'].append(result)
            except Exception as e:
                error_msg = f"Test {test_method.__name__} failed with exception: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['total_tests'] += 1
                results['failed_tests'] += 1
        
        return results
    
    def test_database_connection(self) -> Dict[str, Any]:
        """Test database connection and basic functionality."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result[0] == 1:
                return {
                    'test_name': 'Database Connection',
                    'passed': True,
                    'message': 'Database connection successful'
                }
            else:
                return {
                    'test_name': 'Database Connection',
                    'passed': False,
                    'message': 'Unexpected query result'
                }
        except Exception as e:
            return {
                'test_name': 'Database Connection',
                'passed': False,
                'message': f'Connection failed: {e}'
            }
    
    def test_schema_creation(self) -> Dict[str, Any]:
        """Test that all required tables exist."""
        required_tables = [
            'sports', 'leagues', 'seasons', 'teams', 'games',
            'odds', 'experts', 'expert_performance', 'expert_picks',
            'team_ratings', 'predictions', 'backtest_results', 'live_updates'
        ]
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if not missing_tables:
                return {
                    'test_name': 'Schema Creation',
                    'passed': True,
                    'message': f'All {len(required_tables)} required tables exist'
                }
            else:
                return {
                    'test_name': 'Schema Creation',
                    'passed': False,
                    'message': f'Missing tables: {missing_tables}'
                }
        except Exception as e:
            return {
                'test_name': 'Schema Creation',
                'passed': False,
                'message': f'Schema check failed: {e}'
            }
    
    def test_initial_data(self) -> Dict[str, Any]:
        """Test that initial data was inserted correctly."""
        try:
            cursor = self.conn.cursor()
            
            # Check sports data
            cursor.execute("SELECT COUNT(*) FROM sports")
            sports_count = cursor.fetchone()[0]
            
            # Check NFL leagues
            cursor.execute("SELECT COUNT(*) FROM leagues WHERE sport_id = 1")
            nfl_leagues_count = cursor.fetchone()[0]
            
            # Check NFL seasons
            cursor.execute("SELECT COUNT(*) FROM seasons WHERE sport_id = 1")
            nfl_seasons_count = cursor.fetchone()[0]
            
            if sports_count >= 6 and nfl_leagues_count >= 11 and nfl_seasons_count >= 5:
                return {
                    'test_name': 'Initial Data',
                    'passed': True,
                    'message': f'Sports: {sports_count}, NFL Leagues: {nfl_leagues_count}, NFL Seasons: {nfl_seasons_count}'
                }
            else:
                return {
                    'test_name': 'Initial Data',
                    'passed': False,
                    'message': f'Insufficient initial data - Sports: {sports_count}, NFL Leagues: {nfl_leagues_count}, NFL Seasons: {nfl_seasons_count}'
                }
        except Exception as e:
            return {
                'test_name': 'Initial Data',
                'passed': False,
                'message': f'Initial data check failed: {e}'
            }
    
    def test_foreign_key_constraints(self) -> Dict[str, Any]:
        """Test foreign key constraints."""
        try:
            cursor = self.conn.cursor()
            
            # Test that foreign keys are enabled
            cursor.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            
            if not fk_enabled:
                return {
                    'test_name': 'Foreign Key Constraints',
                    'passed': False,
                    'message': 'Foreign keys are not enabled'
                }
            
            # Test foreign key constraint by trying to insert invalid data
            try:
                cursor.execute("INSERT INTO teams (sport_id, team_code, team_name, city, mascot) VALUES (999, 'TEST', 'Test Team', 'Test City', 'Test')")
                self.conn.rollback()
                return {
                    'test_name': 'Foreign Key Constraints',
                    'passed': False,
                    'message': 'Foreign key constraint not working - invalid sport_id accepted'
                }
            except sqlite3.IntegrityError:
                # This is expected - foreign key constraint should prevent this
                pass
            
            return {
                'test_name': 'Foreign Key Constraints',
                'passed': True,
                'message': 'Foreign key constraints are working correctly'
            }
        except Exception as e:
            return {
                'test_name': 'Foreign Key Constraints',
                'passed': False,
                'message': f'Foreign key test failed: {e}'
            }
    
    def test_indexes(self) -> Dict[str, Any]:
        """Test that performance indexes exist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_sports_code', 'idx_leagues_sport_id', 'idx_seasons_sport_year',
                'idx_teams_sport_code', 'idx_games_sport_season', 'idx_games_teams',
                'idx_odds_game_id', 'idx_experts_external_id', 'idx_expert_picks_expert_game'
            ]
            
            missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
            
            if not missing_indexes:
                return {
                    'test_name': 'Indexes',
                    'passed': True,
                    'message': f'All {len(expected_indexes)} expected indexes exist'
                }
            else:
                return {
                    'test_name': 'Indexes',
                    'passed': False,
                    'message': f'Missing indexes: {missing_indexes}'
                }
        except Exception as e:
            return {
                'test_name': 'Indexes',
                'passed': False,
                'message': f'Index test failed: {e}'
            }
    
    def test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and consistency."""
        try:
            cursor = self.conn.cursor()
            
            # Test that all teams have valid sport_id
            cursor.execute("SELECT COUNT(*) FROM teams WHERE sport_id NOT IN (SELECT id FROM sports)")
            invalid_teams = cursor.fetchone()[0]
            
            # Test that all games have valid team_ids
            cursor.execute("SELECT COUNT(*) FROM games WHERE home_team_id NOT IN (SELECT id FROM teams) OR away_team_id NOT IN (SELECT id FROM teams)")
            invalid_games = cursor.fetchone()[0]
            
            # Test that all expert_picks have valid expert_id
            cursor.execute("SELECT COUNT(*) FROM expert_picks WHERE expert_id NOT IN (SELECT id FROM experts)")
            invalid_picks = cursor.fetchone()[0]
            
            if invalid_teams == 0 and invalid_games == 0 and invalid_picks == 0:
                return {
                    'test_name': 'Data Integrity',
                    'passed': True,
                    'message': 'All foreign key relationships are valid'
                }
            else:
                return {
                    'test_name': 'Data Integrity',
                    'passed': False,
                    'message': f'Invalid relationships - Teams: {invalid_teams}, Games: {invalid_games}, Picks: {invalid_picks}'
                }
        except Exception as e:
            return {
                'test_name': 'Data Integrity',
                'passed': False,
                'message': f'Data integrity test failed: {e}'
            }
    
    def test_performance(self) -> Dict[str, Any]:
        """Test database performance with sample queries."""
        try:
            cursor = self.conn.cursor()
            
            # Test query performance
            start_time = datetime.now()
            
            # Complex query joining multiple tables
            cursor.execute('''
                SELECT s.sport_name, l.league_name, t.team_name, g.game_date, g.home_score, g.away_score
                FROM games g
                JOIN sports s ON g.sport_id = s.id
                JOIN leagues l ON g.league_id = l.id
                JOIN teams t ON g.home_team_id = t.id
                LIMIT 100
            ''')
            results = cursor.fetchall()
            
            end_time = datetime.now()
            query_time = (end_time - start_time).total_seconds()
            
            if query_time < 1.0:  # Should complete in under 1 second
                return {
                    'test_name': 'Performance',
                    'passed': True,
                    'message': f'Complex query completed in {query_time:.3f}s, returned {len(results)} rows'
                }
            else:
                return {
                    'test_name': 'Performance',
                    'passed': False,
                    'message': f'Query too slow: {query_time:.3f}s'
                }
        except Exception as e:
            return {
                'test_name': 'Performance',
                'passed': False,
                'message': f'Performance test failed: {e}'
            }
    
    def test_multi_sport_support(self) -> Dict[str, Any]:
        """Test multi-sport functionality."""
        try:
            cursor = self.conn.cursor()
            
            # Test that we can add a new sport
            cursor.execute("INSERT INTO sports (sport_code, sport_name, sport_type, season_structure) VALUES ('test', 'Test Sport', 'test', 'regular')")
            test_sport_id = cursor.lastrowid
            
            # Test that we can add a league for the new sport
            cursor.execute("INSERT INTO leagues (sport_id, league_code, league_name, level) VALUES (?, 'test_league', 'Test League', 'professional')", (test_sport_id,))
            test_league_id = cursor.lastrowid
            
            # Test that we can add a season for the new sport
            cursor.execute("INSERT INTO seasons (sport_id, season_year, season_name, status) VALUES (?, 2025, '2025', 'upcoming')", (test_sport_id,))
            test_season_id = cursor.lastrowid
            
            # Test that we can add teams for the new sport
            cursor.execute("INSERT INTO teams (sport_id, league_id, team_code, team_name, city, mascot) VALUES (?, ?, 'TEST1', 'Test Team 1', 'Test City', 'Testers')", (test_sport_id, test_league_id))
            cursor.execute("INSERT INTO teams (sport_id, league_id, team_code, team_name, city, mascot) VALUES (?, ?, 'TEST2', 'Test Team 2', 'Test City', 'Testers')", (test_sport_id, test_league_id))
            
            # Test that we can add a game for the new sport
            cursor.execute("INSERT INTO games (sport_id, season_id, league_id, game_type, home_team_id, away_team_id, game_date) VALUES (?, ?, ?, 'regular', ?, ?, '2025-01-01')", (test_sport_id, test_season_id, test_league_id, cursor.lastrowid - 1, cursor.lastrowid))
            
            # Clean up test data
            cursor.execute("DELETE FROM games WHERE sport_id = ?", (test_sport_id,))
            cursor.execute("DELETE FROM teams WHERE sport_id = ?", (test_sport_id,))
            cursor.execute("DELETE FROM seasons WHERE sport_id = ?", (test_sport_id,))
            cursor.execute("DELETE FROM leagues WHERE sport_id = ?", (test_sport_id,))
            cursor.execute("DELETE FROM sports WHERE id = ?", (test_sport_id,))
            
            self.conn.commit()
            
            return {
                'test_name': 'Multi-Sport Support',
                'passed': True,
                'message': 'Successfully created and managed test sport with teams and games'
            }
        except Exception as e:
            return {
                'test_name': 'Multi-Sport Support',
                'passed': False,
                'message': f'Multi-sport test failed: {e}'
            }
    
    def close(self):
        """Close database connection."""
        self.conn.close()

def main():
    """Main function to run tests."""
    print("🧪 Running Unified Database Tests...")
    print("=" * 50)
    
    tester = UnifiedDatabaseTester()
    results = tester.run_all_tests()
    tester.close()
    
    print(f"\n📊 Test Results Summary:")
    print(f"  Total Tests: {results['total_tests']}")
    print(f"  Passed: {results['passed_tests']}")
    print(f"  Failed: {results['failed_tests']}")
    print(f"  Success Rate: {(results['passed_tests'] / results['total_tests'] * 100):.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for test_result in results['test_results']:
        status = "✅ PASS" if test_result['passed'] else "❌ FAIL"
        print(f"  {status} {test_result['test_name']}: {test_result['message']}")
    
    if results['errors']:
        print(f"\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['failed_tests'] == 0:
        print(f"\n🎉 All tests passed! The unified database is ready for use.")
    else:
        print(f"\n⚠️  {results['failed_tests']} test(s) failed. Please review and fix issues.")

if __name__ == "__main__":
    main()
