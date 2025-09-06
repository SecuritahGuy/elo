/**
 * Game Prediction Service
 * Provides game predictions with win probabilities and confidence scores
 */

import apiService from './api';

class PredictionService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Get game predictions for a specific week
   */
  async getGamePredictions(season = 2025, week = 1) {
    const cacheKey = `predictions:${season}:${week}`;
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      // Get ELO ratings for the season
      const eloRatings = await apiService.getEloRatings(season, 'comprehensive');
      
      // Get games for the week
      const games = await this.getGamesForWeek(season, week);
      
      // Generate predictions
      const predictions = this.generatePredictions(games, eloRatings);
      
      // Cache the results
      this.cache.set(cacheKey, {
        data: predictions,
        timestamp: Date.now()
      });
      
      return predictions;
    } catch (error) {
      console.error('Error generating predictions:', error);
      throw error;
    }
  }

  /**
   * Get games for a specific week
   */
  async getGamesForWeek(season, week) {
    try {
      // Use the real API endpoint for predictions
      const response = await apiService.getWeekPredictions(week);
      return response.data.predictions || [];
    } catch (error) {
      console.error('Error fetching games:', error);
      // Fallback to empty array instead of mock data
      return [];
    }
  }

  /**
   * Generate mock games for testing
   */
  generateMockGames(season, week) {
    if (season === 2025 && week === 1) {
      // Return our generated 2025 Week 1 games
      return [
        {
          id: 'game1',
          homeTeam: 'KC',
          awayTeam: 'BAL',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-05T20:20:00Z',
          status: 'scheduled'
        },
        {
          id: 'game2',
          homeTeam: 'PHI',
          awayTeam: 'DAL',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game3',
          homeTeam: 'BUF',
          awayTeam: 'NYJ',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game4',
          homeTeam: 'SF',
          awayTeam: 'LAR',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game5',
          homeTeam: 'GB',
          awayTeam: 'MIN',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game6',
          homeTeam: 'DET',
          awayTeam: 'CHI',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game7',
          homeTeam: 'CIN',
          awayTeam: 'CLE',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game8',
          homeTeam: 'TB',
          awayTeam: 'ATL',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game9',
          homeTeam: 'MIA',
          awayTeam: 'NE',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game10',
          homeTeam: 'PIT',
          awayTeam: 'BAL',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game11',
          homeTeam: 'CAR',
          awayTeam: 'NO',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game12',
          homeTeam: 'ARI',
          awayTeam: 'SEA',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T13:00:00Z',
          status: 'scheduled'
        },
        {
          id: 'game13',
          homeTeam: 'DEN',
          awayTeam: 'LAC',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T16:05:00Z',
          status: 'scheduled'
        },
        {
          id: 'game14',
          homeTeam: 'LV',
          awayTeam: 'HOU',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T16:05:00Z',
          status: 'scheduled'
        },
        {
          id: 'game15',
          homeTeam: 'IND',
          awayTeam: 'JAX',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T16:25:00Z',
          status: 'scheduled'
        },
        {
          id: 'game16',
          homeTeam: 'TEN',
          awayTeam: 'NYG',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T16:25:00Z',
          status: 'scheduled'
        },
        {
          id: 'game17',
          homeTeam: 'WAS',
          awayTeam: 'DAL',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-07T20:20:00Z',
          status: 'scheduled'
        },
        {
          id: 'game18',
          homeTeam: 'LAR',
          awayTeam: 'SF',
          week: 1,
          season: 2025,
          completed: false,
          gameDate: '2025-09-08T20:15:00Z',
          status: 'scheduled'
        }
      ];
    }
    
    // Default mock games for other seasons/weeks
    const teams = [
      'PHI', 'DAL', 'SF', 'BUF', 'BAL', 'KC', 'GB', 'MIN',
      'DET', 'CIN', 'LAR', 'TB', 'MIA', 'NYJ', 'NE', 'PIT'
    ];
    
    const games = [];
    for (let i = 0; i < teams.length; i += 2) {
      games.push({
        id: `game_${season}_${week}_${i/2 + 1}`,
        season,
        week,
        homeTeam: teams[i],
        awayTeam: teams[i + 1],
        gameDate: new Date(2025, 0, 12 + week * 7).toISOString(),
        status: 'scheduled'
      });
    }
    
    return games;
  }

  /**
   * Generate predictions for games based on ELO ratings
   */
  generatePredictions(games, eloRatings) {
    const predictions = [];
    
    for (const game of games) {
      const homeTeamRating = this.getTeamRating(eloRatings, game.homeTeam);
      const awayTeamRating = this.getTeamRating(eloRatings, game.awayTeam);
      
      if (homeTeamRating && awayTeamRating) {
        const prediction = this.calculatePrediction(
          game.homeTeam,
          game.awayTeam,
          homeTeamRating,
          awayTeamRating
        );
        
        predictions.push({
          ...game,
          prediction
        });
      }
    }
    
    return predictions;
  }

  /**
   * Get team rating from ELO data
   */
  getTeamRating(eloRatings, team) {
    if (!eloRatings || !eloRatings.teams) {
      return null;
    }
    
    const teamData = eloRatings.teams.find(t => t.team === team);
    return teamData ? teamData.rating : null;
  }

  /**
   * Calculate prediction for a game
   */
  calculatePrediction(homeTeam, awayTeam, homeRating, awayRating) {
    // Calculate win probability using ELO formula
    const homeAdvantage = 25; // Home field advantage
    const adjustedHomeRating = homeRating + homeAdvantage;
    
    const expectedHomeScore = 1 / (1 + Math.pow(10, (awayRating - adjustedHomeRating) / 400));
    const expectedAwayScore = 1 - expectedHomeScore;
    
    // Calculate confidence based on rating difference
    const ratingDiff = Math.abs(adjustedHomeRating - awayRating);
    const confidence = this.calculateConfidence(ratingDiff);
    
    // Determine predicted winner
    const predictedWinner = expectedHomeScore > expectedAwayScore ? homeTeam : awayTeam;
    const predictedLoser = expectedHomeScore > expectedAwayScore ? awayTeam : homeTeam;
    
    // Calculate predicted score (simplified)
    const predictedScore = this.calculatePredictedScore(expectedHomeScore, expectedAwayScore);
    
    return {
      homeTeam,
      awayTeam,
      homeWinProbability: Math.round(expectedHomeScore * 100),
      awayWinProbability: Math.round(expectedAwayScore * 100),
      predictedWinner,
      predictedLoser,
      confidence: Math.round(confidence * 100),
      predictedScore: {
        home: predictedScore.home,
        away: predictedScore.away
      },
      ratingDifference: Math.round(ratingDiff),
      homeFieldAdvantage: homeAdvantage,
      expectedHomeScore: Math.round(expectedHomeScore * 100) / 100,
      expectedAwayScore: Math.round(expectedAwayScore * 100) / 100
    };
  }

  /**
   * Calculate confidence score based on rating difference
   */
  calculateConfidence(ratingDiff) {
    // Higher rating difference = higher confidence
    // Max confidence at 200+ point difference
    const maxDiff = 200;
    const confidence = Math.min(ratingDiff / maxDiff, 1);
    
    // Apply sigmoid function for better distribution
    return 1 / (1 + Math.exp(-6 * (confidence - 0.5)));
  }

  /**
   * Calculate predicted score
   */
  calculatePredictedScore(homeProb, awayProb) {
    // Base score around 24 points (NFL average)
    const baseScore = 24;
    
    // Adjust based on win probability
    const homeScore = Math.round(baseScore + (homeProb - 0.5) * 14);
    const awayScore = Math.round(baseScore + (awayProb - 0.5) * 14);
    
    // Ensure minimum score
    return {
      home: Math.max(homeScore, 3),
      away: Math.max(awayScore, 3)
    };
  }

  /**
   * Get prediction accuracy for completed games
   */
  async getPredictionAccuracy(season = 2025, week = 1) {
    try {
      const predictions = await this.getGamePredictions(season, week);
      const completedGames = predictions.filter(game => game.status === 'completed');
      
      if (completedGames.length === 0) {
        return {
          totalGames: 0,
          correctPredictions: 0,
          accuracy: 0,
          confidence: 0
        };
      }
      
      let correctPredictions = 0;
      let totalConfidence = 0;
      
      for (const game of completedGames) {
        if (game.prediction) {
          const actualWinner = game.actualWinner; // This would come from game results
          const predictedWinner = game.prediction.predictedWinner;
          
          if (actualWinner === predictedWinner) {
            correctPredictions++;
          }
          
          totalConfidence += game.prediction.confidence;
        }
      }
      
      const accuracy = correctPredictions / completedGames.length;
      const avgConfidence = totalConfidence / completedGames.length;
      
      return {
        totalGames: completedGames.length,
        correctPredictions,
        accuracy: Math.round(accuracy * 100),
        confidence: Math.round(avgConfidence)
      };
    } catch (error) {
      console.error('Error calculating prediction accuracy:', error);
      return {
        totalGames: 0,
        correctPredictions: 0,
        accuracy: 0,
        confidence: 0
      };
    }
  }

  /**
   * Get team prediction history
   */
  async getTeamPredictionHistory(team, season = 2025) {
    try {
      const history = [];
      
      // Get predictions for each week
      for (let week = 1; week <= 18; week++) {
        const predictions = await this.getGamePredictions(season, week);
        const teamGames = predictions.filter(game => 
          game.homeTeam === team || game.awayTeam === team
        );
        
        for (const game of teamGames) {
          if (game.prediction) {
            history.push({
              week: game.week,
              opponent: game.homeTeam === team ? game.awayTeam : game.homeTeam,
              isHome: game.homeTeam === team,
              prediction: game.prediction,
              actualResult: game.actualResult || null
            });
          }
        }
      }
      
      return history;
    } catch (error) {
      console.error('Error fetching team prediction history:', error);
      return [];
    }
  }

  /**
   * Get prediction trends
   */
  async getPredictionTrends(season = 2025) {
    try {
      const trends = {
        weeklyAccuracy: [],
        confidenceTrends: [],
        teamPerformance: {}
      };
      
      // Analyze weekly accuracy
      for (let week = 1; week <= 18; week++) {
        const accuracy = await this.getPredictionAccuracy(season, week);
        trends.weeklyAccuracy.push({
          week,
          accuracy: accuracy.accuracy,
          confidence: accuracy.confidence,
          totalGames: accuracy.totalGames
        });
      }
      
      // Analyze team performance
      const teams = ['PHI', 'DAL', 'SF', 'BUF', 'BAL', 'KC', 'GB', 'MIN'];
      for (const team of teams) {
        const history = await this.getTeamPredictionHistory(team, season);
        const correctPredictions = history.filter(h => 
          h.actualResult && h.actualResult.winner === h.prediction.predictedWinner
        ).length;
        
        trends.teamPerformance[team] = {
          totalGames: history.length,
          correctPredictions,
          accuracy: history.length > 0 ? Math.round((correctPredictions / history.length) * 100) : 0,
          avgConfidence: history.length > 0 ? 
            Math.round(history.reduce((sum, h) => sum + h.prediction.confidence, 0) / history.length) : 0
        };
      }
      
      return trends;
    } catch (error) {
      console.error('Error analyzing prediction trends:', error);
      return {
        weeklyAccuracy: [],
        confidenceTrends: [],
        teamPerformance: {}
      };
    }
  }

  /**
   * Clear prediction cache
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
      timeout: this.cacheTimeout
    };
  }
}

// Create singleton instance
const predictionService = new PredictionService();

export default predictionService;
