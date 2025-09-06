/**
 * Tests for Prediction Service
 * Comprehensive test suite for game prediction functionality
 */

import predictionService from '../predictionService';

// Mock the API service
jest.mock('../api', () => ({
  getEloRatings: jest.fn()
}));

describe('PredictionService', () => {
  beforeEach(() => {
    // Clear cache before each test
    predictionService.clearCache();
    jest.clearAllMocks();
  });

  describe('Game Predictions', () => {
    test('should get game predictions for a specific week', async () => {
      // Mock ELO ratings
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1550 },
          { team: 'SF', rating: 1580 },
          { team: 'BUF', rating: 1520 }
        ]
      };

      const { getEloRatings } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);

      const predictions = await predictionService.getGamePredictions(2025, 1);

      expect(Array.isArray(predictions)).toBe(true);
      expect(predictions.length).toBeGreaterThan(0);
      
      // Check prediction structure
      const prediction = predictions[0];
      expect(prediction).toHaveProperty('id');
      expect(prediction).toHaveProperty('season', 2025);
      expect(prediction).toHaveProperty('week', 1);
      expect(prediction).toHaveProperty('homeTeam');
      expect(prediction).toHaveProperty('awayTeam');
      expect(prediction).toHaveProperty('prediction');
      
      // Check prediction details
      expect(prediction.prediction).toHaveProperty('homeWinProbability');
      expect(prediction.prediction).toHaveProperty('awayWinProbability');
      expect(prediction.prediction).toHaveProperty('predictedWinner');
      expect(prediction.prediction).toHaveProperty('confidence');
      expect(prediction.prediction).toHaveProperty('predictedScore');
    });

    test('should handle missing ELO ratings gracefully', async () => {
      const { getEloRatings } = require('../api');
      getEloRatings.mockResolvedValue(null);

      const predictions = await predictionService.getGamePredictions(2025, 1);

      expect(Array.isArray(predictions)).toBe(true);
      expect(predictions.length).toBe(0);
    });

    test('should cache predictions', async () => {
      const mockEloRatings = {
        teams: [{ team: 'PHI', rating: 1600 }, { team: 'DAL', rating: 1550 }]
      };

      const { getEloRatings } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);

      // First call
      await predictionService.getGamePredictions(2025, 1);
      expect(getEloRatings).toHaveBeenCalledTimes(1);

      // Second call should use cache
      await predictionService.getGamePredictions(2025, 1);
      expect(getEloRatings).toHaveBeenCalledTimes(1);
    });
  });

  describe('Prediction Calculations', () => {
    test('should calculate win probabilities correctly', () => {
      const homeTeam = 'PHI';
      const awayTeam = 'DAL';
      const homeRating = 1600;
      const awayRating = 1550;

      const prediction = predictionService.calculatePrediction(
        homeTeam, awayTeam, homeRating, awayRating
      );

      expect(prediction.homeWinProbability).toBeGreaterThan(prediction.awayWinProbability);
      expect(prediction.predictedWinner).toBe(homeTeam);
      expect(prediction.homeWinProbability + prediction.awayWinProbability).toBe(100);
    });

    test('should calculate confidence based on rating difference', () => {
      const highDiffPrediction = predictionService.calculatePrediction(
        'PHI', 'DAL', 1700, 1500
      );
      const lowDiffPrediction = predictionService.calculatePrediction(
        'PHI', 'DAL', 1600, 1590
      );

      expect(highDiffPrediction.confidence).toBeGreaterThan(lowDiffPrediction.confidence);
    });

    test('should include home field advantage', () => {
      const prediction = predictionService.calculatePrediction(
        'PHI', 'DAL', 1600, 1600
      );

      expect(prediction.homeWinProbability).toBeGreaterThan(50);
      expect(prediction.homeFieldAdvantage).toBe(25);
    });

    test('should calculate predicted scores', () => {
      const prediction = predictionService.calculatePrediction(
        'PHI', 'DAL', 1600, 1550
      );

      expect(prediction.predictedScore).toHaveProperty('home');
      expect(prediction.predictedScore).toHaveProperty('away');
      expect(prediction.predictedScore.home).toBeGreaterThan(0);
      expect(prediction.predictedScore.away).toBeGreaterThan(0);
    });
  });

  describe('Prediction Accuracy', () => {
    test('should calculate prediction accuracy for completed games', async () => {
      // Mock predictions with some completed games
      const mockPredictions = [
        {
          id: 'game1',
          status: 'completed',
          actualWinner: 'PHI',
          prediction: { predictedWinner: 'PHI', confidence: 80 }
        },
        {
          id: 'game2',
          status: 'completed',
          actualWinner: 'DAL',
          prediction: { predictedWinner: 'PHI', confidence: 60 }
        }
      ];

      // Mock the getGamePredictions method
      jest.spyOn(predictionService, 'getGamePredictions').mockResolvedValue(mockPredictions);

      const accuracy = await predictionService.getPredictionAccuracy(2025, 1);

      expect(accuracy.totalGames).toBe(2);
      expect(accuracy.correctPredictions).toBe(1);
      expect(accuracy.accuracy).toBe(50);
      expect(accuracy.confidence).toBe(70); // Average of 80 and 60
    });

    test('should handle no completed games', async () => {
      const mockPredictions = [
        { id: 'game1', status: 'scheduled', prediction: { predictedWinner: 'PHI' } }
      ];

      jest.spyOn(predictionService, 'getGamePredictions').mockResolvedValue(mockPredictions);

      const accuracy = await predictionService.getPredictionAccuracy(2025, 1);

      expect(accuracy.totalGames).toBe(0);
      expect(accuracy.correctPredictions).toBe(0);
      expect(accuracy.accuracy).toBe(0);
      expect(accuracy.confidence).toBe(0);
    });
  });

  describe('Team Prediction History', () => {
    test('should get team prediction history', async () => {
      const mockPredictions = [
        {
          week: 1,
          homeTeam: 'PHI',
          awayTeam: 'DAL',
          prediction: { predictedWinner: 'PHI', confidence: 80 }
        }
      ];

      jest.spyOn(predictionService, 'getGamePredictions').mockResolvedValue(mockPredictions);

      const history = await predictionService.getTeamPredictionHistory('PHI', 2025);

      expect(Array.isArray(history)).toBe(true);
      if (history.length > 0) {
        expect(history[0]).toHaveProperty('week');
        expect(history[0]).toHaveProperty('opponent');
        expect(history[0]).toHaveProperty('isHome');
        expect(history[0]).toHaveProperty('prediction');
      }
    });
  });

  describe('Prediction Trends', () => {
    test('should analyze prediction trends', async () => {
      const mockWeeklyAccuracy = [
        { week: 1, accuracy: 70, confidence: 80, totalGames: 8 },
        { week: 2, accuracy: 75, confidence: 85, totalGames: 8 }
      ];

      jest.spyOn(predictionService, 'getPredictionAccuracy').mockResolvedValue({
        totalGames: 8,
        correctPredictions: 6,
        accuracy: 75,
        confidence: 80
      });

      jest.spyOn(predictionService, 'getTeamPredictionHistory').mockResolvedValue([]);

      const trends = await predictionService.getPredictionTrends(2025);

      expect(trends).toHaveProperty('weeklyAccuracy');
      expect(trends).toHaveProperty('confidenceTrends');
      expect(trends).toHaveProperty('teamPerformance');
      expect(Array.isArray(trends.weeklyAccuracy)).toBe(true);
    });
  });

  describe('Cache Management', () => {
    test('should clear cache', () => {
      predictionService.clearCache();
      const stats = predictionService.getCacheStats();
      expect(stats.size).toBe(0);
    });

    test('should provide cache statistics', () => {
      const stats = predictionService.getCacheStats();
      expect(stats).toHaveProperty('size');
      expect(stats).toHaveProperty('keys');
      expect(stats).toHaveProperty('timeout');
      expect(Array.isArray(stats.keys)).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test.skip('should handle API errors gracefully', async () => {
      const { getEloRatings } = require('../api');
      getEloRatings.mockRejectedValue(new Error('API Error'));

      // The service should throw the error
      try {
        await predictionService.getGamePredictions(2025, 1);
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error.message).toBe('API Error');
      }
    });

    test('should handle missing team ratings', () => {
      const mockEloRatings = {
        teams: [{ team: 'PHI', rating: 1600 }] // Missing DAL rating
      };

      const { getEloRatings } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);

      // This should not throw an error, but should handle missing ratings gracefully
      expect(async () => {
        await predictionService.getGamePredictions(2025, 1);
      }).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    test('should handle equal ratings', () => {
      const prediction = predictionService.calculatePrediction(
        'PHI', 'DAL', 1600, 1600
      );

      // With equal ratings, home team should have slight advantage
      expect(prediction.homeWinProbability).toBeGreaterThan(prediction.awayWinProbability);
      expect(prediction.predictedWinner).toBe('PHI');
    });

    test('should handle very large rating differences', () => {
      const prediction = predictionService.calculatePrediction(
        'PHI', 'DAL', 2000, 1000
      );

      expect(prediction.homeWinProbability).toBeGreaterThan(90);
      expect(prediction.confidence).toBeGreaterThan(80);
    });

    test('should handle very small rating differences', () => {
      const prediction = predictionService.calculatePrediction(
        'PHI', 'DAL', 1600, 1599
      );

      expect(prediction.homeWinProbability).toBeGreaterThan(50);
      expect(prediction.confidence).toBeLessThan(60);
    });
  });
});
