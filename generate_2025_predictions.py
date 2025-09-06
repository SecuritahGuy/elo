#!/usr/bin/env python3
"""
Generate 2025 NFL Season Week 1 Predictions
Creates ELO ratings and predictions for the 2025 season
"""

import sys
import os
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

# Add the models directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'models', 'nfl_elo'))

class NFL2025Predictor:
    """Generate 2025 NFL season predictions using ELO system"""
    
    def __init__(self, db_path='nfl_elo.db'):
        self.db_path = db_path
        self.base_rating = 1500
        self.k_factor = 20
        self.hfa = 55  # Home field advantage
        self.scale = 400
        self.preseason_regress = 0.30  # 30% carryover from previous season
        
    def initialize_database(self):
        """Initialize the database with necessary tables"""
        print("Initializing database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create team_ratings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                rating REAL NOT NULL,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                win_pct REAL DEFAULT 0.0,
                rating_change REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                home_win BOOLEAN,
                game_date TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_rating REAL NOT NULL,
                away_rating REAL NOT NULL,
                home_win_prob REAL NOT NULL,
                predicted_winner TEXT NOT NULL,
                confidence REAL NOT NULL,
                predicted_home_score INTEGER,
                predicted_away_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
    
    def get_2025_week1_games(self):
        """Get Week 1 games for 2025 season (mock data for now)"""
        print("Generating 2025 Week 1 games...")
        
        # NFL teams
        teams = ['PHI', 'DAL', 'SF', 'BUF', 'BAL', 'KC', 'GB', 'MIN', 'DET', 'CIN', 
                'LAR', 'TB', 'MIA', 'NYJ', 'NE', 'PIT', 'ATL', 'CAR', 'NO', 'ARI',
                'SEA', 'DEN', 'LAC', 'LV', 'HOU', 'IND', 'JAX', 'TEN', 'CHI', 'NYG',
                'WAS', 'CLE']
        
        # Create realistic Week 1 matchups
        week1_games = [
            # Thursday Night Football
            {'home_team': 'KC', 'away_team': 'BAL', 'game_date': '2025-09-05T20:20:00Z'},
            
            # Sunday Games
            {'home_team': 'PHI', 'away_team': 'DAL', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'BUF', 'away_team': 'NYJ', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'SF', 'away_team': 'LAR', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'GB', 'away_team': 'MIN', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'DET', 'away_team': 'CHI', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'CIN', 'away_team': 'CLE', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'TB', 'away_team': 'ATL', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'MIA', 'away_team': 'NE', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'PIT', 'away_team': 'BAL', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'CAR', 'away_team': 'NO', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'ARI', 'away_team': 'SEA', 'game_date': '2025-09-07T13:00:00Z'},
            {'home_team': 'DEN', 'away_team': 'LAC', 'game_date': '2025-09-07T16:05:00Z'},
            {'home_team': 'LV', 'away_team': 'HOU', 'game_date': '2025-09-07T16:05:00Z'},
            {'home_team': 'IND', 'away_team': 'JAX', 'game_date': '2025-09-07T16:25:00Z'},
            {'home_team': 'TEN', 'away_team': 'NYG', 'game_date': '2025-09-07T16:25:00Z'},
            
            # Sunday Night Football
            {'home_team': 'WAS', 'away_team': 'DAL', 'game_date': '2025-09-07T20:20:00Z'},
            
            # Monday Night Football
            {'home_team': 'LAR', 'away_team': 'SF', 'game_date': '2025-09-08T20:15:00Z'},
        ]
        
        # Add game IDs and season info
        for i, game in enumerate(week1_games, 1):
            game['id'] = i
            game['season'] = 2025
            game['week'] = 1
            game['completed'] = False
        
        return week1_games
    
    def calculate_preseason_ratings(self):
        """Calculate preseason ratings based on 2024 final ratings with regression"""
        print("Calculating preseason 2025 ratings...")
        
        # Mock 2024 final ratings (in a real scenario, these would come from our 2024 data)
        final_2024_ratings = {
            'KC': 1650, 'BUF': 1620, 'SF': 1600, 'BAL': 1580, 'DAL': 1570,
            'PHI': 1560, 'GB': 1550, 'DET': 1540, 'MIA': 1530, 'LAR': 1520,
            'TB': 1510, 'CIN': 1500, 'PIT': 1490, 'CLE': 1480, 'HOU': 1470,
            'IND': 1460, 'JAX': 1450, 'TEN': 1440, 'ATL': 1430, 'NO': 1420,
            'CAR': 1410, 'ARI': 1400, 'SEA': 1390, 'DEN': 1380, 'LAC': 1370,
            'LV': 1360, 'NYJ': 1350, 'NE': 1340, 'CHI': 1330, 'NYG': 1320,
            'WAS': 1310, 'MIN': 1300
        }
        
        # Apply preseason regression (30% carryover, 70% regression to mean)
        mean_rating = np.mean(list(final_2024_ratings.values()))
        preseason_ratings = {}
        
        for team, rating in final_2024_ratings.items():
            preseason_ratings[team] = (self.preseason_regress * rating + 
                                     (1 - self.preseason_regress) * mean_rating)
        
        return preseason_ratings
    
    def calculate_win_probability(self, home_rating, away_rating):
        """Calculate home team win probability"""
        rating_diff = home_rating - away_rating + self.hfa
        return 1 / (1 + 10 ** (-rating_diff / self.scale))
    
    def calculate_predicted_scores(self, home_rating, away_rating):
        """Calculate predicted scores based on ELO ratings"""
        # Simple model: average NFL score is ~23 points
        avg_score = 23
        rating_diff = home_rating - away_rating
        
        # Each 100 ELO points difference = ~2.5 points in score
        score_diff = rating_diff / 100 * 2.5
        
        home_score = round(avg_score + score_diff / 2)
        away_score = round(avg_score - score_diff / 2)
        
        # Ensure minimum scores
        home_score = max(10, home_score)
        away_score = max(10, away_score)
        
        return home_score, away_score
    
    def generate_predictions(self, games, team_ratings):
        """Generate predictions for all games"""
        print("Generating predictions...")
        
        predictions = []
        
        for game in games:
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Get team ratings
            home_rating = team_ratings.get(home_team, self.base_rating)
            away_rating = team_ratings.get(away_team, self.base_rating)
            
            # Calculate win probability
            home_win_prob = self.calculate_win_probability(home_rating, away_rating)
            
            # Determine predicted winner
            predicted_winner = home_team if home_win_prob > 0.5 else away_team
            
            # Calculate confidence (0-100 scale)
            confidence = abs(home_win_prob - 0.5) * 200
            
            # Calculate predicted scores
            home_score, away_score = self.calculate_predicted_scores(home_rating, away_rating)
            
            prediction = {
                'season': game['season'],
                'week': game['week'],
                'home_team': home_team,
                'away_team': away_team,
                'home_rating': round(home_rating, 1),
                'away_rating': round(away_rating, 1),
                'home_win_prob': round(home_win_prob, 3),
                'predicted_winner': predicted_winner,
                'confidence': round(confidence, 1),
                'predicted_home_score': home_score,
                'predicted_away_score': away_score,
                'game_date': game['game_date'],
                'completed': game['completed']
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def store_data(self, games, team_ratings, predictions):
        """Store all data in the database"""
        print("Storing data in database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store games
        for game in games:
            cursor.execute('''
                INSERT INTO games (season, week, home_team, away_team, game_date, completed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (game['season'], game['week'], game['home_team'], game['away_team'], 
                  game['game_date'], game['completed']))
        
        # Store team ratings
        for team, rating in team_ratings.items():
            cursor.execute('''
                INSERT INTO team_ratings (team, season, week, rating, wins, losses, win_pct, rating_change)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (team, 2025, 0, rating, 0, 0, 0.0, 0.0))
        
        # Store predictions
        for pred in predictions:
            cursor.execute('''
                INSERT INTO predictions (season, week, home_team, away_team, home_rating, away_rating,
                                       home_win_prob, predicted_winner, confidence, predicted_home_score, predicted_away_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pred['season'], pred['week'], pred['home_team'], pred['away_team'],
                  pred['home_rating'], pred['away_rating'], pred['home_win_prob'],
                  pred['predicted_winner'], pred['confidence'], pred['predicted_home_score'],
                  pred['predicted_away_score']))
        
        conn.commit()
        conn.close()
        print("✅ Data stored in database")
    
    def run_prediction(self):
        """Run the complete prediction process"""
        print("🏈 Generating 2025 NFL Season Week 1 Predictions")
        print("=" * 60)
        
        # Initialize database
        self.initialize_database()
        
        # Get Week 1 games
        games = self.get_2025_week1_games()
        print(f"✅ Generated {len(games)} Week 1 games")
        
        # Calculate preseason ratings
        team_ratings = self.calculate_preseason_ratings()
        print(f"✅ Calculated ratings for {len(team_ratings)} teams")
        
        # Generate predictions
        predictions = self.generate_predictions(games, team_ratings)
        print(f"✅ Generated {len(predictions)} predictions")
        
        # Store data
        self.store_data(games, team_ratings, predictions)
        
        # Display results
        self.display_results(predictions, team_ratings)
        
        return predictions, team_ratings
    
    def display_results(self, predictions, team_ratings):
        """Display the prediction results"""
        print(f"\n🎯 2025 NFL SEASON - WEEK 1 PREDICTIONS")
        print("=" * 60)
        
        # Sort predictions by confidence (highest first)
        sorted_predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
        
        for i, pred in enumerate(sorted_predictions, 1):
            confidence_label = "🔥 HIGH" if pred['confidence'] >= 60 else "⚡ MED" if pred['confidence'] >= 40 else "❓ LOW"
            
            print(f"\n{i:2d}. {pred['away_team']} @ {pred['home_team']}")
            print(f"    Predicted Winner: {pred['predicted_winner']} ({confidence_label} - {pred['confidence']:.1f}%)")
            print(f"    Win Probability: {pred['home_win_prob']:.1%} (Home)")
            print(f"    Predicted Score: {pred['away_team']} {pred['predicted_away_score']} - {pred['home_team']} {pred['predicted_home_score']}")
            print(f"    ELO Ratings: {pred['away_team']} {pred['away_rating']} vs {pred['home_team']} {pred['home_rating']}")
        
        # Top 10 team ratings
        print(f"\n🏆 TOP 10 TEAM RATINGS (Preseason 2025)")
        print("=" * 50)
        sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
        for i, (team, rating) in enumerate(sorted_teams[:10], 1):
            print(f"{i:2d}. {team}: {rating:.0f}")
        
        # Confidence breakdown
        high_conf = [p for p in predictions if p['confidence'] >= 60]
        med_conf = [p for p in predictions if 40 <= p['confidence'] < 60]
        low_conf = [p for p in predictions if p['confidence'] < 40]
        
        print(f"\n📊 CONFIDENCE BREAKDOWN")
        print("=" * 30)
        print(f"High Confidence (≥60%): {len(high_conf)} games")
        print(f"Medium Confidence (40-60%): {len(med_conf)} games")
        print(f"Low Confidence (<40%): {len(low_conf)} games")
        
        # Save to JSON for dashboard
        self.save_predictions_json(predictions, team_ratings)
    
    def save_predictions_json(self, predictions, team_ratings):
        """Save predictions to JSON file for dashboard consumption"""
        output_data = {
            'season': 2025,
            'week': 1,
            'generated_at': datetime.now().isoformat(),
            'predictions': predictions,
            'team_ratings': team_ratings,
            'summary': {
                'total_games': len(predictions),
                'high_confidence': len([p for p in predictions if p['confidence'] >= 60]),
                'medium_confidence': len([p for p in predictions if 40 <= p['confidence'] < 60]),
                'low_confidence': len([p for p in predictions if p['confidence'] < 40])
            }
        }
        
        with open('2025_week1_predictions.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n💾 Predictions saved to: 2025_week1_predictions.json")

def main():
    """Main execution function"""
    predictor = NFL2025Predictor()
    predictions, team_ratings = predictor.run_prediction()
    
    print(f"\n✅ Prediction generation completed successfully!")
    print(f"Generated {len(predictions)} predictions for Week 1 of the 2025 season")

if __name__ == "__main__":
    main()
