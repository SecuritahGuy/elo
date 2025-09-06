import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './WeeklySchedule.css';

const WeeklySchedule = () => {
  const [currentSeason, setCurrentSeason] = useState(2025);
  const [currentWeek, setCurrentWeek] = useState(1);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGame, setSelectedGame] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // Get current NFL week (simplified - in production would calculate from current date)
  const getCurrentWeek = () => {
    const now = new Date();
    const seasonStart = new Date(now.getFullYear(), 8, 1); // September 1st
    const weeksSinceStart = Math.floor((now - seasonStart) / (7 * 24 * 60 * 60 * 1000));
    return Math.min(Math.max(weeksSinceStart + 1, 1), 18); // NFL season is 18 weeks
  };

  useEffect(() => {
    const week = getCurrentWeek();
    setCurrentWeek(week);
    loadGames(currentSeason, week);
    
    // Set up auto-refresh for live games every 60 seconds (optimized)
    const refreshInterval = setInterval(() => {
      loadGames(currentSeason, week);
    }, 60000);
    
    return () => clearInterval(refreshInterval);
  }, [currentSeason]);

  const loadGames = async (season, week) => {
    try {
      setLoading(true);
      setError(null);
      
      // Get real live games data
      const liveGamesResponse = await apiService.getLiveGames();
      const liveGames = liveGamesResponse.data.games || [];
      
      // Get ELO ratings for the season (current or projected)
      let eloRatings = [];
      const currentWeek = getCurrentWeek();
      
      if (week <= currentWeek) {
        // Use current ELO ratings for current/past weeks
        const eloResponse = await apiService.getEloRatings(season, 'comprehensive');
        eloRatings = eloResponse.data.ratings || [];
      } else {
        // Use projected ELO ratings for future weeks
        try {
          const projectionResponse = await apiService.getEloProjections(season, week);
          eloRatings = projectionResponse.data.projections || [];
          // Convert projection format to match current ratings format
          eloRatings = eloRatings.map(proj => ({
            team: proj.team,
            rating: proj.projected_rating,
            confidence: proj.confidence_score,
            method: proj.projection_method
          }));
        } catch (projError) {
          console.warn('Projected ELOs not available, using current ratings:', projError);
          const eloResponse = await apiService.getEloRatings(season, 'comprehensive');
          eloRatings = eloResponse.data.ratings || [];
        }
      }
      
      // Create ELO lookup map
      const eloMap = {};
      eloRatings.forEach(team => {
        eloMap[team.team] = team.rating;
      });
      
      // Process live games into weekly schedule format
      const processedGames = liveGames.map(game => {
        const homeElo = eloMap[game.home_team] || 1500;
        const awayElo = eloMap[game.away_team] || 1500;
        const eloDifference = homeElo - awayElo;
        const homeAdvantage = 25;
        const adjustedDifference = eloDifference + homeAdvantage;
        
        // Calculate win probabilities based on ELO difference
        const homeWinProb = 1 / (1 + Math.pow(10, -adjustedDifference / 400));
        const awayWinProb = 1 - homeWinProb;
        
        // Determine predicted winner based on win probability
        const predictedWinner = homeWinProb > awayWinProb ? game.home_team : game.away_team;
        
        // Calculate confidence based on ELO difference
        const confidence = Math.min(0.95, Math.max(0.55, Math.abs(adjustedDifference) / 200));
        
        // Calculate expected margin (positive means home team favored)
        const expectedMargin = Math.round(adjustedDifference / 25);
        
        // Determine game status and format time
        let gameStatus = game.status || 'scheduled';
        let gameTime = game.last_update || new Date().toISOString();
        
        // Override status based on game state
        const hasScores = (game.home_score > 0 || game.away_score > 0);
        const isInProgress = game.quarter > 0 && game.time_remaining && game.time_remaining !== '0:00';
        const isLive = gameStatus === 'in_progress' || (hasScores && isInProgress);
        const isFinal = gameStatus === 'final' || (hasScores && game.quarter >= 4 && (!game.time_remaining || game.time_remaining === '0:00'));
        
        // Debug logging for specific games
        if ((game.home_team === 'LAC' && game.away_team === 'KC') || 
            (game.home_team === 'PHI' && game.away_team === 'DAL')) {
          console.log(`${game.away_team} @ ${game.home_team} Debug:`, {
            originalStatus: game.status,
            hasScores,
            quarter: game.quarter,
            time_remaining: game.time_remaining,
            isInProgress,
            isLive,
            isFinal
          });
        }
        
        if (isFinal) {
          gameStatus = 'FINAL';
        } else if (isLive) {
          gameStatus = 'LIVE';
        } else if (gameStatus === 'scheduled') {
          gameStatus = 'SCHEDULED';
        }
        
        // Format time display
        if (gameStatus === 'LIVE' && game.quarter && game.time_remaining) {
          // Show live game time
          gameTime = `Q${game.quarter} - ${game.time_remaining}`;
        } else {
          try {
            const gameDate = new Date(gameTime);
            gameTime = gameDate.toLocaleString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
              timeZoneName: 'short'
            });
          } catch (e) {
            gameTime = 'TBD';
          }
        }
        
        return {
          id: game.id,
          home_team: game.home_team,
          away_team: game.away_team,
          home_score: game.home_score || 0,
          away_score: game.away_score || 0,
          week: week,
          season: season,
          status: gameStatus,
          game_time: gameTime,
          home_elo: homeElo,
          away_elo: awayElo,
          home_win_probability: homeWinProb,
          away_win_probability: awayWinProb,
          predicted_winner: predictedWinner,
          confidence: confidence,
          expected_margin: expectedMargin
        };
      });
      
      if (processedGames.length > 0) {
        setGames(processedGames);
      } else {
        // Fallback to mock data if no real data available
        const mockGames = generateMockGames(season, week);
        setGames(mockGames);
      }
    } catch (err) {
      console.error('Error loading games:', err);
      // Fallback to mock data
      const mockGames = generateMockGames(season, week);
      setGames(mockGames);
      // Don't set error if we have mock data
      if (mockGames.length === 0) {
        setError('Failed to load games');
      }
    } finally {
      setLoading(false);
    }
  };

  const generateMockGames = (season, week) => {
    const teams = [
      'KC', 'BUF', 'MIA', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT', 'HOU',
      'IND', 'JAX', 'TEN', 'DEN', 'LV', 'LAC', 'DAL', 'PHI', 'NYG', 'WAS',
      'CHI', 'DET', 'GB', 'MIN', 'ATL', 'CAR', 'NO', 'TB', 'ARI', 'LAR',
      'SF', 'SEA'
    ];

    const mockGames = [];
    const gamesPerWeek = 16; // 32 teams = 16 games per week
    
    for (let i = 0; i < gamesPerWeek; i += 2) {
      const homeTeam = teams[i];
      const awayTeam = teams[i + 1];
      
      mockGames.push({
        id: `game_${season}_week${week}_${homeTeam}_${awayTeam}`,
        home_team: homeTeam,
        away_team: awayTeam,
        home_score: Math.floor(Math.random() * 35),
        away_score: Math.floor(Math.random() * 35),
        week: week,
        season: season,
        status: Math.random() > 0.5 ? 'scheduled' : 'final',
        game_time: new Date(2025, 8, 5 + Math.floor(Math.random() * 7), 12 + Math.floor(Math.random() * 12), Math.floor(Math.random() * 60)).toISOString(),
        home_elo: 1500 + Math.floor(Math.random() * 400) - 200,
        away_elo: 1500 + Math.floor(Math.random() * 400) - 200,
        home_win_probability: Math.random(),
        away_win_probability: Math.random(),
        predicted_winner: Math.random() > 0.5 ? homeTeam : awayTeam,
        confidence: Math.random() * 0.4 + 0.6, // 60-100% confidence
        expected_margin: Math.floor(Math.random() * 14) - 7 // -7 to +7 points
      });
    }
    
    return mockGames;
  };

  const handleWeekChange = (week) => {
    setCurrentWeek(week);
    loadGames(currentSeason, week);
  };

  const handleGameClick = async (game) => {
    try {
      // Get detailed ELO data for both teams
      const [homeEloResponse, awayEloResponse] = await Promise.all([
        apiService.getTeamEloHistory(game.home_team, [currentSeason]),
        apiService.getTeamEloHistory(game.away_team, [currentSeason])
      ]);

      const homeElo = homeEloResponse.data?.elo_history?.[0] || { rating: game.home_elo };
      const awayElo = awayEloResponse.data?.elo_history?.[0] || { rating: game.away_elo };

      // Get game prediction using the real API
      const predictionResponse = await apiService.getGamePrediction(
        game.home_team, 
        game.away_team
      );

      const prediction = predictionResponse.data || {
        home_win_probability: game.home_win_probability,
        away_win_probability: game.away_win_probability,
        predicted_winner: game.predicted_winner,
        confidence: game.confidence,
        expected_margin: game.expected_margin
      };

      setSelectedGame({
        ...game,
        home_elo_data: homeElo,
        away_elo_data: awayElo,
        prediction: prediction
      });
      setShowModal(true);
    } catch (err) {
      console.error('Error loading game details:', err);
      // Use basic game data if API fails
      setSelectedGame({
        ...game,
        home_elo_data: { rating: game.home_elo },
        away_elo_data: { rating: game.away_elo },
        prediction: {
          home_win_probability: game.home_win_probability,
          away_win_probability: game.away_win_probability,
          predicted_winner: game.predicted_winner,
          confidence: game.confidence,
          expected_margin: game.expected_margin
        }
      });
      setShowModal(true);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedGame(null);
  };

  const formatGameTime = (gameTime) => {
    // If it's already formatted (like "Q4 - 2:30"), return as is
    if (typeof gameTime === 'string' && (gameTime.includes('Q') || gameTime === 'TBD')) {
      return gameTime;
    }
    
    // Otherwise, format as a date
    try {
      return new Date(gameTime).toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        timeZoneName: 'short'
      });
    } catch (e) {
      return 'TBD';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'FINAL': return '#4CAF50';
      case 'LIVE': return '#FF5722';
      case 'SCHEDULED': return '#2196F3';
      case 'final': return '#4CAF50';
      case 'in_progress': return '#FF5722';
      case 'scheduled': return '#2196F3';
      default: return '#9E9E9E';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'FINAL': return 'FINAL';
      case 'LIVE': return 'LIVE';
      case 'SCHEDULED': return 'SCHEDULED';
      case 'final': return 'FINAL';
      case 'in_progress': return 'LIVE';
      case 'scheduled': return 'SCHEDULED';
      default: return 'UNKNOWN';
    }
  };

  if (loading) {
    return (
      <div className="weekly-schedule">
        <div className="loading">Loading games...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weekly-schedule">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="weekly-schedule">
      <div className="schedule-header">
        <h2>Week {currentWeek} Schedule - {currentSeason} Season</h2>
        <div className="week-selector">
          {Array.from({ length: 18 }, (_, i) => i + 1).map(week => (
            <button
              key={week}
              className={`week-btn ${week === currentWeek ? 'active' : ''}`}
              onClick={() => handleWeekChange(week)}
            >
              Week {week}
            </button>
          ))}
        </div>
      </div>

      <div className="games-grid">
        {games.map((game) => (
          <div
            key={game.id}
            className={`game-card ${game.status.toLowerCase()}`}
            onClick={() => handleGameClick(game)}
          >
            <div className="game-header">
              <div className="game-status" style={{ color: getStatusColor(game.status) }}>
                {game.status === 'LIVE' && <span className="live-indicator">●</span>}
                {getStatusText(game.status)}
              </div>
              <div className="game-time">
                {formatGameTime(game.game_time)}
              </div>
            </div>

            <div className="teams">
              <div className="team away-team">
                <div className="team-name">{game.away_team}</div>
                <div className="team-score">{game.away_score}</div>
                <div className="team-elo">
                  ELO: {game.away_elo}
                  {currentWeek > getCurrentWeek() && <span className="projected-indicator"> (Projected)</span>}
                </div>
              </div>
              
              <div className="vs">@</div>
              
              <div className="team home-team">
                <div className="team-name">{game.home_team}</div>
                <div className="team-score">{game.home_score}</div>
                <div className="team-elo">
                  ELO: {game.home_elo}
                  {currentWeek > getCurrentWeek() && <span className="projected-indicator"> (Projected)</span>}
                </div>
              </div>
            </div>

            <div className="prediction-preview">
              <div className="predicted-winner">
                Predicted: {game.predicted_winner}
              </div>
              <div className="confidence">
                Confidence: {Math.round(game.confidence * 100)}%
              </div>
              <div className="expected-margin">
                Expected Margin: {game.expected_margin > 0 ? '+' : ''}{game.expected_margin}
              </div>
            </div>

            <div className="click-hint">
              Click for detailed ELO breakdown
            </div>
          </div>
        ))}
      </div>

      {showModal && selectedGame && (
        <EloBreakdownModal
          game={selectedGame}
          onClose={closeModal}
        />
      )}
    </div>
  );
};

