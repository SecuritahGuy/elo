"""Main integration script for Action Network data collection and analysis."""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ingest.action_network.data_collector import ActionNetworkCollector
from ingest.action_network.analysis_tools import ActionNetworkAnalyzer
from ingest.action_network.team_mapper import ActionNetworkTeamMapper


def setup_logging(level=logging.INFO):
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('artifacts/action_network.log'),
            logging.StreamHandler()
        ]
    )


def collect_data(date=None, expert_picks=True, all_picks=True):
    """
    Collect Action Network data.
    
    Args:
        date: Date in YYYYMMDD format (defaults to today)
        expert_picks: Whether to collect expert picks
        all_picks: Whether to collect all picks data
    """
    print("Starting Action Network data collection...")
    
    collector = ActionNetworkCollector()
    results = {}
    
    if expert_picks:
        print("Collecting expert picks...")
        results['expert_picks'] = collector.collect_expert_picks()
        print(f"Expert picks: {results['expert_picks']}")
    
    if all_picks:
        print("Collecting all picks...")
        results['all_picks'] = collector.collect_all_picks(date)
        print(f"All picks: {results['all_picks']}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"artifacts/collection_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Collection results saved to {results_file}")
    return results


def analyze_data(league='nfl', export_csv=False):
    """
    Analyze Action Network data.
    
    Args:
        league: League to analyze
        export_csv: Whether to export data to CSV
    """
    print(f"Analyzing Action Network data for {league.upper()}...")
    
    analyzer = ActionNetworkAnalyzer()
    mapper = ActionNetworkTeamMapper()
    
    # Get top experts
    print("\nTop Experts:")
    top_experts = analyzer.get_top_experts(league, limit=10)
    for i, expert in enumerate(top_experts, 1):
        print(f"{i:2d}. {expert['name']:<20} | "
              f"Win Rate: {expert['win_rate']:5.1f}% | "
              f"Units: {expert['total_units_net']:6.2f} | "
              f"Picks: {expert['total_picks']:3d}")
    
    # Get league summary
    print(f"\n{league.upper()} League Summary:")
    league_summary = analyzer.get_league_performance_summary(league)
    if 'error' not in league_summary:
        print(f"Total Picks: {league_summary['total_picks']:,}")
        print(f"Win Rate: {league_summary['win_rate']:.1f}%")
        print(f"Total Units Net: {league_summary['total_units_net']:,.2f}")
        print(f"Average Units Net: {league_summary['avg_units_net']:.2f}")
        print(f"Recent Picks (7 days): {league_summary['recent_picks']}")
        print(f"Recent Win Rate: {league_summary['recent_win_rate']:.1f}%")
    
    # Get pick accuracy by type
    print(f"\nPick Accuracy by Type ({league.upper()}):")
    accuracy_by_type = analyzer.get_pick_accuracy_by_type(league)
    if 'error' not in accuracy_by_type:
        for pick_type in accuracy_by_type['pick_types'][:5]:
            print(f"{pick_type['pick_type']:<15} | "
                  f"Win Rate: {pick_type['win_rate']:5.1f}% | "
                  f"Picks: {pick_type['total_picks']:3d} | "
                  f"Units: {pick_type['avg_units_net']:6.2f}")
    
    # Get social metrics analysis
    print(f"\nSocial Metrics Analysis ({league.upper()}):")
    social_analysis = analyzer.get_social_metrics_analysis(league)
    if 'error' not in social_analysis:
        print(f"Picks with Social Data: {social_analysis['total_picks_with_social']:,}")
        print(f"High Likes Picks: {social_analysis['high_likes_picks']:,}")
        print(f"High Copies Picks: {social_analysis['high_copies_picks']:,}")
        print(f"Overall Win Rate: {social_analysis['overall_win_rate']:.1f}%")
        print(f"High Likes Win Rate: {social_analysis['high_likes_win_rate']:.1f}%")
        print(f"High Copies Win Rate: {social_analysis['high_copies_win_rate']:.1f}%")
        print(f"Average Likes: {social_analysis['avg_likes']:.1f}")
        print(f"Average Copies: {social_analysis['avg_copies']:.1f}")
    
    # Get team mappings
    print(f"\nNFL Team Mappings:")
    nfl_mapping = mapper.map_nfl_teams_to_standard()
    print(f"Total NFL teams mapped: {len(nfl_mapping)}")
    for an_id, team_name in list(nfl_mapping.items())[:5]:
        print(f"  AN ID {an_id}: {team_name}")
    
    # Export to CSV if requested
    if export_csv:
        print(f"\nExporting {league.upper()} data to CSV...")
        csv_file = analyzer.export_analysis_to_csv(league)
        print(f"Data exported to: {csv_file}")
    
    return {
        'top_experts': top_experts,
        'league_summary': league_summary,
        'accuracy_by_type': accuracy_by_type,
        'social_analysis': social_analysis
    }


def get_expert_details(expert_name, days=30):
    """
    Get detailed analysis for a specific expert.
    
    Args:
        expert_name: Name of the expert
        days: Number of days to analyze
    """
    print(f"Getting detailed analysis for expert: {expert_name}")
    
    analyzer = ActionNetworkAnalyzer()
    mapper = ActionNetworkTeamMapper()
    
    # Get expert trends
    trends = analyzer.get_expert_trends(expert_name, days)
    if 'error' in trends:
        print(f"Error: {trends['error']}")
        return
    
    print(f"\nExpert: {trends['expert_name']}")
    print(f"Analysis Period: {trends['analysis_period_days']} days")
    print(f"Total Picks: {trends['total_picks']}")
    print(f"Wins: {trends['total_wins']}")
    print(f"Losses: {trends['total_losses']}")
    print(f"Win Rate: {trends['win_rate']:.1f}%")
    print(f"Total Units Net: {trends['total_units_net']:.2f}")
    print(f"Recent Win Rate (7 days): {trends['recent_win_rate']:.1f}%")
    
    # Get NFL-specific performance
    nfl_performance = mapper.get_expert_nfl_performance(expert_name)
    if 'error' not in nfl_performance:
        print(f"\nNFL-Specific Performance:")
        print(f"NFL Picks: {nfl_performance['total_picks']}")
        print(f"NFL Win Rate: {nfl_performance['win_rate']:.1f}%")
        print(f"NFL Units Net: {nfl_performance['total_units_net']:.2f}")
        print(f"Average Odds: {nfl_performance['avg_odds']:.0f}")
        print(f"Average Units: {nfl_performance['avg_units']:.2f}")
    
    return trends


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='Action Network Integration Tool')
    parser.add_argument('--action', choices=['collect', 'analyze', 'expert', 'all'], 
                       default='all', help='Action to perform')
    parser.add_argument('--league', default='nfl', 
                       help='League to analyze (nfl, mlb, etc.)')
    parser.add_argument('--date', help='Date in YYYYMMDD format (defaults to today)')
    parser.add_argument('--expert-name', help='Expert name for detailed analysis')
    parser.add_argument('--days', type=int, default=30, 
                       help='Number of days for expert analysis')
    parser.add_argument('--export-csv', action='store_true', 
                       help='Export analysis data to CSV')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Create artifacts directory
    Path("artifacts").mkdir(exist_ok=True)
    
    try:
        if args.action in ['collect', 'all']:
            collect_data(args.date)
        
        if args.action in ['analyze', 'all']:
            analyze_data(args.league, args.export_csv)
        
        if args.action == 'expert' and args.expert_name:
            get_expert_details(args.expert_name, args.days)
        
        print("\nAction Network integration completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Integration failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
