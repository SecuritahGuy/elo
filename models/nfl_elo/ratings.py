"""Core Elo rating system components."""

from dataclasses import dataclass, field
from typing import Dict, Optional
import numpy as np


@dataclass
class TeamRating:
    """Individual team rating."""
    team: str
    elo: float
    
    def __post_init__(self):
        """Validate rating after initialization."""
        if self.elo < 0:
            raise ValueError(f"Rating cannot be negative: {self.elo}")


@dataclass
class OffDefRating:
    """Offense and defense ratings for a team."""
    team: str
    offense: float
    defense: float
    
    def __post_init__(self):
        """Validate ratings after initialization."""
        if self.offense < 0 or self.defense < 0:
            raise ValueError(f"Offense/defense ratings cannot be negative: {self.offense}, {self.defense}")


@dataclass
class RatingBook:
    """Container for all team ratings."""
    base: float
    ratings: Dict[str, TeamRating] = field(default_factory=dict)
    offdef_ratings: Optional[Dict[str, OffDefRating]] = field(default=None)
    
    def get(self, team: str) -> float:
        """Get team's current Elo rating."""
        if team in self.ratings:
            return self.ratings[team].elo
        return self.base
    
    def set(self, team: str, value: float) -> None:
        """Set team's Elo rating."""
        if value < 0:
            raise ValueError(f"Rating cannot be negative: {value}")
        self.ratings[team] = TeamRating(team, value)
    
    def get_offdef(self, team: str) -> tuple[float, float]:
        """Get team's offense and defense ratings."""
        if self.offdef_ratings and team in self.offdef_ratings:
            odr = self.offdef_ratings[team]
            return odr.offense, odr.defense
        # Fallback to base rating for both
        return self.base, self.base
    
    def set_offdef(self, team: str, offense: float, defense: float) -> None:
        """Set team's offense and defense ratings."""
        if offense < 0 or defense < 0:
            raise ValueError(f"Offense/defense ratings cannot be negative: {offense}, {defense}")
        
        if self.offdef_ratings is None:
            self.offdef_ratings = {}
        
        self.offdef_ratings[team] = OffDefRating(team, offense, defense)
    
    def regress_preseason(self, carry: float) -> None:
        """Apply preseason regression to all ratings."""
        if not 0 <= carry <= 1:
            raise ValueError(f"Regression factor must be between 0 and 1: {carry}")
        
        # Regress team ratings
        for team, rating in self.ratings.items():
            rating.elo = (carry * rating.elo) + (1.0 - carry) * self.base
        
        # Regress offense/defense ratings if they exist
        if self.offdef_ratings:
            for team, odr in self.offdef_ratings.items():
                odr.offense = (carry * odr.offense) + (1.0 - carry) * self.base
                odr.defense = (carry * odr.defense) + (1.0 - carry) * self.base
    
    def get_all_teams(self) -> set:
        """Get all teams that have ratings."""
        teams = set(self.ratings.keys())
        if self.offdef_ratings:
            teams.update(self.offdef_ratings.keys())
        return teams
    
    def get_rating_summary(self) -> Dict[str, float]:
        """Get summary of all team ratings."""
        summary = {}
        for team, rating in self.ratings.items():
            summary[team] = rating.elo
        return summary
    
    def get_offdef_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of all offense/defense ratings."""
        if not self.offdef_ratings:
            return {}
        
        summary = {}
        for team, odr in self.offdef_ratings.items():
            summary[team] = {
                "offense": odr.offense,
                "defense": odr.defense
            }
        return summary
