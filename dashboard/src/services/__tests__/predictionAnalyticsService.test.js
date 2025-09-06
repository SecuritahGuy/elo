/**
 * Tests for Prediction Analytics Service
 */

import predictionAnalyticsService from '../predictionAnalyticsService';

// Mock the API service
jest.mock('../api', () => ({
  getPredictions: jest.fn()
}));

describe('PredictionAnalyticsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    predictionAnalyticsService.clearCache();
  });

  describe('calculateBrierScore', () => {
    it('should calculate Brier score correctly', () => {
      const predictions = [
        { homeWinProb: 0.8, actualWinner: 'home', homeTeam: 'home' },
        { homeWinProb: 0.6, actualWinner: 'away', homeTeam: 'home' },
        { homeWinProb: 0.4, actualWinner: 'away', homeTeam: 'home' }
      ];

      const brierScore = predictionAnalyticsService.calculateBrierScore(predictions);
      
      // Expected: ((0.8-1)² + (0.6-0)² + (0.4-0)²) / 3 = (0.04 + 0.36 + 0.16) / 3 = 0.187
      expect(brierScore).toBeCloseTo(0.187, 3);
    });

    it('should return null for empty predictions', () => {
      const brierScore = predictionAnalyticsService.calculateBrierScore([]);
      expect(brierScore).toBeNull();
    });

    it('should return null for null predictions', () => {
      const brierScore = predictionAnalyticsService.calculateBrierScore(null);
      expect(brierScore).toBeNull();
    });
  });

  describe('calculateLogLoss', () => {
    it('should calculate log loss correctly', () => {
      const predictions = [
        { homeWinProb: 0.9, actualWinner: 'home', homeTeam: 'home' },
        { homeWinProb: 0.1, actualWinner: 'away', homeTeam: 'home' }
      ];

      const logLoss = predictionAnalyticsService.calculateLogLoss(predictions);
      
      // Expected: -(1*ln(0.9) + 0*ln(0.1) + 0*ln(0.1) + 1*ln(0.9)) / 2
      expect(logLoss).toBeCloseTo(0.105, 3);
    });

    it('should handle edge cases with clamping', () => {
      const predictions = [
        { homeWinProb: 0, actualWinner: 'home', homeTeam: 'home' },
        { homeWinProb: 1, actualWinner: 'away', homeTeam: 'home' }
      ];

      const logLoss = predictionAnalyticsService.calculateLogLoss(predictions);
      expect(logLoss).toBeGreaterThan(0);
      expect(Number.isFinite(logLoss)).toBe(true);
    });
  });

  describe('calculateReliabilityDiagram', () => {
    it('should create reliability diagram data', () => {
      const predictions = [
        { homeWinProb: 0.1, actualWinner: 'home', homeTeam: 'home' },
        { homeWinProb: 0.3, actualWinner: 'away', homeTeam: 'home' },
        { homeWinProb: 0.7, actualWinner: 'home', homeTeam: 'home' },
        { homeWinProb: 0.9, actualWinner: 'away', homeTeam: 'home' }
      ];

      const diagram = predictionAnalyticsService.calculateReliabilityDiagram(predictions, 5);
      
      expect(diagram).toHaveLength(4); // 4 bins with data
      expect(diagram[0]).toHaveProperty('binMin');
      expect(diagram[0]).toHaveProperty('binMax');
      expect(diagram[0]).toHaveProperty('count');
      expect(diagram[0]).toHaveProperty('accuracy');
      expect(diagram[0]).toHaveProperty('avgConfidence');
    });
  });

  describe('calculateOverallAccuracy', () => {
    it('should calculate accuracy correctly', () => {
      const predictions = [
        { predictedWinner: 'home', actualWinner: 'home' },
        { predictedWinner: 'away', actualWinner: 'away' },
        { predictedWinner: 'home', actualWinner: 'away' }
      ];

      const accuracy = predictionAnalyticsService.calculateOverallAccuracy(predictions);
      expect(accuracy).toBeCloseTo(0.667, 3);
    });

    it('should return null for empty predictions', () => {
      const accuracy = predictionAnalyticsService.calculateOverallAccuracy([]);
      expect(accuracy).toBeNull();
    });
  });

  describe('calculateConfidenceWeightedAccuracy', () => {
    it('should calculate confidence-weighted accuracy', () => {
      const predictions = [
        { predictedWinner: 'home', actualWinner: 'home', confidence: 0.8 },
        { predictedWinner: 'away', actualWinner: 'away', confidence: 0.6 },
        { predictedWinner: 'home', actualWinner: 'away', confidence: 0.4 }
      ];

      const weightedAccuracy = predictionAnalyticsService.calculateConfidenceWeightedAccuracy(predictions);
      
      // Expected: (0.8*1 + 0.6*1 + 0.4*0) / (0.8 + 0.6 + 0.4) = 1.4 / 1.8 = 0.778
      expect(weightedAccuracy).toBeCloseTo(0.778, 3);
    });
  });

  describe('calculateConfidencePerformance', () => {
    it('should categorize predictions by confidence level', () => {
      const predictions = [
        { confidence: 0.1, predictedWinner: 'home', actualWinner: 'home' },
        { confidence: 0.3, predictedWinner: 'away', actualWinner: 'away' },
        { confidence: 0.5, predictedWinner: 'home', actualWinner: 'home' },
        { confidence: 0.7, predictedWinner: 'away', actualWinner: 'away' },
        { confidence: 0.9, predictedWinner: 'home', actualWinner: 'away' }
      ];

      const performance = predictionAnalyticsService.calculateConfidencePerformance(predictions);
      
      expect(performance).toHaveLength(5);
      expect(performance[0].name).toBe('Very Low');
      expect(performance[4].name).toBe('Very High');
      expect(performance[0].count).toBe(1);
      expect(performance[1].count).toBe(1);
    });
  });

  describe('calculateTeamPerformance', () => {
    it('should calculate team-specific metrics', () => {
      const predictions = [
        { 
          homeTeam: 'KC', 
          awayTeam: 'BUF', 
          predictedWinner: 'KC', 
          actualWinner: 'KC',
          confidence: 0.8
        },
        { 
          homeTeam: 'BUF', 
          awayTeam: 'KC', 
          predictedWinner: 'BUF', 
          actualWinner: 'KC',
          confidence: 0.6
        }
      ];

      const teamPerformance = predictionAnalyticsService.calculateTeamPerformance(predictions);
      
      expect(teamPerformance).toHaveLength(2);
      expect(teamPerformance[0]).toHaveProperty('team');
      expect(teamPerformance[0]).toHaveProperty('totalGames');
      expect(teamPerformance[0]).toHaveProperty('accuracy');
      expect(teamPerformance[0]).toHaveProperty('avgConfidence');
    });
  });

  describe('calculateTemporalTrends', () => {
    it('should calculate weekly trends', () => {
      const predictions = [
        { week: 1, predictedWinner: 'home', actualWinner: 'home', confidence: 0.8 },
        { week: 1, predictedWinner: 'away', actualWinner: 'away', confidence: 0.6 },
        { week: 2, predictedWinner: 'home', actualWinner: 'away', confidence: 0.7 },
        { week: 2, predictedWinner: 'away', actualWinner: 'away', confidence: 0.5 }
      ];

      const trends = predictionAnalyticsService.calculateTemporalTrends(predictions);
      
      expect(trends).toHaveLength(2);
      expect(trends[0].week).toBe(1);
      expect(trends[1].week).toBe(2);
      expect(trends[0]).toHaveProperty('accuracy');
      expect(trends[0]).toHaveProperty('avgConfidence');
    });
  });

  describe('calculateModelStability', () => {
    it('should calculate stability metrics', () => {
      const predictions = [
        { week: 1, predictedWinner: 'home', actualWinner: 'home', confidence: 0.8 },
        { week: 1, predictedWinner: 'away', actualWinner: 'away', confidence: 0.6 },
        { week: 2, predictedWinner: 'home', actualWinner: 'away', confidence: 0.7 },
        { week: 2, predictedWinner: 'away', actualWinner: 'away', confidence: 0.5 }
      ];

      const stability = predictionAnalyticsService.calculateModelStability(predictions);
      
      expect(stability).toHaveProperty('accuracyStdDev');
      expect(stability).toHaveProperty('confidenceStdDev');
      expect(stability).toHaveProperty('stabilityScore');
      expect(stability.stabilityScore).toBeGreaterThanOrEqual(0);
      expect(stability.stabilityScore).toBeLessThanOrEqual(1);
    });
  });

  describe('generateInsights', () => {
    it('should generate insights based on performance', () => {
      const predictions = [
        { homeWinProb: 0.8, actualWinner: 'home', homeTeam: 'home', predictedWinner: 'home', confidence: 0.8 },
        { homeWinProb: 0.6, actualWinner: 'away', homeTeam: 'home', predictedWinner: 'away', confidence: 0.6 },
        { homeWinProb: 0.4, actualWinner: 'away', homeTeam: 'home', predictedWinner: 'away', confidence: 0.4 }
      ];

      const insights = predictionAnalyticsService.generateInsights(predictions);
      
      expect(Array.isArray(insights)).toBe(true);
      insights.forEach(insight => {
        expect(insight).toHaveProperty('type');
        expect(insight).toHaveProperty('category');
        expect(insight).toHaveProperty('message');
        expect(insight).toHaveProperty('recommendation');
      });
    });
  });

  describe('generateAnalyticsReport', () => {
    it('should generate comprehensive analytics report', async () => {
      // Mock the getPredictionData method
      const mockPredictions = [
        { 
          homeWinProb: 0.8, 
          actualWinner: 'home', 
          homeTeam: 'home', 
          predictedWinner: 'home', 
          confidence: 0.8,
          week: 1,
          season: 2025
        }
      ];

      jest.spyOn(predictionAnalyticsService, 'getPredictionData').mockResolvedValue(mockPredictions);

      const report = await predictionAnalyticsService.generateAnalyticsReport(2025, 1);
      
      expect(report).toHaveProperty('metadata');
      expect(report).toHaveProperty('overallMetrics');
      expect(report).toHaveProperty('calibration');
      expect(report).toHaveProperty('teamPerformance');
      expect(report).toHaveProperty('temporalTrends');
      expect(report).toHaveProperty('modelStability');
      expect(report).toHaveProperty('insights');
      
      expect(report.metadata.season).toBe(2025);
      expect(report.metadata.week).toBe(1);
    });

    it('should handle errors gracefully', async () => {
      jest.spyOn(predictionAnalyticsService, 'getPredictionData').mockRejectedValue(new Error('API Error'));

      await expect(predictionAnalyticsService.generateAnalyticsReport(2025, 1))
        .rejects.toThrow('API Error');
    });
  });

  describe('generateMockPredictionData', () => {
    it('should generate mock data for testing', () => {
      const mockData = predictionAnalyticsService.generateMockPredictionData(2025, 1);
      
      expect(Array.isArray(mockData)).toBe(true);
      expect(mockData.length).toBeGreaterThan(0);
      
      mockData.forEach(prediction => {
        expect(prediction).toHaveProperty('season', 2025);
        expect(prediction).toHaveProperty('week', 1);
        expect(prediction).toHaveProperty('homeTeam');
        expect(prediction).toHaveProperty('awayTeam');
        expect(prediction).toHaveProperty('homeWinProb');
        expect(prediction).toHaveProperty('predictedWinner');
        expect(prediction).toHaveProperty('actualWinner');
        expect(prediction).toHaveProperty('confidence');
      });
    });
  });

  describe('cache functionality', () => {
    it('should cache results and return cached data', async () => {
      const mockPredictions = [
        { homeWinProb: 0.8, actualWinner: 'home', homeTeam: 'home', predictedWinner: 'home', confidence: 0.8, week: 1, season: 2025 }
      ];

      jest.spyOn(predictionAnalyticsService, 'getPredictionData').mockResolvedValue(mockPredictions);

      // First call
      const report1 = await predictionAnalyticsService.generateAnalyticsReport(2025, 1);
      
      // Second call should use cache
      const report2 = await predictionAnalyticsService.generateAnalyticsReport(2025, 1);
      
      expect(report1).toEqual(report2);
      expect(predictionAnalyticsService.getPredictionData).toHaveBeenCalledTimes(1);
    });

    it('should clear cache', () => {
      predictionAnalyticsService.clearCache();
      // No assertion needed, just ensure no error is thrown
    });
  });
});
