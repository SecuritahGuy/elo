"""NFL Stadium database with coordinates and weather sensitivity."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class StadiumInfo:
    """Information about an NFL stadium."""
    name: str
    team: str
    city: str
    state: str
    latitude: float
    longitude: float
    elevation: float
    stadium_type: str  # 'outdoor', 'dome', 'retractable'
    weather_sensitivity: str  # 'high', 'medium', 'low', 'none'
    capacity: int
    surface: str  # 'grass', 'turf', 'hybrid'


class StadiumDatabase:
    """Database of NFL stadiums with weather information."""
    
    def __init__(self):
        """Initialize the stadium database."""
        self.stadiums = self._create_stadium_database()
    
    def _create_stadium_database(self) -> Dict[str, StadiumInfo]:
        """Create the comprehensive NFL stadium database."""
        stadiums = {}
        
        # AFC East
        stadiums['BUF'] = StadiumInfo(
            name="Highmark Stadium", team="BUF", city="Orchard Park", state="NY",
            latitude=42.7738, longitude=-78.7869, elevation=200,
            stadium_type="outdoor", weather_sensitivity="high", capacity=71608, surface="grass"
        )
        stadiums['MIA'] = StadiumInfo(
            name="Hard Rock Stadium", team="MIA", city="Miami Gardens", state="FL",
            latitude=25.9581, longitude=-80.2389, elevation=5,
            stadium_type="outdoor", weather_sensitivity="medium", capacity=65326, surface="grass"
        )
        stadiums['NE'] = StadiumInfo(
            name="Gillette Stadium", team="NE", city="Foxborough", state="MA",
            latitude=42.0909, longitude=-71.2643, elevation=50,
            stadium_type="outdoor", weather_sensitivity="high", capacity=65878, surface="grass"
        )
        stadiums['NYJ'] = StadiumInfo(
            name="MetLife Stadium", team="NYJ", city="East Rutherford", state="NJ",
            latitude=40.8138, longitude=-74.0744, elevation=7,
            stadium_type="outdoor", weather_sensitivity="high", capacity=82500, surface="turf"
        )
        
        # AFC North
        stadiums['BAL'] = StadiumInfo(
            name="M&T Bank Stadium", team="BAL", city="Baltimore", state="MD",
            latitude=39.2780, longitude=-76.6227, elevation=15,
            stadium_type="outdoor", weather_sensitivity="high", capacity=71008, surface="grass"
        )
        stadiums['CIN'] = StadiumInfo(
            name="Paycor Stadium", team="CIN", city="Cincinnati", state="OH",
            latitude=39.0950, longitude=-84.5160, elevation=150,
            stadium_type="outdoor", weather_sensitivity="high", capacity=65515, surface="turf"
        )
        stadiums['CLE'] = StadiumInfo(
            name="FirstEnergy Stadium", team="CLE", city="Cleveland", state="OH",
            latitude=41.5061, longitude=-81.6996, elevation=200,
            stadium_type="outdoor", weather_sensitivity="high", capacity=67431, surface="grass"
        )
        stadiums['PIT'] = StadiumInfo(
            name="Acrisure Stadium", team="PIT", city="Pittsburgh", state="PA",
            latitude=40.4468, longitude=-80.0158, elevation=230,
            stadium_type="outdoor", weather_sensitivity="high", capacity=68400, surface="grass"
        )
        
        # AFC South
        stadiums['HOU'] = StadiumInfo(
            name="NRG Stadium", team="HOU", city="Houston", state="TX",
            latitude=29.6847, longitude=-95.4107, elevation=10,
            stadium_type="retractable", weather_sensitivity="low", capacity=72220, surface="turf"
        )
        stadiums['IND'] = StadiumInfo(
            name="Lucas Oil Stadium", team="IND", city="Indianapolis", state="IN",
            latitude=39.7601, longitude=-86.1639, elevation=220,
            stadium_type="dome", weather_sensitivity="none", capacity=67000, surface="turf"
        )
        stadiums['JAX'] = StadiumInfo(
            name="TIAA Bank Field", team="JAX", city="Jacksonville", state="FL",
            latitude=30.3239, longitude=-81.6373, elevation=5,
            stadium_type="outdoor", weather_sensitivity="medium", capacity=69132, surface="grass"
        )
        stadiums['TEN'] = StadiumInfo(
            name="Nissan Stadium", team="TEN", city="Nashville", state="TN",
            latitude=36.1664, longitude=-86.7714, elevation=130,
            stadium_type="outdoor", weather_sensitivity="medium", capacity=69143, surface="grass"
        )
        
        # AFC West
        stadiums['DEN'] = StadiumInfo(
            name="Empower Field at Mile High", team="DEN", city="Denver", state="CO",
            latitude=39.7439, longitude=-105.0200, elevation=1609,
            stadium_type="outdoor", weather_sensitivity="high", capacity=76125, surface="grass"
        )
        stadiums['KC'] = StadiumInfo(
            name="Arrowhead Stadium", team="KC", city="Kansas City", state="MO",
            latitude=39.0489, longitude=-94.4839, elevation=250,
            stadium_type="outdoor", weather_sensitivity="high", capacity=76416, surface="grass"
        )
        stadiums['LV'] = StadiumInfo(
            name="Allegiant Stadium", team="LV", city="Las Vegas", state="NV",
            latitude=36.0909, longitude=-115.1836, elevation=610,
            stadium_type="dome", weather_sensitivity="none", capacity=65000, surface="turf"
        )
        stadiums['LAC'] = StadiumInfo(
            name="SoFi Stadium", team="LAC", city="Inglewood", state="CA",
            latitude=33.9533, longitude=-118.3390, elevation=30,
            stadium_type="dome", weather_sensitivity="none", capacity=70240, surface="turf"
        )
        
        # NFC East
        stadiums['DAL'] = StadiumInfo(
            name="AT&T Stadium", team="DAL", city="Arlington", state="TX",
            latitude=32.7473, longitude=-97.0945, elevation=150,
            stadium_type="retractable", weather_sensitivity="low", capacity=80000, surface="turf"
        )
        stadiums['NYG'] = StadiumInfo(
            name="MetLife Stadium", team="NYG", city="East Rutherford", state="NJ",
            latitude=40.8138, longitude=-74.0744, elevation=7,
            stadium_type="outdoor", weather_sensitivity="high", capacity=82500, surface="turf"
        )
        stadiums['PHI'] = StadiumInfo(
            name="Lincoln Financial Field", team="PHI", city="Philadelphia", state="PA",
            latitude=39.9008, longitude=-75.1674, elevation=10,
            stadium_type="outdoor", weather_sensitivity="high", capacity=69596, surface="grass"
        )
        stadiums['WAS'] = StadiumInfo(
            name="FedExField", team="WAS", city="Landover", state="MD",
            latitude=38.9077, longitude=-76.8644, elevation=50,
            stadium_type="outdoor", weather_sensitivity="high", capacity=82000, surface="grass"
        )
        
        # NFC North
        stadiums['CHI'] = StadiumInfo(
            name="Soldier Field", team="CHI", city="Chicago", state="IL",
            latitude=41.8625, longitude=-87.6167, elevation=180,
            stadium_type="outdoor", weather_sensitivity="high", capacity=61500, surface="grass"
        )
        stadiums['DET'] = StadiumInfo(
            name="Ford Field", team="DET", city="Detroit", state="MI",
            latitude=42.3400, longitude=-83.0456, elevation=190,
            stadium_type="dome", weather_sensitivity="none", capacity=65000, surface="turf"
        )
        stadiums['GB'] = StadiumInfo(
            name="Lambeau Field", team="GB", city="Green Bay", state="WI",
            latitude=44.5013, longitude=-88.0622, elevation=195,
            stadium_type="outdoor", weather_sensitivity="high", capacity=81441, surface="grass"
        )
        stadiums['MIN'] = StadiumInfo(
            name="U.S. Bank Stadium", team="MIN", city="Minneapolis", state="MN",
            latitude=44.9739, longitude=-93.2581, elevation=250,
            stadium_type="dome", weather_sensitivity="none", capacity=66655, surface="turf"
        )
        
        # NFC South
        stadiums['ATL'] = StadiumInfo(
            name="Mercedes-Benz Stadium", team="ATL", city="Atlanta", state="GA",
            latitude=33.7550, longitude=-84.4010, elevation=320,
            stadium_type="dome", weather_sensitivity="none", capacity=71000, surface="turf"
        )
        stadiums['CAR'] = StadiumInfo(
            name="Bank of America Stadium", team="CAR", city="Charlotte", state="NC",
            latitude=35.2258, longitude=-80.8528, elevation=200,
            stadium_type="outdoor", weather_sensitivity="medium", capacity=75525, surface="grass"
        )
        stadiums['NO'] = StadiumInfo(
            name="Caesars Superdome", team="NO", city="New Orleans", state="LA",
            latitude=29.9508, longitude=-90.0811, elevation=5,
            stadium_type="dome", weather_sensitivity="none", capacity=73000, surface="turf"
        )
        stadiums['TB'] = StadiumInfo(
            name="Raymond James Stadium", team="TB", city="Tampa", state="FL",
            latitude=27.9759, longitude=-82.5033, elevation=10,
            stadium_type="outdoor", weather_sensitivity="medium", capacity=65890, surface="grass"
        )
        
        # NFC West
        stadiums['ARI'] = StadiumInfo(
            name="State Farm Stadium", team="ARI", city="Glendale", state="AZ",
            latitude=33.5275, longitude=-112.2625, elevation=350,
            stadium_type="retractable", weather_sensitivity="low", capacity=63400, surface="turf"
        )
        stadiums['LAR'] = StadiumInfo(
            name="SoFi Stadium", team="LAR", city="Inglewood", state="CA",
            latitude=33.9533, longitude=-118.3390, elevation=30,
            stadium_type="dome", weather_sensitivity="none", capacity=70240, surface="turf"
        )
        stadiums['SF'] = StadiumInfo(
            name="Levi's Stadium", team="SF", city="Santa Clara", state="CA",
            latitude=37.4030, longitude=-121.9700, elevation=20,
            stadium_type="outdoor", weather_sensitivity="medium", capacity=68500, surface="grass"
        )
        stadiums['SEA'] = StadiumInfo(
            name="Lumen Field", team="SEA", city="Seattle", state="WA",
            latitude=47.5952, longitude=-122.3316, elevation=5,
            stadium_type="outdoor", weather_sensitivity="high", capacity=68000, surface="turf"
        )
        
        return stadiums
    
    def get_stadium(self, team: str) -> Optional[StadiumInfo]:
        """Get stadium information for a team."""
        return self.stadiums.get(team)
    
    def get_all_stadiums(self) -> List[StadiumInfo]:
        """Get all stadium information."""
        return list(self.stadiums.values())
    
    def get_outdoor_stadiums(self) -> List[StadiumInfo]:
        """Get all outdoor stadiums (weather-sensitive)."""
        return [stadium for stadium in self.stadiums.values() 
                if stadium.stadium_type == "outdoor"]
    
    def get_dome_stadiums(self) -> List[StadiumInfo]:
        """Get all dome stadiums (weather-insensitive)."""
        return [stadium for stadium in self.stadiums.values() 
                if stadium.stadium_type == "dome"]
    
    def get_weather_sensitive_stadiums(self) -> List[StadiumInfo]:
        """Get all weather-sensitive stadiums."""
        return [stadium for stadium in self.stadiums.values() 
                if stadium.weather_sensitivity in ["high", "medium"]]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert stadium database to DataFrame."""
        data = []
        for team, stadium in self.stadiums.items():
            data.append({
                'team': team,
                'name': stadium.name,
                'city': stadium.city,
                'state': stadium.state,
                'latitude': stadium.latitude,
                'longitude': stadium.longitude,
                'elevation': stadium.elevation,
                'stadium_type': stadium.stadium_type,
                'weather_sensitivity': stadium.weather_sensitivity,
                'capacity': stadium.capacity,
                'surface': stadium.surface
            })
        return pd.DataFrame(data)
    
    def get_stadium_coordinates(self, team: str) -> Optional[tuple]:
        """Get latitude and longitude for a team's stadium."""
        stadium = self.get_stadium(team)
        if stadium:
            return (stadium.latitude, stadium.longitude)
        return None
    
    def is_weather_sensitive(self, team: str) -> bool:
        """Check if a team's stadium is weather-sensitive."""
        stadium = self.get_stadium(team)
        if stadium:
            return stadium.weather_sensitivity != "none"
        return False


def create_stadium_database() -> StadiumDatabase:
    """Create and return a new stadium database instance."""
    return StadiumDatabase()
