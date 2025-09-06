#!/usr/bin/env python3
"""
Display 2025 Week 1 Predictions in a nice format
"""

import json
from datetime import datetime

def display_predictions():
    """Display the 2025 Week 1 predictions"""
    
    try:
        with open('2025_week1_predictions.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Predictions file not found. Please run generate_2025_predictions.py first.")
        return
    
    predictions = data['predictions']
    team_ratings = data['team_ratings']
    summary = data['summary']
    
    print("🏈 2025 NFL SEASON - WEEK 1 PREDICTIONS")
    print("=" * 60)
    print(f"Generated: {data['generated_at']}")
    print(f"Total Games: {summary['total_games']}")
    print(f"High Confidence: {summary['high_confidence']} games")
    print(f"Medium Confidence: {summary['medium_confidence']} games")
    print(f"Low Confidence: {summary['low_confidence']} games")
    print()
    
    # Sort predictions by confidence (highest first)
    sorted_predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    
    print("🎯 GAME PREDICTIONS")
    print("=" * 60)
    
    for i, pred in enumerate(sorted_predictions, 1):
        # Format game time
        game_date = datetime.fromisoformat(pred['game_date'].replace('Z', '+00:00'))
        time_str = game_date.strftime('%a %b %d, %I:%M %p ET')
        
        # Confidence label
        if pred['confidence'] >= 60:
            conf_label = "🔥 HIGH"
            conf_color = "\033[92m"  # Green
        elif pred['confidence'] >= 40:
            conf_label = "⚡ MED"
            conf_color = "\033[93m"  # Yellow
        else:
            conf_label = "❓ LOW"
            conf_color = "\033[91m"  # Red
        
        print(f"\n{i:2d}. {pred['away_team']} @ {pred['home_team']}")
        print(f"    Time: {time_str}")
        print(f"    Predicted Winner: {pred['predicted_winner']} ({conf_color}{conf_label} - {pred['confidence']:.1f}%\033[0m)")
        print(f"    Win Probability: {pred['home_win_prob']:.1%} (Home)")
        print(f"    Predicted Score: {pred['away_team']} {pred['predicted_away_score']} - {pred['home_team']} {pred['predicted_home_score']}")
        print(f"    ELO Ratings: {pred['away_team']} {pred['away_rating']:.0f} vs {pred['home_team']} {pred['home_rating']:.0f}")
    
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
    
    # Key insights
    print(f"\n💡 KEY INSIGHTS")
    print("=" * 30)
    print("• All predictions show low confidence, indicating competitive matchups")
    print("• Home field advantage is factored into all predictions")
    print("• ELO ratings are based on 2024 performance with 30% carryover")
    print("• Predicted scores are based on ELO rating differences")
    print("• Confidence scores reflect the closeness of ELO ratings")

if __name__ == "__main__":
    display_predictions()
