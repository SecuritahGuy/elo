/**
 * Live Game Tracking Service
 * Real-time tracking of NFL games with prediction monitoring
 */

import apiService from './api';
import predictionService from './predictionService';

class LiveGameTrackingService {
  constructor() {
    this.activeGames = new Map();
    this.subscribers = new Map();
    this.updateInterval = null;
    this.isTracking = false;
    this.updateFrequency = 60000; // 60 seconds (reduced from 30 seconds)
    this.hasLiveGames = false; // Track if there are any live games
  }

  /**
   * Start tracking live games
   */
  startTracking() {
    if (this.isTracking) return;

    this.isTracking = true;
    this.updateInterval = setInterval(() => {
      this.smartUpdateLiveGames();
    }, this.updateFrequency);

    console.log('Live game tracking started with smart updates');
  }

  /**
   * Stop tracking live games
   */
  stopTracking() {
    if (!this.isTracking) return;

    this.isTracking = false;
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }

    console.log('Live game tracking stopped');
  }

  /**
   * Get current live games
   */
  async getLiveGames() {
    try {
      // Try to get real live games from API
      const response = await apiService.getLiveGames();
      return response.data.games || [];
    } catch (error) {
      console.warn('Real live games not available:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  /**
   * Generate mock live games for testing
   */
  generateMockLiveGames() {
    const currentTime = new Date();
    const games = [];

    // Simulate different game states
    const gameStates = [
      {
        id: 'live_game_1',
        homeTeam: 'KC',
        awayTeam: 'BUF',
        homeScore: 14,
        awayScore: 10,
        quarter: 2,
        timeRemaining: '8:42',
        status: 'in_progress',
        possession: 'KC',
        down: 2,
        distance: 7,
        yardLine: 45,
        redZone: false,
        weather: 'Clear',
        temperature: 72,
        windSpeed: 8,
        gameDate: new Date(currentTime.getTime() - 30 * 60 * 1000).toISOString(), // Started 30 min ago
        lastUpdate: currentTime.toISOString()
      },
      {
        id: 'live_game_2',
        homeTeam: 'SF',
        awayTeam: 'DAL',
        homeScore: 21,
        awayScore: 17,
        quarter: 3,
        timeRemaining: '12:15',
        status: 'in_progress',
        possession: 'DAL',
        down: 1,
        distance: 10,
        yardLine: 25,
        redZone: true,
        weather: 'Partly Cloudy',
        temperature: 68,
        windSpeed: 12,
        gameDate: new Date(currentTime.getTime() - 60 * 60 * 1000).toISOString(), // Started 1 hour ago
        lastUpdate: currentTime.toISOString()
      },
      {
        id: 'live_game_3',
        homeTeam: 'PHI',
        awayTeam: 'GB',
        homeScore: 28,
        awayScore: 24,
        quarter: 4,
        timeRemaining: '2:30',
        status: 'in_progress',
        possession: 'GB',
        down: 3,
        distance: 3,
        yardLine: 8,
        redZone: true,
        weather: 'Rain',
        temperature: 45,
        windSpeed: 15,
        gameDate: new Date(currentTime.getTime() - 90 * 60 * 1000).toISOString(), // Started 1.5 hours ago
        lastUpdate: currentTime.toISOString()
      }
    ];

    return gameStates;
  }

  /**
   * Smart update that only polls when there are live games
   */
  async smartUpdateLiveGames() {
    try {
      // First, check if we have any live games currently
      const currentLiveGames = Array.from(this.activeGames.values())
        .filter(game => game.status === 'in_progress');
      
      // If no live games and we haven't detected any recently, skip the API call
      if (currentLiveGames.length === 0 && !this.hasLiveGames) {
        console.log('No live games detected, skipping API call to save resources');
        return;
      }

      // Get live games from API
      const liveGames = await this.getLiveGames();
      const inProgressGames = liveGames.filter(game => game.status === 'in_progress');
      
      // Update our tracking of whether there are live games
      this.hasLiveGames = inProgressGames.length > 0;
      
      if (inProgressGames.length === 0) {
        console.log('No live games found, will reduce polling frequency');
        // Clean up any completed games
        this.cleanupCompletedGames();
        return;
      }

      console.log(`Found ${inProgressGames.length} live games, updating data...`);
      
      for (const game of liveGames) {
        const gameId = game.id;
        const existingGame = this.activeGames.get(gameId);
        
        // Update game data
        this.activeGames.set(gameId, {
          ...game,
          lastUpdate: new Date().toISOString(),
          predictionData: await this.getGamePredictionData(game),
          liveMetrics: this.calculateLiveMetrics(game, existingGame)
        });

        // Notify subscribers
        this.notifySubscribers(gameId, this.activeGames.get(gameId));
      }

      // Remove completed games
      this.cleanupCompletedGames();
    } catch (error) {
      console.error('Error updating live games:', error);
    }
  }

  /**
   * Update live games data (legacy method for backward compatibility)
   */
  async updateLiveGames() {
    return this.smartUpdateLiveGames();
  }

  /**
   * Get prediction data for a specific game
   */
  async getGamePredictionData(game) {
    try {
      // Get our prediction for this game
      const predictions = await predictionService.getPredictions(2025, 1);
      const gamePrediction = predictions.find(p => 
        p.homeTeam === game.homeTeam && p.awayTeam === game.awayTeam
      );

      if (!gamePrediction) {
        return null;
      }

      // Calculate live prediction accuracy
      const currentWinner = game.homeScore > game.awayScore ? game.homeTeam : 
                           game.awayScore > game.homeScore ? game.awayTeam : null;
      
      const predictionCorrect = currentWinner ? 
        currentWinner === gamePrediction.predictedWinner : null;

      return {
        predictedWinner: gamePrediction.predictedWinner,
        homeWinProb: gamePrediction.homeWinProb,
        confidence: gamePrediction.confidence,
        predictedScore: gamePrediction.predictedScore,
        currentWinner,
        predictionCorrect,
        liveAccuracy: this.calculateLiveAccuracy(game, gamePrediction)
      };
    } catch (error) {
      console.error('Error getting game prediction data:', error);
      return null;
    }
  }

  /**
   * Calculate live prediction accuracy
   */
  calculateLiveAccuracy(game, prediction) {
    if (!prediction) return null;

    const currentWinner = game.homeScore > game.awayScore ? game.homeTeam : 
                         game.awayScore > game.homeScore ? game.awayTeam : null;
    
    if (!currentWinner) return null;

    return currentWinner === prediction.predictedWinner;
  }

  /**
   * Calculate live metrics for a game
   */
  calculateLiveMetrics(game, previousGame) {
    const metrics = {
      scoreChange: {
        home: previousGame ? game.homeScore - previousGame.homeScore : 0,
        away: previousGame ? game.awayScore - previousGame.awayScore : 0
      },
      momentum: this.calculateMomentum(game, previousGame),
      excitement: this.calculateExcitementLevel(game),
      competitiveness: this.calculateCompetitiveness(game),
      timeRemaining: this.parseTimeRemaining(game.timeRemaining, game.quarter)
    };

    return metrics;
  }

  /**
   * Calculate game momentum
   */
  calculateMomentum(game, previousGame) {
    if (!previousGame) return 'neutral';

    const homeScoreChange = game.homeScore - previousGame.homeScore;
    const awayScoreChange = game.awayScore - previousGame.awayScore;
    const netChange = homeScoreChange - awayScoreChange;

    if (netChange > 7) return 'home_momentum';
    if (netChange < -7) return 'away_momentum';
    return 'neutral';
  }

  /**
   * Calculate excitement level
   */
  calculateExcitementLevel(game) {
    const totalScore = game.homeScore + game.awayScore;
    const scoreDifference = Math.abs(game.homeScore - game.awayScore);
    const quarter = game.quarter;
    
    let excitement = 0;
    
    // Base excitement from total score
    excitement += Math.min(totalScore / 10, 5);
    
    // Close games are more exciting
    if (scoreDifference <= 7) excitement += 3;
    else if (scoreDifference <= 14) excitement += 1;
    
    // Later quarters are more exciting
    excitement += quarter * 0.5;
    
    // Red zone adds excitement
    if (game.redZone) excitement += 2;
    
    return Math.min(excitement, 10);
  }

  /**
   * Calculate competitiveness
   */
  calculateCompetitiveness(game) {
    const scoreDifference = Math.abs(game.homeScore - game.awayScore);
    const totalScore = game.homeScore + game.awayScore;
    
    if (totalScore === 0) return 0.5;
    
    // More competitive when scores are close
    const competitiveness = 1 - (scoreDifference / Math.max(totalScore, 1));
    return Math.max(0, Math.min(1, competitiveness));
  }

  /**
   * Parse time remaining
   */
  parseTimeRemaining(timeString, quarter) {
    if (!timeString) return null;
    
    const [minutes, seconds] = timeString.split(':').map(Number);
    const totalSeconds = minutes * 60 + seconds;
    
    return {
      minutes,
      seconds,
      totalSeconds,
      quarter,
      formatted: timeString
    };
  }

  /**
   * Subscribe to game updates
   */
  subscribe(gameId, callback) {
    if (!this.subscribers.has(gameId)) {
      this.subscribers.set(gameId, new Set());
    }
    this.subscribers.get(gameId).add(callback);

    // Return unsubscribe function
    return () => {
      const gameSubscribers = this.subscribers.get(gameId);
      if (gameSubscribers) {
        gameSubscribers.delete(callback);
        if (gameSubscribers.size === 0) {
          this.subscribers.delete(gameId);
        }
      }
    };
  }

  /**
   * Notify subscribers of game updates
   */
  notifySubscribers(gameId, gameData) {
    const gameSubscribers = this.subscribers.get(gameId);
    if (gameSubscribers) {
      gameSubscribers.forEach(callback => {
        try {
          callback(gameData);
        } catch (error) {
          console.error('Error in subscriber callback:', error);
        }
      });
    }
  }

  /**
   * Get specific game data
   */
  getGame(gameId) {
    return this.activeGames.get(gameId);
  }

  /**
   * Get all active games
   */
  getAllGames() {
    return Array.from(this.activeGames.values());
  }

  /**
   * Get games by team
   */
  getGamesByTeam(team) {
    return this.getAllGames().filter(game => 
      game.homeTeam === team || game.awayTeam === team
    );
  }

  /**
   * Get games by status
   */
  getGamesByStatus(status) {
    return this.getAllGames().filter(game => game.status === status);
  }

  /**
   * Clean up completed games
   */
  cleanupCompletedGames() {
    const completedGames = [];
    
    for (const [gameId, game] of this.activeGames) {
      if (game.status === 'final' || game.status === 'completed') {
        completedGames.push(gameId);
      }
    }

    completedGames.forEach(gameId => {
      this.activeGames.delete(gameId);
      this.subscribers.delete(gameId);
    });
  }

  /**
   * Get live analytics summary
   */
  getLiveAnalytics() {
    const games = this.getAllGames();
    const inProgressGames = games.filter(g => g.status === 'in_progress');
    
    if (inProgressGames.length === 0) {
      return {
        totalGames: 0,
        inProgressGames: 0,
        averageExcitement: 0,
        averageCompetitiveness: 0,
        predictionAccuracy: 0,
        totalPredictions: 0,
        correctPredictions: 0
      };
    }

    const totalExcitement = inProgressGames.reduce((sum, game) => 
      sum + (game.liveMetrics?.excitement || 0), 0);
    const totalCompetitiveness = inProgressGames.reduce((sum, game) => 
      sum + (game.liveMetrics?.competitiveness || 0), 0);
    
    const gamesWithPredictions = inProgressGames.filter(g => g.predictionData);
    const correctPredictions = gamesWithPredictions.filter(g => 
      g.predictionData.predictionCorrect === true).length;

    return {
      totalGames: games.length,
      inProgressGames: inProgressGames.length,
      averageExcitement: totalExcitement / inProgressGames.length,
      averageCompetitiveness: totalCompetitiveness / inProgressGames.length,
      predictionAccuracy: gamesWithPredictions.length > 0 ? 
        correctPredictions / gamesWithPredictions.length : 0,
      totalPredictions: gamesWithPredictions.length,
      correctPredictions
    };
  }

  /**
   * Get game highlights
   */
  getGameHighlights(gameId) {
    const game = this.getGame(gameId);
    if (!game) return [];

    const highlights = [];

    // Score milestones
    if (game.homeScore >= 21) {
      highlights.push({
        type: 'score_milestone',
        team: game.homeTeam,
        message: `${game.homeTeam} reaches 21+ points`,
        timestamp: game.lastUpdate
      });
    }

    if (game.awayScore >= 21) {
      highlights.push({
        type: 'score_milestone',
        team: game.awayTeam,
        message: `${game.awayTeam} reaches 21+ points`,
        timestamp: game.lastUpdate
      });
    }

    // Close game
    const scoreDifference = Math.abs(game.homeScore - game.awayScore);
    if (scoreDifference <= 3) {
      highlights.push({
        type: 'close_game',
        message: 'Game within 3 points - very competitive!',
        timestamp: game.lastUpdate
      });
    }

    // Red zone
    if (game.redZone) {
      highlights.push({
        type: 'red_zone',
        team: game.possession,
        message: `${game.possession} in the red zone`,
        timestamp: game.lastUpdate
      });
    }

    // High excitement
    if (game.liveMetrics?.excitement > 7) {
      highlights.push({
        type: 'high_excitement',
        message: 'High excitement level!',
        timestamp: game.lastUpdate
      });
    }

    return highlights;
  }

  /**
   * Check if there are any live games without making API calls
   */
  hasActiveLiveGames() {
    return Array.from(this.activeGames.values())
      .some(game => game.status === 'in_progress');
  }

  /**
   * Force an update regardless of smart update logic
   */
  async forceUpdate() {
    console.log('Forcing live games update...');
    await this.updateLiveGames();
  }

  /**
   * Get current polling status
   */
  getPollingStatus() {
    return {
      isTracking: this.isTracking,
      updateFrequency: this.updateFrequency,
      hasLiveGames: this.hasLiveGames,
      activeGamesCount: this.activeGames.size,
      liveGamesCount: Array.from(this.activeGames.values())
        .filter(game => game.status === 'in_progress').length
    };
  }

  /**
   * Cleanup on destroy
   */
  destroy() {
    this.stopTracking();
    this.activeGames.clear();
    this.subscribers.clear();
  }
}

export default new LiveGameTrackingService();
