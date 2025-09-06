#!/usr/bin/env python3
"""
Test Multi-Sport Integration
Comprehensive test script to validate the unified database and multi-sport functionality
"""

import sqlite3
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class MultiSportIntegrationTester:
    """Test suite for multi-sport integration."""
    
    def __init__(self, db_path: str = "sportsedge_unified.db", api_url: str = "http://localhost:5001"):
        self.db_path = db_path
        self.api_url = api_url
        self.results = {
            'database_tests': [],
            'api_tests': [],
            'integration_tests': [],
            'errors': []
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        print("🧪 Starting Multi-Sport Integration Tests")
        print("=" * 60)
        
        # Test database
        self.test_database_connectivity()
        self.test_database_schema()
        self.test_database_data()
        
        # Test API (if running)
        self.test_api_connectivity()
        if self.is_api_running():
            self.test_api_endpoints()
            self.test_multi_sport_api()
        
        # Test integration
        self.test_data_consistency()
        self.test_performance()
        
        self.print_results()
        return self.results
    
    def test_database_connectivity(self):
        """Test database connection and basic queries."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result[0] == 1:
                self.results['database_tests'].append({
                    'test': 'Database Connectivity',
                    'status': 'PASS',
                    'message': 'Database connection successful'
                })
            else:
                self.results['database_tests'].append({
                    'test': 'Database Connectivity',
                    'status': 'FAIL',
                    'message': 'Unexpected query result'
                })
            
            conn.close()
            
        except Exception as e:
            self.results['database_tests'].append({
                'test': 'Database Connectivity',
                'status': 'FAIL',
                'message': f'Connection failed: {e}'
            })
    
    def test_database_schema(self):
        """Test database schema completeness."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check required tables
            required_tables = [
                'sports', 'leagues', 'seasons', 'teams', 'games',
                'odds', 'experts', 'expert_performance', 'expert_picks',
                'team_ratings', 'predictions', 'backtest_results', 'live_updates'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if not missing_tables:
                self.results['database_tests'].append({
                    'test': 'Database Schema',
                    'status': 'PASS',
                    'message': f'All {len(required_tables)} required tables exist'
                })
            else:
                self.results['database_tests'].append({
                    'test': 'Database Schema',
                    'status': 'FAIL',
                    'message': f'Missing tables: {missing_tables}'
                })
            
            conn.close()
            
        except Exception as e:
            self.results['database_tests'].append({
                'test': 'Database Schema',
                'status': 'FAIL',
                'message': f'Schema check failed: {e}'
            })
    
    def test_database_data(self):
        """Test database data integrity and counts."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get data counts
            cursor.execute("SELECT COUNT(*) FROM sports")
            sports_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM teams")
            teams_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM games")
            games_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM experts")
            experts_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM expert_picks")
            picks_count = cursor.fetchone()[0]
            
            # Check data quality
            cursor.execute("SELECT COUNT(*) FROM teams WHERE sport_id IS NULL")
            invalid_teams = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM games WHERE sport_id IS NULL")
            invalid_games = cursor.fetchone()[0]
            
            data_quality_issues = []
            if invalid_teams > 0:
                data_quality_issues.append(f"{invalid_teams} teams with null sport_id")
            if invalid_games > 0:
                data_quality_issues.append(f"{invalid_games} games with null sport_id")
            
            if not data_quality_issues:
                self.results['database_tests'].append({
                    'test': 'Database Data',
                    'status': 'PASS',
                    'message': f'Sports: {sports_count}, Teams: {teams_count}, Games: {games_count}, Experts: {experts_count}, Picks: {picks_count}'
                })
            else:
                self.results['database_tests'].append({
                    'test': 'Database Data',
                    'status': 'WARN',
                    'message': f'Data issues: {", ".join(data_quality_issues)}'
                })
            
            conn.close()
            
        except Exception as e:
            self.results['database_tests'].append({
                'test': 'Database Data',
                'status': 'FAIL',
                'message': f'Data check failed: {e}'
            })
    
    def test_api_connectivity(self):
        """Test API server connectivity."""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            if response.status_code == 200:
                self.results['api_tests'].append({
                    'test': 'API Connectivity',
                    'status': 'PASS',
                    'message': 'API server responding'
                })
            else:
                self.results['api_tests'].append({
                    'test': 'API Connectivity',
                    'status': 'FAIL',
                    'message': f'API returned status {response.status_code}'
                })
        except requests.exceptions.ConnectionError:
            self.results['api_tests'].append({
                'test': 'API Connectivity',
                'status': 'SKIP',
                'message': 'API server not running'
            })
        except Exception as e:
            self.results['api_tests'].append({
                'test': 'API Connectivity',
                'status': 'FAIL',
                'message': f'API test failed: {e}'
            })
    
    def is_api_running(self) -> bool:
        """Check if API server is running."""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def test_api_endpoints(self):
        """Test core API endpoints."""
        endpoints = [
            ('/api/sports', 'GET'),
            ('/api/sports/nfl/teams', 'GET'),
            ('/api/sports/nfl/games', 'GET'),
            ('/api/sports/nfl/expert-picks', 'GET'),
            ('/api/sports/nfl/dashboard', 'GET')
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    self.results['api_tests'].append({
                        'test': f'API {endpoint}',
                        'status': 'PASS',
                        'message': f'Returned {len(data) if isinstance(data, list) else "data"}'
                    })
                else:
                    self.results['api_tests'].append({
                        'test': f'API {endpoint}',
                        'status': 'FAIL',
                        'message': f'Status {response.status_code}'
                    })
                    
            except Exception as e:
                self.results['api_tests'].append({
                    'test': f'API {endpoint}',
                    'status': 'FAIL',
                    'message': f'Error: {e}'
                })
    
    def test_multi_sport_api(self):
        """Test multi-sport API functionality."""
        sports = ['nfl', 'nba', 'mlb', 'nhl']
        
        for sport in sports:
            try:
                # Test sport-specific endpoints
                response = requests.get(f"{self.api_url}/api/sports/{sport}/teams", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    team_count = len(data.get('teams', []))
                    self.results['api_tests'].append({
                        'test': f'Multi-Sport {sport.upper()} Teams',
                        'status': 'PASS',
                        'message': f'Found {team_count} teams'
                    })
                else:
                    self.results['api_tests'].append({
                        'test': f'Multi-Sport {sport.upper()} Teams',
                        'status': 'FAIL',
                        'message': f'Status {response.status_code}'
                    })
                    
            except Exception as e:
                self.results['api_tests'].append({
                    'test': f'Multi-Sport {sport.upper()} Teams',
                    'status': 'FAIL',
                    'message': f'Error: {e}'
                })
    
    def test_data_consistency(self):
        """Test data consistency between database and API."""
        if not self.is_api_running():
            self.results['integration_tests'].append({
                'test': 'Data Consistency',
                'status': 'SKIP',
                'message': 'API not running'
            })
            return
        
        try:
            # Get data from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM teams WHERE sport_id = 1")
            db_teams = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM games WHERE sport_id = 1")
            db_games = cursor.fetchone()[0]
            
            conn.close()
            
            # Get data from API
            response = requests.get(f"{self.api_url}/api/sports/nfl/teams", timeout=5)
            api_teams = len(response.json().get('teams', [])) if response.status_code == 200 else 0
            
            response = requests.get(f"{self.api_url}/api/sports/nfl/games", timeout=5)
            api_games = len(response.json().get('games', [])) if response.status_code == 200 else 0
            
            # Compare counts
            if db_teams == api_teams and db_games == api_games:
                self.results['integration_tests'].append({
                    'test': 'Data Consistency',
                    'status': 'PASS',
                    'message': f'DB and API data match (Teams: {db_teams}, Games: {db_games})'
                })
            else:
                self.results['integration_tests'].append({
                    'test': 'Data Consistency',
                    'status': 'WARN',
                    'message': f'Data mismatch - DB: {db_teams} teams, {db_games} games | API: {api_teams} teams, {api_games} games'
                })
                
        except Exception as e:
            self.results['integration_tests'].append({
                'test': 'Data Consistency',
                'status': 'FAIL',
                'message': f'Consistency check failed: {e}'
            })
    
    def test_performance(self):
        """Test system performance."""
        try:
            start_time = time.time()
            
            # Test database query performance
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.sport_name, COUNT(t.id) as team_count, COUNT(g.id) as game_count
                FROM sports s
                LEFT JOIN teams t ON s.id = t.sport_id
                LEFT JOIN games g ON s.id = g.sport_id
                GROUP BY s.id, s.sport_name
            ''')
            
            results = cursor.fetchall()
            db_time = time.time() - start_time
            
            conn.close()
            
            # Test API performance (if running)
            api_time = None
            if self.is_api_running():
                start_time = time.time()
                try:
                    response = requests.get(f"{self.api_url}/api/sports", timeout=10)
                    api_time = time.time() - start_time
                except:
                    pass
            
            performance_issues = []
            if db_time > 1.0:
                performance_issues.append(f"Database query slow: {db_time:.2f}s")
            if api_time and api_time > 2.0:
                performance_issues.append(f"API response slow: {api_time:.2f}s")
            
            if not performance_issues:
                self.results['integration_tests'].append({
                    'test': 'Performance',
                    'status': 'PASS',
                    'message': f'DB: {db_time:.2f}s, API: {api_time:.2f}s' if api_time else f'DB: {db_time:.2f}s'
                })
            else:
                self.results['integration_tests'].append({
                    'test': 'Performance',
                    'status': 'WARN',
                    'message': f'Performance issues: {", ".join(performance_issues)}'
                })
                
        except Exception as e:
            self.results['integration_tests'].append({
                'test': 'Performance',
                'status': 'FAIL',
                'message': f'Performance test failed: {e}'
            })
    
    def print_results(self):
        """Print test results summary."""
        print("\n📊 Test Results Summary")
        print("=" * 60)
        
        # Database tests
        print("\n🗄️  Database Tests:")
        for test in self.results['database_tests']:
            status_icon = "✅" if test['status'] == 'PASS' else "⚠️" if test['status'] == 'WARN' else "❌"
            print(f"  {status_icon} {test['test']}: {test['message']}")
        
        # API tests
        print("\n🌐 API Tests:")
        for test in self.results['api_tests']:
            status_icon = "✅" if test['status'] == 'PASS' else "⏭️" if test['status'] == 'SKIP' else "❌"
            print(f"  {status_icon} {test['test']}: {test['message']}")
        
        # Integration tests
        print("\n🔗 Integration Tests:")
        for test in self.results['integration_tests']:
            status_icon = "✅" if test['status'] == 'PASS' else "⚠️" if test['status'] == 'WARN' else "⏭️" if test['status'] == 'SKIP' else "❌"
            print(f"  {status_icon} {test['test']}: {test['message']}")
        
        # Summary
        total_tests = len(self.results['database_tests']) + len(self.results['api_tests']) + len(self.results['integration_tests'])
        passed_tests = sum(1 for test in self.results['database_tests'] + self.results['api_tests'] + self.results['integration_tests'] if test['status'] == 'PASS')
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Multi-sport integration is working correctly.")
        elif passed_tests > total_tests * 0.8:
            print("👍 Most tests passed! Minor issues to address.")
        else:
            print("⚠️  Several tests failed. Review and fix issues.")

def main():
    """Main function to run integration tests."""
    tester = MultiSportIntegrationTester()
    results = tester.run_all_tests()
    
    # Return exit code based on results
    total_tests = len(results['database_tests']) + len(results['api_tests']) + len(results['integration_tests'])
    passed_tests = sum(1 for test in results['database_tests'] + results['api_tests'] + results['integration_tests'] if test['status'] == 'PASS')
    
    if passed_tests == total_tests:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()
