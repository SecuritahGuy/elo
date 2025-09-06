/**
 * Tests for Confidence Service
 * Comprehensive test suite for confidence calibration functionality
 */

import confidenceService from '../confidenceService';

// Mock the prediction service
jest.mock('../predictionService', () => ({
  getGamePredictions: jest.fn()
}));

describe('ConfidenceService', () => {
  beforeEach(() => {
    // Clear calibration data before each test
    confidenceService.clearCalibrationData();
    jest.clearAllMocks();
  });

  describe('Confidence Calibration', () => {
    test('should calibrate confidence scores', async () => {
      // Mock historical predictions
      const mockPredictions = [
        {
          prediction: { confidence: 80, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        },
        {
          prediction: { confidence: 80, predictedWinner: 'DAL' },
          actualWinner: 'DAL'
        },
        {
          prediction: { confidence: 60, predictedWinner: 'PHI' },
          actualWinner: 'DAL'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const calibration = await confidenceService.calibrateConfidence(2025);

      expect(calibration).toHaveProperty('bins');
      expect(calibration).toHaveProperty('overallCalibration');
      expect(calibration).toHaveProperty('reliability');
      expect(calibration).toHaveProperty('sharpness');
      expect(calibration).toHaveProperty('recommendations');
      expect(Array.isArray(calibration.bins)).toBe(true);
    });

    test('should handle empty predictions gracefully', async () => {
      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue([]);

      const calibration = await confidenceService.calibrateConfidence(2025);

      expect(calibration.overallCalibration).toBe(0);
      expect(calibration.reliability).toBe(0);
      expect(calibration.sharpness).toBe(0);
    });

    test('should calculate calibration metrics correctly', async () => {
      // Mock predictions with known accuracy
      const mockPredictions = [
        {
          prediction: { confidence: 80, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        },
        {
          prediction: { confidence: 80, predictedWinner: 'DAL' },
          actualWinner: 'DAL'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const calibration = await confidenceService.calibrateConfidence(2025);

      // Should have high calibration for 80% confidence bin
      const highConfidenceBin = calibration.bins.find(bin => bin.range === '80-100%');
      expect(highConfidenceBin).toBeDefined();
      expect(highConfidenceBin.actualAccuracy).toBeGreaterThanOrEqual(0);
      expect(highConfidenceBin.expectedAccuracy).toBe(90);
    });
  });

  describe('Confidence Bins', () => {
    test('should analyze confidence bins correctly', async () => {
      const mockPredictions = [
        {
          prediction: { confidence: 85, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        },
        {
          prediction: { confidence: 75, predictedWinner: 'DAL' },
          actualWinner: 'DAL'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const bin = { min: 80, max: 100, label: 'Very High' };
      const binData = await confidenceService.analyzeConfidenceBin(bin, 2025);

      expect(binData).toHaveProperty('range', '80-100%');
      expect(binData).toHaveProperty('label', 'Very High');
      expect(binData).toHaveProperty('predictedCount');
      expect(binData).toHaveProperty('actualAccuracy');
      expect(binData).toHaveProperty('expectedAccuracy');
      expect(binData).toHaveProperty('calibrationError');
      expect(binData).toHaveProperty('reliability');
    });

    test('should handle empty confidence bins', async () => {
      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue([]);

      const bin = { min: 80, max: 100, label: 'Very High' };
      const binData = await confidenceService.analyzeConfidenceBin(bin, 2025);

      expect(binData.predictedCount).toBe(0);
      expect(binData.actualAccuracy).toBe(0);
    });
  });

  describe('Calibrated Confidence', () => {
    test('should return raw confidence when no calibration data', () => {
      const rawConfidence = 75;
      const calibrated = confidenceService.getCalibratedConfidence(rawConfidence, 2025);

      expect(calibrated.raw).toBe(rawConfidence);
      expect(calibrated.calibrated).toBe(rawConfidence);
      expect(calibrated.adjustment).toBe(0);
    });

    test('should apply calibration adjustments', async () => {
      // First calibrate the service
      const mockPredictions = [
        {
          prediction: { confidence: 80, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      await confidenceService.calibrateConfidence(2025);

      // Now test calibrated confidence
      const calibrated = confidenceService.getCalibratedConfidence(80, 2025);

      expect(calibrated.raw).toBe(80);
      expect(calibrated.calibrated).toBeDefined();
      expect(calibrated.label).toBeDefined();
      expect(calibrated.adjustment).toBeDefined();
    });
  });

  describe('Confidence Labels and Colors', () => {
    test('should return correct confidence labels', () => {
      expect(confidenceService.getConfidenceLabel(90)).toBe('Very High');
      expect(confidenceService.getConfidenceLabel(70)).toBe('High');
      expect(confidenceService.getConfidenceLabel(50)).toBe('Medium');
      expect(confidenceService.getConfidenceLabel(30)).toBe('Low');
      expect(confidenceService.getConfidenceLabel(10)).toBe('Very Low');
    });

    test('should return correct confidence colors', () => {
      expect(confidenceService.getConfidenceColor(90)).toContain('green');
      expect(confidenceService.getConfidenceColor(70)).toContain('yellow');
      expect(confidenceService.getConfidenceColor(50)).toContain('orange');
      expect(confidenceService.getConfidenceColor(30)).toContain('red');
    });

    test('should return correct confidence icons', () => {
      expect(confidenceService.getConfidenceIcon(90)).toBe('🎯');
      expect(confidenceService.getConfidenceIcon(70)).toBe('📊');
      expect(confidenceService.getConfidenceIcon(50)).toBe('⚠️');
      expect(confidenceService.getConfidenceIcon(30)).toBe('❓');
    });
  });

  describe('Confidence Report', () => {
    test('should generate confidence report', async () => {
      const mockPredictions = [
        {
          prediction: { confidence: 80, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const report = await confidenceService.generateConfidenceReport(2025);

      expect(report).toHaveProperty('season', 2025);
      expect(report).toHaveProperty('generatedAt');
      expect(report).toHaveProperty('summary');
      expect(report).toHaveProperty('bins');
      expect(report).toHaveProperty('recommendations');
      expect(report).toHaveProperty('status');
      expect(Array.isArray(report.bins)).toBe(true);
      expect(Array.isArray(report.recommendations)).toBe(true);
    });

    test('should include proper summary metrics', async () => {
      const mockPredictions = [
        {
          prediction: { confidence: 80, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const report = await confidenceService.generateConfidenceReport(2025);

      expect(report.summary).toHaveProperty('overallCalibration');
      expect(report.summary).toHaveProperty('reliability');
      expect(report.summary).toHaveProperty('sharpness');
      expect(report.summary).toHaveProperty('totalPredictions');
    });
  });

  describe('Confidence Trends', () => {
    test('should analyze confidence trends', async () => {
      const mockPredictions = [
        {
          prediction: { confidence: 80, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const trends = await confidenceService.getConfidenceTrends(2025);

      expect(trends).toHaveProperty('weeklyCalibration');
      expect(trends).toHaveProperty('confidenceDistribution');
      expect(trends).toHaveProperty('accuracyByConfidence');
      expect(Array.isArray(trends.weeklyCalibration)).toBe(true);
    });

    test('should handle weekly calibration calculation', async () => {
      const mockPredictions = [
        {
          prediction: { confidence: 80, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const weeklyCalibration = await confidenceService.calculateWeeklyCalibration(2025, 1);

      expect(weeklyCalibration).toHaveProperty('calibration');
      expect(weeklyCalibration).toHaveProperty('reliability');
      expect(weeklyCalibration).toHaveProperty('totalPredictions');
    });
  });

  describe('Recommendations', () => {
    test('should generate overconfidence recommendations', async () => {
      // Mock overconfident predictions
      const mockPredictions = [
        {
          prediction: { confidence: 90, predictedWinner: 'PHI' },
          actualWinner: 'DAL' // Wrong prediction with high confidence
        },
        {
          prediction: { confidence: 85, predictedWinner: 'DAL' },
          actualWinner: 'PHI' // Wrong prediction with high confidence
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const calibration = await confidenceService.calibrateConfidence(2025);

      const overconfidenceRecs = calibration.recommendations.filter(rec => 
        rec.type === 'overconfidence'
      );

      expect(overconfidenceRecs.length).toBeGreaterThan(0);
      expect(overconfidenceRecs[0].severity).toBe('high');
    });

    test('should generate low sharpness recommendations', async () => {
      // Mock low confidence predictions
      const mockPredictions = [
        {
          prediction: { confidence: 45, predictedWinner: 'PHI' },
          actualWinner: 'PHI'
        },
        {
          prediction: { confidence: 50, predictedWinner: 'DAL' },
          actualWinner: 'DAL'
        }
      ];

      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);

      const calibration = await confidenceService.calibrateConfidence(2025);

      const lowSharpnessRecs = calibration.recommendations.filter(rec => 
        rec.type === 'low_sharpness'
      );

      expect(lowSharpnessRecs.length).toBeGreaterThan(0);
    });
  });

  describe('Cache Management', () => {
    test('should clear calibration data', () => {
      confidenceService.clearCalibrationData();
      const stats = confidenceService.getCalibrationStats();
      expect(stats.totalCalibrations).toBe(0);
    });

    test('should provide calibration statistics', () => {
      const stats = confidenceService.getCalibrationStats();
      expect(stats).toHaveProperty('calibratedSeasons');
      expect(stats).toHaveProperty('totalCalibrations');
      expect(stats).toHaveProperty('confidenceBins');
      expect(Array.isArray(stats.calibratedSeasons)).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test.skip('should handle prediction service errors', async () => {
      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockRejectedValue(new Error('Prediction service error'));

      await expect(confidenceService.calibrateConfidence(2025))
        .rejects.toThrow('Prediction service error');
    });

    test('should handle missing calibration data gracefully', () => {
      const calibrated = confidenceService.getCalibratedConfidence(80, 2025);
      expect(calibrated.raw).toBe(80);
      expect(calibrated.calibrated).toBe(80);
    });
  });

  describe('Edge Cases', () => {
    test('should handle confidence scores at bin boundaries', () => {
      expect(confidenceService.getConfidenceLabel(80)).toBe('High');
      expect(confidenceService.getConfidenceLabel(79)).toBe('High');
      expect(confidenceService.getConfidenceLabel(60)).toBe('Medium');
      expect(confidenceService.getConfidenceLabel(59)).toBe('Medium');
    });

    test('should handle extreme confidence scores', () => {
      expect(confidenceService.getConfidenceLabel(0)).toBe('Very Low');
      expect(confidenceService.getConfidenceLabel(100)).toBe('Very High');
      expect(confidenceService.getConfidenceLabel(150)).toBe('Unknown');
    });

    test('should handle empty prediction arrays', async () => {
      const { getGamePredictions } = require('../predictionService');
      getGamePredictions.mockResolvedValue([]);

      const calibration = await confidenceService.calibrateConfidence(2025);
      expect(calibration.overallCalibration).toBe(0);
      expect(calibration.reliability).toBe(0);
      expect(calibration.sharpness).toBe(0);
    });
  });
});
