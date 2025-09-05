"""Configuration system for NFL Elo ratings."""

from pydantic import BaseModel, Field
from typing import Optional


class EloConfig(BaseModel):
    """Configuration for NFL Elo rating system."""
    
    # General Elo parameters
    base_rating: float = Field(default=1500.0, description="Starting rating for all teams")
    k: float = Field(default=20.0, description="K-factor for rating updates")
    scale: float = Field(default=400.0, description="Logistic scale in Elo expectation")
    hfa_points: float = Field(default=55.0, description="Home field advantage in rating points")
    preseason_regress: float = Field(default=0.30, description="Preseason regression factor (30% carry-over)")
    mov_enabled: bool = Field(default=True, description="Enable margin of victory multiplier")
    qb_adj_weight: float = Field(default=0.0, description="QB adjustment weight in points")
    rest_per_day_pts: float = Field(default=1.0, description="Rest advantage per extra rest day")

    # MOV multiplier (FiveThirtyEight-style)
    mov_mult_a: float = Field(default=2.2, description="MOV multiplier parameter A")
    mov_mult_b: float = Field(default=0.001, description="MOV multiplier parameter B")

    # Offense/Defense split (optional)
    use_offdef_split: bool = Field(default=False, description="Enable offense/defense split ratings")
    k_off: float = Field(default=12.0, description="K-factor for offense ratings")
    k_def: float = Field(default=12.0, description="K-factor for defense ratings")
    offdef_scale: float = Field(default=30.0, description="Logistic scale for off/def point expectations")

    # Backtest parameters
    start_season: int = Field(default=2021, description="Starting season for backtesting")
    end_season: int = Field(default=2024, description="Ending season for backtesting")
    seed: int = Field(default=42, description="Random seed for reproducibility")

    # Safety rails
    max_rating_shift_per_game: float = Field(default=80.0, description="Maximum rating change per game")
    
    # QB adjustment parameters
    use_qb_adjustment: bool = Field(default=False, description="Enable QB adjustments")
    use_advanced_qb_adjustment: bool = Field(default=False, description="Use advanced QB performance tracking")
    use_qb_change_adjustment: bool = Field(default=False, description="Enable QB change adjustments")
    qb_adjustment_weight: float = Field(default=1.0, description="Weight for QB adjustments (0.0-2.0)")
    qb_performance_window: int = Field(default=4, description="Rolling window for QB performance metrics")
    qb_experience_threshold: int = Field(default=5, description="Games threshold for QB experience adjustment")
    qb_qbr_excellent: float = Field(default=70.0, description="QBR threshold for excellent performance")
    qb_qbr_good: float = Field(default=60.0, description="QBR threshold for good performance")
    qb_qbr_poor: float = Field(default=40.0, description="QBR threshold for poor performance")
    qb_qbr_very_poor: float = Field(default=30.0, description="QBR threshold for very poor performance")
    qb_epa_excellent: float = Field(default=0.2, description="EPA threshold for excellent performance")
    qb_epa_good: float = Field(default=0.1, description="EPA threshold for good performance")
    qb_epa_poor: float = Field(default=-0.1, description="EPA threshold for poor performance")
    qb_epa_very_poor: float = Field(default=-0.2, description="EPA threshold for very poor performance")
    qb_win_rate_excellent: float = Field(default=0.7, description="Win rate threshold for excellent performance")
    qb_win_rate_good: float = Field(default=0.6, description="Win rate threshold for good performance")
    qb_win_rate_poor: float = Field(default=0.3, description="Win rate threshold for poor performance")
    qb_win_rate_very_poor: float = Field(default=0.2, description="Win rate threshold for very poor performance")
    qb_max_delta: float = Field(default=10.0, description="Maximum QB adjustment delta")
    
    # Weather adjustment parameters
    use_weather_adjustment: bool = Field(default=False, description="Enable weather adjustments")
    weather_adjustment_weight: float = Field(default=1.0, description="Weight for weather adjustments (0.0-2.0)")
    weather_temp_optimal: float = Field(default=20.0, description="Optimal temperature in Celsius")
    weather_wind_threshold: float = Field(default=15.0, description="Wind speed threshold for significant impact")
    weather_precip_threshold: float = Field(default=5.0, description="Precipitation threshold for significant impact")
    weather_max_delta: float = Field(default=5.0, description="Maximum weather adjustment delta")
    
    # Travel adjustment parameters
    use_travel_adjustment: bool = Field(default=False, description="Enable travel adjustments")
    travel_adjustment_weight: float = Field(default=1.0, description="Weight for travel adjustments (0.0-2.0)")
    travel_fatigue_weight: float = Field(default=1.0, description="Weight for travel fatigue (0.0-2.0)")
    travel_distance_threshold: float = Field(default=1000.0, description="Distance threshold for significant travel impact")
    travel_timezone_threshold: int = Field(default=2, description="Timezone threshold for significant travel impact")
    travel_max_delta: float = Field(default=3.0, description="Maximum travel adjustment delta")
    
    # Injury adjustment parameters
    use_injury_adjustment: bool = Field(default=False, description="Enable injury adjustments")
    injury_adjustment_weight: float = Field(default=1.0, description="Weight for injury adjustments (0.0-2.0)")
    injury_max_delta: float = Field(default=10.0, description="Maximum injury adjustment in points")
    injury_position_weights: dict = Field(default_factory=dict, description="Position importance weights for injury impact")
    injury_severity_weights: dict = Field(default_factory=dict, description="Injury severity weights")
    injury_key_position_threshold: float = Field(default=2.0, description="Threshold for significant key position injuries")
    
    # Red zone adjustment parameters
    use_redzone_adjustment: bool = Field(default=False, description="Enable red zone efficiency adjustments")
    redzone_adjustment_weight: float = Field(default=1.0, description="Weight for red zone adjustments (0.0-2.0)")
    redzone_max_delta: float = Field(default=5.0, description="Maximum red zone adjustment in points")
    redzone_impact_threshold: float = Field(default=0.01, description="Minimum red zone impact to apply adjustment")
    
    # Down efficiency adjustment parameters
    use_downs_adjustment: bool = Field(default=False, description="Enable third/fourth down efficiency adjustments")
    downs_adjustment_weight: float = Field(default=1.0, description="Weight for down efficiency adjustments (0.0-2.0)")
    downs_max_delta: float = Field(default=3.0, description="Maximum down efficiency adjustment in points")
    downs_impact_threshold: float = Field(default=0.01, description="Minimum down efficiency impact to apply adjustment")
    
    # Clock management adjustment parameters
    use_clock_management_adjustment: bool = Field(default=False, description="Enable clock management efficiency adjustments")
    clock_management_adjustment_weight: float = Field(default=1.0, description="Weight for clock management adjustments (0.0-2.0)")
    clock_management_max_delta: float = Field(default=4.0, description="Maximum clock management adjustment in points")
    clock_management_impact_threshold: float = Field(default=0.01, description="Minimum clock management impact to apply adjustment")
    
    # Situational efficiency adjustment parameters
    use_situational_adjustment: bool = Field(default=False, description="Enable situational efficiency adjustments (red zone, third down)")
    situational_adjustment_weight: float = Field(default=1.0, description="Weight for situational adjustments (0.0-2.0)")
    situational_max_delta: float = Field(default=5.0, description="Maximum situational adjustment in points")
    situational_impact_threshold: float = Field(default=0.01, description="Minimum situational impact to apply adjustment")
    
    # Turnover adjustment parameters
    use_turnover_adjustment: bool = Field(default=False, description="Enable turnover differential adjustments")
    turnover_adjustment_weight: float = Field(default=1.0, description="Weight for turnover adjustments (0.0-2.0)")
    turnover_max_delta: float = Field(default=6.0, description="Maximum turnover adjustment in points")
    turnover_impact_threshold: float = Field(default=0.01, description="Minimum turnover impact to apply adjustment")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Add any custom encoders if needed
        }
        validate_assignment = True
