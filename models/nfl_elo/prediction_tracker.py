"""Prediction tracking system for NFL Elo ratings - 2025 season monitoring."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import os
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .prediction_system import NFLPredictionSystem
from ingest.nfl.data_loader import load_games


class PredictionTracker:
    """Track and monitor prediction accuracy for 2025 season."""
    
    def __init__(self, training_years: List[int] = [2019, 2021, 2022, 2023, 2024]):
        """
        Initialize prediction tracker.
        
        Args:
            training_years: Years to use for training
        """
        self.training_years = training_years
        self.prediction_system = NFLPredictionSystem(training_years)
        self.tracking_data = []
        self.accuracy_history = []
        self.tracking_file = "artifacts/prediction_tracking_2025.json"
        
        # Create artifacts directory if it doesn't exist
        os.makedirs("artifacts", exist_ok=True)
        
        # Load existing tracking data
        self._load_tracking_data()
    
    def _load_tracking_data(self):
        """Load existing tracking data."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    self.tracking_data = data.get('tracking_data', [])
                    self.accuracy_history = data.get('accuracy_history', [])
                print(f"Loaded {len(self.tracking_data)} existing predictions")
            except Exception as e:
                print(f"Error loading tracking data: {e}")
                self.tracking_data = []
                self.accuracy_history = []
        else:
            print("No existing tracking data found")
    
    def _save_tracking_data(self):
        """Save tracking data to file."""
        data = {
            'tracking_data': self.tracking_data,
            'accuracy_history': self.accuracy_history,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved tracking data to {self.tracking_file}")
        except Exception as e:
            print(f"Error saving tracking data: {e}")
    
    def make_week_predictions(self, week: int, season: int = 2025) -> List[Dict[str, Any]]:
        """
        Make predictions for a specific week and track them.
        
        Args:
            week: Week number
            season: Season year
            
        Returns:
            List of predictions with tracking IDs
        """
        print(f"Making predictions for Week {week} of {season} season...")
        
        # Get predictions from system
        predictions = self.prediction_system.predict_week(week, season)
        
        # Add tracking information
        tracked_predictions = []
        for i, pred in enumerate(predictions):
            tracking_id = f"{season}_W{week:02d}_G{i+1:02d}"
            
            tracked_pred = {
                'tracking_id': tracking_id,
                'season': season,
                'week': week,
                'game_number': i + 1,
                'prediction_timestamp': datetime.now().isoformat(),
                'home_team': pred['home_team'],
                'away_team': pred['away_team'],
                'home_win_probability': pred['home_win_probability'],
                'away_win_probability': pred['away_win_probability'],
                'expected_margin': pred['expected_margin'],
                'prediction': pred['prediction'],
                'confidence': pred['confidence'],
                'home_rating': pred['home_rating'],
                'away_rating': pred['away_rating'],
                'actual_winner': None,  # To be filled when results are available
                'actual_home_score': None,
                'actual_away_score': None,
                'actual_margin': None,
                'prediction_correct': None,
                'probability_calibration': None,
                'result_timestamp': None
            }
            
            tracked_predictions.append(tracked_pred)
            self.tracking_data.append(tracked_pred)
        
        # Save tracking data
        self._save_tracking_data()
        
        print(f"Created {len(tracked_predictions)} predictions for Week {week}")
        return tracked_predictions
    
    def update_results(self, week: int, season: int = 2025) -> Dict[str, Any]:
        """
        Update predictions with actual results.
        
        Args:
            week: Week number
            season: Season year
            
        Returns:
            Dictionary with update summary
        """
        print(f"Updating results for Week {week} of {season} season...")
        
        # Load actual game results
        try:
            games = load_games([season])
            week_games = games[games['week'] == week]
            
            if len(week_games) == 0:
                print(f"No games found for Week {week} of {season}")
                return {'updated': 0, 'errors': 0}
            
            updated_count = 0
            error_count = 0
            
            # Update tracking data with results
            for _, game in week_games.iterrows():
                home_team = game['home_team']
                away_team = game['away_team']
                home_score = int(game['home_score'])
                away_score = int(game['away_score'])
                
                # Find matching prediction
                for pred in self.tracking_data:
                    if (pred['season'] == season and 
                        pred['week'] == week and
                        pred['home_team'] == home_team and
                        pred['away_team'] == away_team and
                        pred['actual_winner'] is None):
                        
                        # Update with actual results
                        actual_winner = home_team if home_score > away_score else away_team
                        actual_margin = home_score - away_score
                        prediction_correct = pred['prediction'] == actual_winner
                        
                        # Calculate probability calibration
                        if actual_winner == home_team:
                            probability_calibration = pred['home_win_probability']
                        else:
                            probability_calibration = pred['away_win_probability']
                        
                        pred.update({
                            'actual_winner': actual_winner,
                            'actual_home_score': home_score,
                            'actual_away_score': away_score,
                            'actual_margin': actual_margin,
                            'prediction_correct': prediction_correct,
                            'probability_calibration': probability_calibration,
                            'result_timestamp': datetime.now().isoformat()
                        })
                        
                        updated_count += 1
                        break
                else:
                    error_count += 1
                    print(f"Warning: No prediction found for {away_team} @ {home_team}")
            
            # Calculate week accuracy
            week_predictions = [p for p in self.tracking_data 
                              if p['season'] == season and p['week'] == week and p['prediction_correct'] is not None]
            
            if week_predictions:
                week_accuracy = sum(1 for p in week_predictions if p['prediction_correct']) / len(week_predictions)
                
                # Add to accuracy history
                self.accuracy_history.append({
                    'season': season,
                    'week': week,
                    'accuracy': week_accuracy,
                    'total_games': len(week_predictions),
                    'correct_predictions': sum(1 for p in week_predictions if p['prediction_correct']),
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"Week {week} accuracy: {week_accuracy:.3f} ({sum(1 for p in week_predictions if p['prediction_correct'])}/{len(week_predictions)})")
            
            # Save updated data
            self._save_tracking_data()
            
            return {
                'updated': updated_count,
                'errors': error_count,
                'week_accuracy': week_accuracy if week_predictions else None
            }
            
        except Exception as e:
            print(f"Error updating results: {e}")
            return {'updated': 0, 'errors': 1, 'error': str(e)}
    
    def get_accuracy_summary(self) -> Dict[str, Any]:
        """Get overall accuracy summary."""
        if not self.accuracy_history:
            return {'total_weeks': 0, 'overall_accuracy': 0.0}
        
        total_games = sum(h['total_games'] for h in self.accuracy_history)
        total_correct = sum(h['correct_predictions'] for h in self.accuracy_history)
        overall_accuracy = total_correct / total_games if total_games > 0 else 0.0
        
        return {
            'total_weeks': len(self.accuracy_history),
            'total_games': total_games,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'accuracy_percentage': overall_accuracy * 100,
            'recent_accuracy': self.accuracy_history[-1]['accuracy'] if self.accuracy_history else 0.0
        }
    
    def get_team_performance(self) -> Dict[str, Any]:
        """Get team-specific performance analysis."""
        team_stats = {}
        
        for pred in self.tracking_data:
            if pred['prediction_correct'] is None:
                continue
            
            home_team = pred['home_team']
            away_team = pred['away_team']
            
            # Track home team performance
            if home_team not in team_stats:
                team_stats[home_team] = {'games': 0, 'correct': 0, 'as_home': 0, 'as_away': 0}
            
            team_stats[home_team]['games'] += 1
            team_stats[home_team]['as_home'] += 1
            if pred['prediction_correct'] and pred['prediction'] == home_team:
                team_stats[home_team]['correct'] += 1
            
            # Track away team performance
            if away_team not in team_stats:
                team_stats[away_team] = {'games': 0, 'correct': 0, 'as_home': 0, 'as_away': 0}
            
            team_stats[away_team]['games'] += 1
            team_stats[away_team]['as_away'] += 1
            if pred['prediction_correct'] and pred['prediction'] == away_team:
                team_stats[away_team]['correct'] += 1
        
        # Calculate accuracy for each team
        for team, stats in team_stats.items():
            stats['accuracy'] = stats['correct'] / stats['games'] if stats['games'] > 0 else 0.0
        
        return team_stats
    
    def generate_weekly_report(self, week: int, season: int = 2025) -> str:
        """Generate a weekly prediction report."""
        week_predictions = [p for p in self.tracking_data 
                          if p['season'] == season and p['week'] == week]
        
        if not week_predictions:
            return f"No predictions found for Week {week} of {season}"
        
        report = f"\\n🏈 WEEK {week} PREDICTION REPORT - {season} SEASON\\n"
        report += "=" * 60 + "\\n"
        
        # Summary
        completed_games = [p for p in week_predictions if p['prediction_correct'] is not None]
        if completed_games:
            accuracy = sum(1 for p in completed_games if p['prediction_correct']) / len(completed_games)
            report += f"Accuracy: {accuracy:.3f} ({sum(1 for p in completed_games if p['prediction_correct'])}/{len(completed_games)})\\n"
        else:
            report += "No completed games yet\\n"
        
        report += f"Total predictions: {len(week_predictions)}\\n\\n"
        
        # Game-by-game breakdown
        for pred in week_predictions:
            status = "✅" if pred['prediction_correct'] else "❌" if pred['prediction_correct'] is False else "⏳"
            report += f"{status} {pred['away_team']} @ {pred['home_team']}: "
            report += f"{pred['home_win_probability']:.3f} | "
            report += f"Pred: {pred['prediction']}"
            
            if pred['actual_winner']:
                report += f" | Actual: {pred['actual_winner']}"
                report += f" ({pred['actual_home_score']}-{pred['actual_away_score']})"
            
            report += "\\n"
        
        return report


def test_prediction_tracker():
    """Test the prediction tracking system."""
    print("📊 TESTING PREDICTION TRACKING SYSTEM")
    print("="*80)
    
    # Initialize tracker
    tracker = PredictionTracker()
    
    # Make predictions for Week 1, 2025
    print("\\nMaking predictions for Week 1, 2025...")
    predictions = tracker.make_week_predictions(1, 2025)
    
    print(f"Created {len(predictions)} predictions")
    
    # Show sample predictions
    print("\\nSample predictions:")
    for pred in predictions[:3]:
        print(f"  {pred['away_team']} @ {pred['home_team']}: {pred['home_win_probability']:.3f} | {pred['prediction']}")
    
    # Update with results (if available)
    print("\\nUpdating with results...")
    update_result = tracker.update_results(1, 2025)
    print(f"Updated {update_result['updated']} games, {update_result['errors']} errors")
    
    # Get accuracy summary
    accuracy_summary = tracker.get_accuracy_summary()
    print(f"\\nAccuracy Summary: {accuracy_summary}")
    
    # Generate weekly report
    report = tracker.generate_weekly_report(1, 2025)
    print(report)
    
    return tracker


if __name__ == "__main__":
    tracker = test_prediction_tracker()
