"""Tests for core Elo functionality."""

import pytest
import numpy as np
from models.nfl_elo.config import EloConfig
from models.nfl_elo.ratings import TeamRating, RatingBook, OffDefRating
from models.nfl_elo.updater import logistic_expectation, mov_multiplier, apply_game_update


class TestLogisticExpectation:
    """Test logistic expectation function."""
    
    def test_equal_ratings(self):
        """Equal ratings should give 0.5 probability."""
        prob = logistic_expectation(1500, 1500, 400)
        assert prob == pytest.approx(0.5, abs=1e-6)
    
    def test_rating_advantage(self):
        """Higher rating should give higher probability."""
        prob_high = logistic_expectation(1700, 1500, 400)
        prob_low = logistic_expectation(1500, 1700, 400)
        
        assert prob_high > 0.5
        assert prob_low < 0.5
        assert prob_high + prob_low == pytest.approx(1.0, abs=1e-6)
    
    def test_scale_parameter(self):
        """Different scales should affect probability sensitivity."""
        prob_400 = logistic_expectation(1600, 1500, 400)
        prob_200 = logistic_expectation(1600, 1500, 200)
        
        # Smaller scale should make probabilities more extreme
        assert prob_200 > prob_400
    
    def test_invalid_scale(self):
        """Invalid scale should raise error."""
        with pytest.raises(ValueError):
            logistic_expectation(1500, 1500, 0)
        
        with pytest.raises(ValueError):
            logistic_expectation(1500, 1500, -100)


class TestMOVMultiplier:
    """Test margin of victory multiplier."""
    
    def test_no_mov(self):
        """MOV disabled should return 1.0."""
        cfg = EloConfig(mov_enabled=False)
        mult = mov_multiplier(10, 100, cfg)
        assert mult == 1.0
    
    def test_mov_enabled(self):
        """MOV enabled should return multiplier > 1 for blowouts."""
        cfg = EloConfig(mov_enabled=True)
        mult = mov_multiplier(20, 100, cfg)
        assert mult > 1.0
    
    def test_close_game(self):
        """Close games should have smaller multiplier."""
        cfg = EloConfig(mov_enabled=True)
        mult_close = mov_multiplier(1, 100, cfg)
        mult_blowout = mov_multiplier(20, 100, cfg)
        
        assert mult_close < mult_blowout
    
    def test_negative_margin(self):
        """Negative margins should work the same as positive."""
        cfg = EloConfig(mov_enabled=True)
        mult_pos = mov_multiplier(10, 100, cfg)
        mult_neg = mov_multiplier(-10, 100, cfg)
        
        assert mult_pos == mult_neg


class TestGameUpdate:
    """Test game update function."""
    
    def test_basic_update(self):
        """Basic game update should work."""
        cfg = EloConfig()
        home_rating = 1500
        away_rating = 1500
        
        new_home, new_away, prob = apply_game_update(
            home_rating, away_rating, 21, 14, cfg
        )
        
        # Home team won, so should gain rating
        assert new_home > home_rating
        assert new_away < away_rating
        assert prob > 0.5  # Home team had HFA advantage
        
        # Ratings should sum to same total (approximately)
        total_before = home_rating + away_rating
        total_after = new_home + new_away
        assert abs(total_after - total_before) < 1e-6
    
    def test_away_team_wins(self):
        """Away team winning should reduce home rating."""
        cfg = EloConfig()
        home_rating = 1500
        away_rating = 1500
        
        new_home, new_away, prob = apply_game_update(
            home_rating, away_rating, 14, 21, cfg
        )
        
        # Away team won, so home should lose rating
        assert new_home < home_rating
        assert new_away > away_rating
        assert prob > 0.5  # Still > 0.5 due to HFA
    
    def test_rest_advantage(self):
        """Rest advantage should affect ratings."""
        cfg = EloConfig(rest_per_day_pts=2.0)
        
        # Home team with more rest
        new_home1, new_away1, prob1 = apply_game_update(
            1500, 1500, 21, 14, cfg, home_rest_days=7, away_rest_days=3
        )
        
        # Home team with less rest
        new_home2, new_away2, prob2 = apply_game_update(
            1500, 1500, 21, 14, cfg, home_rest_days=3, away_rest_days=7
        )
        
        # More rest should give higher probability
        assert prob1 > prob2
    
    def test_safety_rails(self):
        """Safety rails should limit rating changes."""
        cfg = EloConfig(k=1000, max_rating_shift_per_game=50.0)
        
        new_home, new_away, prob = apply_game_update(
            1500, 1500, 50, 0, cfg  # Huge blowout
        )
        
        # Rating change should be capped
        change = abs(new_home - 1500)
        assert change <= cfg.max_rating_shift_per_game
    
    def test_invalid_inputs(self):
        """Invalid inputs should raise errors."""
        cfg = EloConfig()
        
        with pytest.raises(ValueError):
            apply_game_update(1500, 1500, -1, 14, cfg)
        
        with pytest.raises(ValueError):
            apply_game_update(1500, 1500, 21, -1, cfg)


