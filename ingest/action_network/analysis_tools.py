"""Analysis tools for Action Network expert performance and pick accuracy."""

import sqlite3
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging


class ActionNetworkAnalyzer:
    """Analyzes Action Network expert performance and pick accuracy."""
    
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        """
        Initialize analyzer.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    def get_top_experts(self, league: str = 'nfl', limit: int = 10, 
                       min_picks: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing experts for a specific league.
        
        Args:
            league: League to analyze ('nfl', 'mlb', etc.)
            limit: Number of top experts to return
            min_picks: Minimum number of picks required
            
        Returns:
            List of top experts with performance metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT e.id, e.an_expert_id, e.name, e.followers, e.is_verified,
                       COUNT(p.id) as total_picks,
                       SUM(CASE WHEN p.result = 'win' THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN p.result = 'loss' THEN 1 ELSE 0 END) as losses,
                       SUM(CASE WHEN p.result = 'pending' THEN 1 ELSE 0 END) as pending,
                       AVG(p.units_net) as avg_units_net,
                       SUM(p.units_net) as total_units_net,
                       AVG(p.odds) as avg_odds,
                       AVG(p.units) as avg_units
                FROM action_network_experts e
                JOIN action_network_picks p ON e.id = p.expert_id
                WHERE p.league_name = ?
                GROUP BY e.id, e.an_expert_id, e.name, e.followers, e.is_verified
                HAVING total_picks >= ?
                ORDER BY total_units_net DESC
                LIMIT ?
            ''', (league, min_picks, limit))
            
            columns = [desc[0] for desc in cursor.description]
            experts = []
            for row in cursor.fetchall():
                expert = dict(zip(columns, row))
                
                # Calculate win rate
                wins = expert['wins'] or 0
                losses = expert['losses'] or 0
                expert['win_rate'] = (wins / max(wins + losses, 1)) * 100
                
                # Calculate ROI
                total_units = expert['total_picks'] * (expert['avg_units'] or 0)
                expert['roi'] = (expert['total_units_net'] / max(total_units, 1)) * 100 if total_units > 0 else 0
                
                experts.append(expert)
            
            return experts
            
        except Exception as e:
            self.logger.error(f"Error getting top experts: {e}")
            return []
        finally:
            conn.close()
    
    def get_expert_trends(self, expert_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Get performance trends for a specific expert over time.
        
        Args:
            expert_name: Name of the expert
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
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
            
            # Get picks from the last N days
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT DATE(created_at) as pick_date, 
                       COUNT(*) as total_picks,
                       SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                       SUM(units_net) as daily_units_net,
                       AVG(odds) as avg_odds
                FROM action_network_picks
                WHERE expert_id = ? AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY pick_date DESC
            ''', (expert_id, start_date))
            
            daily_data = cursor.fetchall()
            
            if not daily_data:
                return {'error': 'No picks found for this period'}
            
            # Calculate trends
            total_picks = sum(row[1] for row in daily_data)
            total_wins = sum(row[2] for row in daily_data)
            total_losses = sum(row[3] for row in daily_data)
            total_units_net = sum(row[4] for row in daily_data)
            
            win_rate = (total_wins / max(total_wins + total_losses, 1)) * 100
            
            # Calculate recent vs overall performance
            recent_days = min(7, len(daily_data))
            recent_wins = sum(row[2] for row in daily_data[:recent_days])
            recent_losses = sum(row[3] for row in daily_data[:recent_days])
            recent_win_rate = (recent_wins / max(recent_wins + recent_losses, 1)) * 100
            
            return {
                'expert_name': expert_name,
                'analysis_period_days': days,
                'total_picks': total_picks,
                'total_wins': total_wins,
                'total_losses': total_losses,
                'win_rate': win_rate,
                'total_units_net': total_units_net,
                'recent_win_rate': recent_win_rate,
                'daily_breakdown': [
                    {
                        'date': row[0],
                        'picks': row[1],
                        'wins': row[2],
                        'losses': row[3],
                        'units_net': row[4],
                        'avg_odds': row[5]
                    } for row in daily_data
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting expert trends: {e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def get_league_performance_summary(self, league: str = 'nfl') -> Dict[str, Any]:
        """
        Get performance summary for a specific league.
        
        Args:
            league: League to analyze
            
        Returns:
            Dictionary with league performance summary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get overall league stats
            cursor.execute('''
                SELECT COUNT(*) as total_picks,
                       SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                       SUM(CASE WHEN result = 'pending' THEN 1 ELSE 0 END) as pending,
                       SUM(units_net) as total_units_net,
                       AVG(units_net) as avg_units_net,
                       AVG(odds) as avg_odds,
                       AVG(units) as avg_units
                FROM action_network_picks
                WHERE league_name = ?
            ''', (league,))
            
            league_stats = cursor.fetchone()
            
            if not league_stats or league_stats[0] == 0:
                return {'error': f'No picks found for {league}'}
            
            total_picks, wins, losses, pending, total_units_net, avg_units_net, avg_odds, avg_units = league_stats
            
            win_rate = (wins / max(wins + losses, 1)) * 100
            
            # Get top performing experts
            top_experts = self.get_top_experts(league, limit=5, min_picks=5)
            
            # Get recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as recent_picks,
                       SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as recent_wins,
                       SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as recent_losses
                FROM action_network_picks
                WHERE league_name = ? AND created_at >= ?
            ''', (league, week_ago))
            
            recent_stats = cursor.fetchone()
            recent_picks, recent_wins, recent_losses = recent_stats or (0, 0, 0)
            recent_win_rate = (recent_wins / max(recent_wins + recent_losses, 1)) * 100 if recent_wins + recent_losses > 0 else 0
            
            return {
                'league': league,
                'total_picks': total_picks,
                'wins': wins,
                'losses': losses,
                'pending': pending,
                'win_rate': win_rate,
                'total_units_net': total_units_net,
                'avg_units_net': avg_units_net,
                'avg_odds': avg_odds,
                'avg_units': avg_units,
                'recent_picks': recent_picks,
                'recent_win_rate': recent_win_rate,
                'top_experts': top_experts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting league performance summary: {e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def get_pick_accuracy_by_type(self, league: str = 'nfl') -> Dict[str, Any]:
        """
        Get pick accuracy broken down by pick type.
        
        Args:
            league: League to analyze
            
        Returns:
            Dictionary with accuracy by pick type
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT pick_type,
                       COUNT(*) as total_picks,
                       SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                       AVG(units_net) as avg_units_net,
                       AVG(odds) as avg_odds
                FROM action_network_picks
                WHERE league_name = ? AND pick_type IS NOT NULL
                GROUP BY pick_type
                ORDER BY total_picks DESC
            ''', (league,))
            
            pick_types = []
            for row in cursor.fetchall():
                pick_type, total_picks, wins, losses, avg_units_net, avg_odds = row
                
                win_rate = (wins / max(wins + losses, 1)) * 100
                
                pick_types.append({
                    'pick_type': pick_type,
                    'total_picks': total_picks,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': win_rate,
                    'avg_units_net': avg_units_net,
                    'avg_odds': avg_odds
                })
            
            return {
                'league': league,
                'pick_types': pick_types
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pick accuracy by type: {e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def get_social_metrics_analysis(self, league: str = 'nfl') -> Dict[str, Any]:
        """
        Analyze social metrics (likes, copies) correlation with performance.
        
        Args:
            league: League to analyze
            
        Returns:
            Dictionary with social metrics analysis
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get picks with social metrics
            cursor.execute('''
                SELECT result, social_likes, social_copies, units_net, odds
                FROM action_network_picks
                WHERE league_name = ? AND social_likes > 0
                ORDER BY social_likes DESC
            ''', (league,))
            
            picks = cursor.fetchall()
            
            if not picks:
                return {'error': 'No picks with social metrics found'}
            
            # Analyze correlation between social metrics and performance
            high_likes = [p for p in picks if p[1] >= 10]  # 10+ likes
            high_copies = [p for p in picks if p[2] >= 5]  # 5+ copies
            
            def calculate_win_rate(pick_list):
                if not pick_list:
                    return 0
                wins = len([p for p in pick_list if p[0] == 'win'])
                losses = len([p for p in pick_list if p[0] == 'loss'])
                return (wins / max(wins + losses, 1)) * 100
            
            return {
                'league': league,
                'total_picks_with_social': len(picks),
                'high_likes_picks': len(high_likes),
                'high_copies_picks': len(high_copies),
                'overall_win_rate': calculate_win_rate(picks),
                'high_likes_win_rate': calculate_win_rate(high_likes),
                'high_copies_win_rate': calculate_win_rate(high_copies),
                'avg_likes': sum(p[1] for p in picks) / len(picks),
                'avg_copies': sum(p[2] for p in picks) / len(picks)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting social metrics analysis: {e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def export_analysis_to_csv(self, league: str = 'nfl', output_file: str = None) -> str:
        """
        Export analysis data to CSV file.
        
        Args:
            league: League to analyze
            output_file: Output file path (optional)
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"artifacts/action_network_analysis_{league}_{timestamp}.csv"
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Export picks data
            query = '''
                SELECT p.an_pick_id, e.name as expert_name, p.play_description,
                       p.pick_type, p.value, p.odds, p.units, p.units_net,
                       p.result, p.created_at, p.trend, p.social_likes, p.social_copies
                FROM action_network_picks p
                JOIN action_network_experts e ON p.expert_id = e.id
                WHERE p.league_name = ?
                ORDER BY p.created_at DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=(league,))
            df.to_csv(output_file, index=False)
            
            self.logger.info(f"Analysis data exported to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error exporting analysis data: {e}")
            raise
        finally:
            conn.close()


def main():
    """Test the analysis tools."""
    analyzer = ActionNetworkAnalyzer()
    
    print("Action Network Analysis Tools Test")
    print("=" * 40)
    
    # Test top experts
    print("\nTop NFL Experts:")
    top_experts = analyzer.get_top_experts('nfl', limit=5)
    for i, expert in enumerate(top_experts, 1):
        print(f"{i}. {expert['name']}: {expert['win_rate']:.1f}% win rate, {expert['total_units_net']:.2f} units")
    
    # Test league summary
    print("\nNFL League Summary:")
    league_summary = analyzer.get_league_performance_summary('nfl')
    if 'error' not in league_summary:
        print(f"Total Picks: {league_summary['total_picks']}")
        print(f"Win Rate: {league_summary['win_rate']:.1f}%")
        print(f"Total Units Net: {league_summary['total_units_net']:.2f}")
        print(f"Recent Picks (7 days): {league_summary['recent_picks']}")
    
    # Test pick accuracy by type
    print("\nPick Accuracy by Type:")
    accuracy_by_type = analyzer.get_pick_accuracy_by_type('nfl')
    if 'error' not in accuracy_by_type:
        for pick_type in accuracy_by_type['pick_types'][:3]:
            print(f"{pick_type['pick_type']}: {pick_type['win_rate']:.1f}% ({pick_type['total_picks']} picks)")
    
    # Test social metrics
    print("\nSocial Metrics Analysis:")
    social_analysis = analyzer.get_social_metrics_analysis('nfl')
    if 'error' not in social_analysis:
        print(f"High Likes Win Rate: {social_analysis['high_likes_win_rate']:.1f}%")
        print(f"High Copies Win Rate: {social_analysis['high_copies_win_rate']:.1f}%")
        print(f"Average Likes: {social_analysis['avg_likes']:.1f}")


if __name__ == "__main__":
    main()
