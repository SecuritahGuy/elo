"""Team abbreviation mapping for NFL data consistency."""

from typing import Dict, Optional


# Mapping from various team abbreviations to standard stadium database abbreviations
TEAM_MAPPING = {
    # Common variations
    'LA': 'LAR',  # Los Angeles Rams
    'LAR': 'LAR',  # Los Angeles Rams (standard)
    'LAC': 'LAC',  # Los Angeles Chargers
    'NE': 'NE',    # New England Patriots
    'BUF': 'BUF',  # Buffalo Bills
    'MIA': 'MIA',  # Miami Dolphins
    'NYJ': 'NYJ',  # New York Jets
    'NYG': 'NYG',  # New York Giants
    'BAL': 'BAL',  # Baltimore Ravens
    'CIN': 'CIN',  # Cincinnati Bengals
    'CLE': 'CLE',  # Cleveland Browns
    'PIT': 'PIT',  # Pittsburgh Steelers
    'HOU': 'HOU',  # Houston Texans
    'IND': 'IND',  # Indianapolis Colts
    'JAX': 'JAX',  # Jacksonville Jaguars
    'TEN': 'TEN',  # Tennessee Titans
    'DEN': 'DEN',  # Denver Broncos
    'KC': 'KC',    # Kansas City Chiefs
    'LV': 'LV',    # Las Vegas Raiders
    'DAL': 'DAL',  # Dallas Cowboys
    'PHI': 'PHI',  # Philadelphia Eagles
    'WAS': 'WAS',  # Washington Commanders
    'CHI': 'CHI',  # Chicago Bears
    'DET': 'DET',  # Detroit Lions
    'GB': 'GB',    # Green Bay Packers
    'MIN': 'MIN',  # Minnesota Vikings
    'ATL': 'ATL',  # Atlanta Falcons
    'CAR': 'CAR',  # Carolina Panthers
    'NO': 'NO',    # New Orleans Saints
    'TB': 'TB',    # Tampa Bay Buccaneers
    'ARI': 'ARI',  # Arizona Cardinals
    'SF': 'SF',    # San Francisco 49ers
    'SEA': 'SEA',  # Seattle Seahawks
}


def normalize_team_abbreviation(team: str) -> str:
    """
    Normalize team abbreviation to match stadium database.
    
    Args:
        team: Team abbreviation from games data
        
    Returns:
        Normalized team abbreviation for stadium database lookup
    """
    return TEAM_MAPPING.get(team.upper(), team.upper())


def get_team_mapping() -> Dict[str, str]:
    """Get the complete team mapping dictionary."""
    return TEAM_MAPPING.copy()
