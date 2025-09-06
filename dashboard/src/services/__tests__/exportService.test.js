/**
 * Tests for Export Service
 * Comprehensive test suite for export functionality
 */

import exportService from '../exportService';

// Mock the API services
jest.mock('../api', () => ({
  getEloRatings: jest.fn(),
  getEloSeasonSummary: jest.fn()
}));

jest.mock('../predictionService', () => ({
  getGamePredictions: jest.fn(),
  getPredictionAccuracy: jest.fn()
}));

jest.mock('../confidenceService', () => ({
  generateConfidenceReport: jest.fn(),
  getConfidenceTrends: jest.fn()
}));

jest.mock('../historicalAnalysisService', () => ({
  compareSeasons: jest.fn(),
  getTeamHistory: jest.fn()
}));

describe('ExportService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('ELO Ratings Export', () => {
    test('should export ELO ratings as CSV', async () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25, pointsFor: 300, pointsAgainst: 250, pointDifferential: 50 }
        ]
      };

      const mockSeasonSummary = {
        totalGames: 16,
        totalTeams: 1
      };

      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);
      getEloSeasonSummary.mockResolvedValue(mockSeasonSummary);

      const result = await exportService.exportEloRatings(2025, 'comprehensive', 'csv');

      expect(typeof result).toBe('string');
      expect(result).toContain('"Team","Rating","Wins","Losses"');
      expect(result).toContain('"PHI","1600","10","6"');
    });

    test('should export ELO ratings as JSON', async () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25 }
        ]
      };

      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);
      getEloSeasonSummary.mockResolvedValue({ totalGames: 16 });

      const result = await exportService.exportEloRatings(2025, 'comprehensive', 'json');

      const parsed = JSON.parse(result);
      expect(parsed).toHaveProperty('metadata');
      expect(parsed).toHaveProperty('summary');
      expect(parsed).toHaveProperty('teams');
      expect(parsed.teams).toHaveLength(1);
      expect(parsed.teams[0].team).toBe('PHI');
    });

    test('should handle API errors', async () => {
      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockRejectedValue(new Error('API Error'));

      await expect(exportService.exportEloRatings(2025, 'comprehensive', 'csv'))
        .rejects.toThrow('API Error');
    });
  });

  describe('Predictions Export', () => {
    test('should export predictions as CSV', async () => {
      const mockPredictions = [
        {
          id: 'game1',
          season: 2025,
          week: 1,
          homeTeam: 'PHI',
          awayTeam: 'DAL',
          gameDate: '2025-01-01T20:00:00Z',
          status: 'scheduled',
          prediction: {
            homeWinProbability: 65,
            awayWinProbability: 35,
            predictedWinner: 'PHI',
            confidence: 75,
            predictedScore: { home: 28, away: 21 },
            ratingDifference: 50,
            homeFieldAdvantage: 25
          }
        }
      ];

      const mockAccuracy = {
        totalGames: 1,
        correctPredictions: 1,
        accuracy: 100,
        confidence: 75
      };

      const { getGamePredictions, getPredictionAccuracy } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);
      getPredictionAccuracy.mockResolvedValue(mockAccuracy);

      const result = await exportService.exportPredictions(2025, 1, 'csv');

      expect(typeof result).toBe('string');
      expect(result).toContain('"Game ID","Season","Week","Home Team","Away Team"');
      expect(result).toContain('"game1","2025","1","PHI","DAL"');
    });

    test('should export predictions as JSON', async () => {
      const mockPredictions = [
        {
          id: 'game1',
          season: 2025,
          week: 1,
          homeTeam: 'PHI',
          awayTeam: 'DAL',
          prediction: { homeWinProbability: 65, awayWinProbability: 35 }
        }
      ];

      const { getGamePredictions, getPredictionAccuracy } = require('../predictionService');
      getGamePredictions.mockResolvedValue(mockPredictions);
      getPredictionAccuracy.mockResolvedValue({ totalGames: 1, correctPredictions: 1, accuracy: 100, confidence: 75 });

      const result = await exportService.exportPredictions(2025, 1, 'json');

      const parsed = JSON.parse(result);
      expect(parsed).toHaveProperty('metadata');
      expect(parsed).toHaveProperty('accuracy');
      expect(parsed).toHaveProperty('predictions');
      expect(parsed.predictions).toHaveLength(1);
    });
  });

  describe('Confidence Analysis Export', () => {
    test('should export confidence analysis', async () => {
      const mockConfidenceReport = {
        summary: { overallCalibration: 85, reliability: 80, sharpness: 70, totalPredictions: 100 },
        bins: [
          { range: '80-100%', label: 'Very High', predictedCount: 20, actualAccuracy: 85, expectedAccuracy: 90, calibrationError: 5, reliability: 90 }
        ],
        recommendations: [
          { type: 'overconfidence', severity: 'medium', message: 'Model is slightly overconfident' }
        ]
      };

      const mockTrends = {
        weeklyCalibration: [
          { week: 1, calibration: 85, reliability: 80, totalPredictions: 8 }
        ],
        confidenceDistribution: { '80-100%': { count: 20, percentage: 20 } },
        accuracyByConfidence: [
          { range: '80-100%', label: 'Very High', count: 20, accuracy: 85, expectedAccuracy: 90 }
        ]
      };

      const { generateConfidenceReport, getConfidenceTrends } = require('../confidenceService');
      generateConfidenceReport.mockResolvedValue(mockConfidenceReport);
      getConfidenceTrends.mockResolvedValue(mockTrends);

      const result = await exportService.exportConfidenceAnalysis(2025, 'json');

      const parsed = JSON.parse(result);
      expect(parsed).toHaveProperty('metadata');
      expect(parsed).toHaveProperty('summary');
      expect(parsed).toHaveProperty('bins');
      expect(parsed).toHaveProperty('recommendations');
      expect(parsed).toHaveProperty('trends');
    });
  });

  describe('Historical Comparison Export', () => {
    test('should export historical comparison', async () => {
      const mockComparison = {
        summary: {
          totalSeasons: 2,
          averageGames: 16,
          averageTeams: 32,
          averageRating: 1500,
          averageSpread: 200
        },
        trends: {
          ratingTrend: 'stable',
          competitiveTrend: 'increasing',
          gameTrend: 'stable',
          teamTrend: 'stable'
        },
        seasons: [
          {
            year: 2024,
            data: {
              totalGames: 16,
              totalTeams: 32,
              averageRating: 1500,
              ratingSpread: 200,
              competitiveBalance: 60,
              topTeam: { team: 'PHI', rating: 1600 },
              bottomTeam: { team: 'DAL', rating: 1400 }
            }
          }
        ]
      };

      const { compareSeasons } = require('../historicalAnalysisService');
      compareSeasons.mockResolvedValue(mockComparison);

      const result = await exportService.exportHistoricalComparison([2024, 2025], 'json');

      const parsed = JSON.parse(result);
      expect(parsed).toHaveProperty('metadata');
      expect(parsed).toHaveProperty('summary');
      expect(parsed).toHaveProperty('trends');
      expect(parsed).toHaveProperty('seasons');
      expect(parsed.seasons).toHaveLength(1);
    });
  });

  describe('Team Analysis Export', () => {
    test('should export team analysis', async () => {
      const mockTeamHistory = {
        team: 'PHI',
        summary: {
          totalSeasons: 2,
          averageRating: 1600,
          highestRating: 1650,
          lowestRating: 1550,
          averageWins: 10,
          averageLosses: 6,
          averageWinPct: 62.5
        },
        trends: {
          ratingTrend: 'increasing',
          performanceTrend: 'increasing',
          consistency: 'consistent',
          ratingVariance: 50
        },
        seasons: [
          { season: 2024, rating: 1600, rank: 1, wins: 10, losses: 6, winPct: 62.5, change: 25 },
          { season: 2025, rating: 1650, rank: 1, wins: 12, losses: 4, winPct: 75.0, change: 50 }
        ]
      };

      const { getTeamHistory } = require('../historicalAnalysisService');
      getTeamHistory.mockResolvedValue(mockTeamHistory);

      const result = await exportService.exportTeamAnalysis('PHI', [2024, 2025], 'json');

      const parsed = JSON.parse(result);
      expect(parsed).toHaveProperty('metadata');
      expect(parsed).toHaveProperty('summary');
      expect(parsed).toHaveProperty('trends');
      expect(parsed).toHaveProperty('seasons');
      expect(parsed.seasons).toHaveLength(2);
    });
  });

  describe('Data Formatting', () => {
    test('should format data as CSV correctly', () => {
      const data = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25, pointsFor: 300, pointsAgainst: 250, pointDifferential: 50 }
        ]
      };

      const result = exportService.formatData(data, 'csv');
      
      expect(typeof result).toBe('string');
      expect(result).toContain('"Team","Rating","Wins","Losses","Win%","Rating Change","Points For","Points Against","Point Differential"');
      expect(result).toContain('"PHI","1600","10","6","62.5","25","300","250","50"');
    });

    test('should format data as JSON correctly', () => {
      const data = { test: 'value', number: 123 };

      const result = exportService.formatData(data, 'json');
      const parsed = JSON.parse(result);

      expect(parsed).toEqual(data);
    });

    test('should handle XLSX format', () => {
      const data = { test: 'value' };
      const result = exportService.formatData(data, 'xlsx');

      expect(result).toHaveProperty('type', 'xlsx');
      expect(result).toHaveProperty('data');
      expect(result).toHaveProperty('note');
    });

    test('should handle PDF format', () => {
      const data = { test: 'value' };
      const result = exportService.formatData(data, 'pdf');

      expect(result).toHaveProperty('type', 'pdf');
      expect(result).toHaveProperty('data');
      expect(result).toHaveProperty('note');
    });

    test('should throw error for unsupported format', () => {
      const data = { test: 'value' };
      
      expect(() => exportService.formatData(data, 'unsupported'))
        .toThrow('Unsupported format: unsupported');
    });
  });

  describe('Configuration Validation', () => {
    test('should validate export configuration', () => {
      const validConfig = {
        type: 'elo-summary',
        format: 'csv',
        season: 2025
      };

      const result = exportService.validateExportConfig(validConfig);
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should reject invalid format', () => {
      const invalidConfig = {
        type: 'elo-summary',
        format: 'invalid',
        season: 2025
      };

      const result = exportService.validateExportConfig(invalidConfig);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Invalid format. Supported formats: csv, json, xlsx, pdf');
    });

    test('should reject invalid report type', () => {
      const invalidConfig = {
        type: 'invalid',
        format: 'csv',
        season: 2025
      };

      const result = exportService.validateExportConfig(invalidConfig);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Invalid report type. Available types: elo-summary, predictions, confidence-analysis, historical-comparison, team-analysis, custom');
    });

    test('should validate ELO summary requirements', () => {
      const invalidConfig = {
        type: 'elo-summary',
        format: 'csv'
        // Missing season
      };

      const result = exportService.validateExportConfig(invalidConfig);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Season is required for ELO summary');
    });

    test('should validate predictions requirements', () => {
      const invalidConfig = {
        type: 'predictions',
        format: 'csv',
        season: 2025
        // Missing week
      };

      const result = exportService.validateExportConfig(invalidConfig);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Season and week are required for predictions');
    });

    test('should validate historical comparison requirements', () => {
      const invalidConfig = {
        type: 'historical-comparison',
        format: 'csv',
        seasons: [2025] // Only one season
      };

      const result = exportService.validateExportConfig(invalidConfig);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('At least 2 seasons are required for historical comparison');
    });

    test('should validate team analysis requirements', () => {
      const invalidConfig = {
        type: 'team-analysis',
        format: 'csv',
        team: 'PHI'
        // Missing seasons
      };

      const result = exportService.validateExportConfig(invalidConfig);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Team and seasons are required for team analysis');
    });
  });

  describe('Utility Functions', () => {
    test('should get supported formats', () => {
      const formats = exportService.getSupportedFormats();
      expect(Array.isArray(formats)).toBe(true);
      expect(formats).toContain('csv');
      expect(formats).toContain('json');
      expect(formats).toContain('xlsx');
      expect(formats).toContain('pdf');
    });

    test('should get report templates', () => {
      const templates = exportService.getReportTemplates();
      expect(typeof templates).toBe('object');
      expect(templates).toHaveProperty('elo-summary');
      expect(templates).toHaveProperty('predictions');
      expect(templates).toHaveProperty('confidence-analysis');
      expect(templates).toHaveProperty('historical-comparison');
      expect(templates).toHaveProperty('team-analysis');
      expect(templates).toHaveProperty('custom');
    });

    test('should generate filename correctly', () => {
      const config = {
        type: 'elo-summary',
        season: 2025,
        format: 'csv'
      };

      const filename = exportService.generateFilename(config.type, config, config.format);
      expect(filename).toContain('elo-ratings-summary');
      expect(filename).toContain('season-2025');
      expect(filename).toContain('.csv');
    });

    test('should get MIME type correctly', () => {
      expect(exportService.getMimeType('csv')).toBe('text/csv');
      expect(exportService.getMimeType('json')).toBe('application/json');
      expect(exportService.getMimeType('xlsx')).toBe('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      expect(exportService.getMimeType('pdf')).toBe('application/pdf');
      expect(exportService.getMimeType('unknown')).toBe('text/plain');
    });

    test('should flatten object correctly', () => {
      const obj = {
        level1: {
          level2: {
            value: 'test'
          },
          array: [1, 2, 3]
        },
        simple: 'value'
      };

      const flattened = exportService.flattenObject(obj);
      expect(flattened['level1.level2.value']).toBe('test');
      expect(flattened['level1.array']).toEqual([1, 2, 3]);
      expect(flattened['simple']).toBe('value');
    });
  });

  describe('Edge Cases', () => {
    test('should handle empty teams data', () => {
      const data = { teams: [] };
      const result = exportService.formatData(data, 'csv');
      
      expect(typeof result).toBe('string');
      expect(result).toContain('"Team","Rating","Wins","Losses"');
    });

    test('should handle null data gracefully', () => {
      const data = null;
      
      // JSON.stringify handles null gracefully
      const result = exportService.formatData(data, 'json');
      expect(result).toBe('null');
    });

    test('should handle missing prediction data', () => {
      const data = {
        predictions: [
          {
            id: 'game1',
            season: 2025,
            week: 1,
            homeTeam: 'PHI',
            awayTeam: 'DAL',
            gameDate: '2025-01-01T20:00:00Z',
            status: 'scheduled'
            // Missing prediction
          }
        ]
      };

      const result = exportService.formatData(data, 'csv');
      expect(typeof result).toBe('string');
      expect(result).toContain('"undefined","2025","1","PHI","DAL"');
    });
  });
});