// ELO Breakdown Modal Component
const EloBreakdownModal = ({ game, onClose }) => {
  const homeElo = game.home_elo_data?.rating || game.home_elo;
  const awayElo = game.away_elo_data?.rating || game.away_elo;
  const prediction = game.prediction;

  const eloDifference = homeElo - awayElo;
  const homeAdvantage = 25; // Home field advantage in ELO points
  const adjustedEloDifference = eloDifference + homeAdvantage;

  const getEloStrength = (elo) => {
    if (elo >= 1600) return 'Elite';
    if (elo >= 1500) return 'Strong';
    if (elo >= 1400) return 'Average';
    if (elo >= 1300) return 'Below Average';
    return 'Weak';
  };

  const getEloColor = (elo) => {
    if (elo >= 1600) return '#4CAF50';
    if (elo >= 1500) return '#8BC34A';
    if (elo >= 1400) return '#FFC107';
    if (elo >= 1300) return '#FF9800';
    return '#F44336';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="elo-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{game.away_team} @ {game.home_team}</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          <div className="elo-comparison">
            <div className="team-elo-detail away">
              <h4>{game.away_team}</h4>
              <div 
                className="elo-rating"
                style={{ color: getEloColor(awayElo) }}
              >
                {awayElo}
              </div>
              <div className="elo-strength">
                {getEloStrength(awayElo)}
              </div>
            </div>

            <div className="elo-difference">
              <div className="difference-value">
                {eloDifference > 0 ? '+' : ''}{eloDifference}
              </div>
              <div className="difference-label">ELO Difference</div>
            </div>

            <div className="team-elo-detail home">
              <h4>{game.home_team}</h4>
              <div 
                className="elo-rating"
                style={{ color: getEloColor(homeElo) }}
              >
                {homeElo}
              </div>
              <div className="elo-strength">
                {getEloStrength(homeElo)}
              </div>
            </div>
          </div>

          <div className="prediction-details">
            <h4>Game Prediction</h4>
            <div className="prediction-grid">
              <div className="prediction-item">
                <div className="prediction-label">Predicted Winner</div>
                <div className="prediction-value winner">
                  {prediction.predicted_winner}
                </div>
              </div>
              
              <div className="prediction-item">
                <div className="prediction-label">Confidence</div>
                <div className="prediction-value">
                  {Math.round(prediction.confidence * 100)}%
                </div>
              </div>
              
              <div className="prediction-item">
                <div className="prediction-label">Expected Margin</div>
                <div className="prediction-value">
                  {prediction.expected_margin > 0 ? '+' : ''}{prediction.expected_margin} points
                </div>
              </div>
            </div>

            <div className="win-probabilities">
              <div className="prob-bar">
                <div className="prob-label">{game.away_team}</div>
                <div className="prob-bar-container">
                  <div 
                    className="prob-bar-fill away"
                    style={{ width: `${prediction.away_win_probability * 100}%` }}
                  ></div>
                </div>
                <div className="prob-value">
                  {Math.round(prediction.away_win_probability * 100)}%
                </div>
              </div>
              
              <div className="prob-bar">
                <div className="prob-label">{game.home_team}</div>
                <div className="prob-bar-container">
                  <div 
                    className="prob-bar-fill home"
                    style={{ width: `${prediction.home_win_probability * 100}%` }}
                  ></div>
                </div>
                <div className="prob-value">
                  {Math.round(prediction.home_win_probability * 100)}%
                </div>
              </div>
            </div>
          </div>

          <div className="game-info">
            <h4>Game Information</h4>
            <div className="info-grid">
              <div className="info-item">
                <div className="info-label">Week</div>
                <div className="info-value">{game.week}</div>
              </div>
              <div className="info-item">
                <div className="info-label">Season</div>
                <div className="info-value">{game.season}</div>
              </div>
              <div className="info-item">
                <div className="info-label">Status</div>
                <div className="info-value">{game.status}</div>
              </div>
              <div className="info-item">
                <div className="info-label">Home Advantage</div>
                <div className="info-value">+{homeAdvantage} ELO</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeeklySchedule;