class TestRatingBook:
    """Test RatingBook functionality."""
    
    def test_initialization(self):
        """RatingBook should initialize correctly."""
        book = RatingBook(base=1500)
        assert book.base == 1500
        assert len(book.ratings) == 0
    
    def test_get_set_ratings(self):
        """Should be able to get and set ratings."""
        book = RatingBook(base=1500)
        
        # Get non-existent team should return base
        assert book.get("NE") == 1500
        
        # Set and get rating
        book.set("NE", 1600)
        assert book.get("NE") == 1600
        assert len(book.ratings) == 1
    
    def test_preseason_regression(self):
        """Preseason regression should work correctly."""
        book = RatingBook(base=1500)
        book.set("NE", 1700)
        book.set("BUF", 1300)
        
        book.regress_preseason(0.75)
        
        # Should regress toward 1500
        assert book.get("NE") < 1700
        assert book.get("BUF") > 1300
        assert book.get("NE") > 1500  # Still above average
        assert book.get("BUF") < 1500  # Still below average
    
    def test_offdef_ratings(self):
        """Offense/defense ratings should work."""
        book = RatingBook(base=1500)
        
        # Set off/def ratings
        book.set_offdef("NE", 1600, 1400)
        off, def_rating = book.get_offdef("NE")
        assert off == 1600
        assert def_rating == 1400
        
        # Non-existent team should return base
        off, def_rating = book.get_offdef("BUF")
        assert off == 1500
        assert def_rating == 1500
    
    def test_negative_ratings(self):
        """Should not allow negative ratings."""
        book = RatingBook(base=1500)
        
        with pytest.raises(ValueError):
            book.set("NE", -100)
        
        with pytest.raises(ValueError):
            book.set_offdef("NE", -100, 1500)
        
        with pytest.raises(ValueError):
            book.set_offdef("NE", 1500, -100)


class TestTeamRating:
    """Test TeamRating class."""
    
    def test_team_rating_creation(self):
        """Should create team rating correctly."""
        rating = TeamRating("NE", 1600)
        assert rating.team == "NE"
        assert rating.elo == 1600
    
    def test_negative_rating_validation(self):
        """Should not allow negative ratings."""
        with pytest.raises(ValueError):
            TeamRating("NE", -100)


class TestOffDefRating:
    """Test OffDefRating class."""
    
    def test_offdef_rating_creation(self):
        """Should create off/def rating correctly."""
        rating = OffDefRating("NE", 1600, 1400)
        assert rating.team == "NE"
        assert rating.offense == 1600
        assert rating.defense == 1400
    
    def test_negative_rating_validation(self):
        """Should not allow negative ratings."""
        with pytest.raises(ValueError):
            OffDefRating("NE", -100, 1500)
        
        with pytest.raises(ValueError):
            OffDefRating("NE", 1500, -100)
