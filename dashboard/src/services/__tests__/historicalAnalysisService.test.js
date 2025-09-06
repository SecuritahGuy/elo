/**
 * Tests for Historical Analysis Service
 * Comprehensive test suite for historical analysis functionality
 */

import historicalAnalysisService from '../historicalAnalysisService';

// Mock the API service
jest.mock('../api', () => ({
  getEloRatings: jest.fn(),
  getEloSeasonSummary: jest.fn()
}));

describe('HistoricalAnalysisService', () => {
  beforeEach(() => {
    // Clear cache before each test
    historicalAnalysisService.clearCache();
    jest.clearAllMocks();
  });

  describe('Season Comparison', () => {
    test('should compare multiple seasons', async () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25 },
          { team: 'DAL', rating: 1550, wins: 8, losses: 8, winPct: 50.0, ratingChange: -15 }
        ]
      };

      const mockSeasonSummary = {
        totalGames: 16,
        totalTeams: 2
      };

      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);
      getEloSeasonSummary.mockResolvedValue(mockSeasonSummary);

      const comparison = await historicalAnalysisService.compareSeasons([2024, 2025]);

      expect(comparison).toHaveProperty('seasons');
      expect(comparison).toHaveProperty('summary');
      expect(comparison).toHaveProperty('trends');
      expect(comparison).toHaveProperty('generatedAt');
      expect(Array.isArray(comparison.seasons)).toBe(true);
      expect(comparison.seasons).toHaveLength(2);
    });

    test('should handle API errors gracefully', async () => {
      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockRejectedValue(new Error('API Error'));
      getEloSeasonSummary.mockRejectedValue(new Error('API Error'));

      const comparison = await historicalAnalysisService.compareSeasons([2024]);

      expect(comparison.seasons[0].data).toHaveProperty('error', 'API Error');
      expect(comparison.seasons[0].data.totalGames).toBe(0);
      expect(comparison.seasons[0].data.totalTeams).toBe(0);
    });

    test('should cache comparison results', async () => {
      const mockEloRatings = {
        teams: [{ team: 'PHI', rating: 1600 }]
      };

      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);
      getEloSeasonSummary.mockResolvedValue({ totalGames: 16 });

      // First call
      await historicalAnalysisService.compareSeasons([2024]);
      expect(getEloRatings).toHaveBeenCalledTimes(1);

      // Second call should use cache
      await historicalAnalysisService.compareSeasons([2024]);
      expect(getEloRatings).toHaveBeenCalledTimes(1);
    });
  });

  describe('Season Analysis', () => {
    test('should analyze a single season', async () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25 },
          { team: 'DAL', rating: 1550, wins: 8, losses: 8, winPct: 50.0, ratingChange: -15 }
        ]
      };

      const mockSeasonSummary = {
        totalGames: 16,
        totalTeams: 2
      };

      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);
      getEloSeasonSummary.mockResolvedValue(mockSeasonSummary);

      const analysis = await historicalAnalysisService.analyzeSeason(2024);

      expect(analysis).toHaveProperty('season', 2024);
      expect(analysis).toHaveProperty('totalGames', 16);
      expect(analysis).toHaveProperty('totalTeams', 2);
      expect(analysis).toHaveProperty('averageRating');
      expect(analysis).toHaveProperty('ratingSpread');
      expect(analysis).toHaveProperty('topTeam');
      expect(analysis).toHaveProperty('bottomTeam');
      expect(analysis).toHaveProperty('competitiveBalance');
      expect(analysis).toHaveProperty('ratingDistribution');
      expect(analysis).toHaveProperty('teamRankings');
    });

    test('should calculate average rating correctly', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1400 }
        ]
      };

      const averageRating = historicalAnalysisService.calculateAverageRating(mockEloRatings);
      expect(averageRating).toBe(1500);
    });

    test('should calculate rating spread correctly', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1400 }
        ]
      };

      const spread = historicalAnalysisService.calculateRatingSpread(mockEloRatings);
      expect(spread).toBe(200);
    });

    test('should get top team correctly', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1400 }
        ]
      };

      const topTeam = historicalAnalysisService.getTopTeam(mockEloRatings);
      expect(topTeam.team).toBe('PHI');
      expect(topTeam.rating).toBe(1600);
    });

    test('should get bottom team correctly', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1400 }
        ]
      };

      const bottomTeam = historicalAnalysisService.getBottomTeam(mockEloRatings);
      expect(bottomTeam.team).toBe('DAL');
      expect(bottomTeam.rating).toBe(1400);
    });

    test('should calculate competitive balance', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1400 }
        ]
      };

      const balance = historicalAnalysisService.calculateCompetitiveBalance(mockEloRatings);
      expect(balance).toBeGreaterThan(0);
      expect(balance).toBeLessThanOrEqual(100);
    });

    test('should calculate rating distribution', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1400 },
          { team: 'SF', rating: 1700 }
        ]
      };

      const distribution = historicalAnalysisService.calculateRatingDistribution(mockEloRatings);
      expect(distribution).toHaveProperty('1400-1500');
      expect(distribution).toHaveProperty('1500-1600');
      expect(distribution).toHaveProperty('1600-1700');
      expect(distribution).toHaveProperty('1700-1800');
      expect(distribution).toHaveProperty('1800+');
    });

    test('should generate team rankings', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25 },
          { team: 'DAL', rating: 1550, wins: 8, losses: 8, winPct: 50.0, ratingChange: -15 }
        ]
      };

      const rankings = historicalAnalysisService.generateTeamRankings(mockEloRatings);
      expect(Array.isArray(rankings)).toBe(true);
      expect(rankings).toHaveLength(2);
      expect(rankings[0].rank).toBe(1);
      expect(rankings[0].team).toBe('PHI');
      expect(rankings[1].rank).toBe(2);
      expect(rankings[1].team).toBe('DAL');
    });
  });

  describe('Team History', () => {
    test('should get team historical performance', async () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25 }
        ]
      };

      const { getEloRatings } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);

      const teamHistory = await historicalAnalysisService.getTeamHistory('PHI', [2024, 2025]);

      expect(teamHistory).toHaveProperty('team', 'PHI');
      expect(teamHistory).toHaveProperty('seasons');
      expect(teamHistory).toHaveProperty('summary');
      expect(teamHistory).toHaveProperty('trends');
      expect(Array.isArray(teamHistory.seasons)).toBe(true);
    });

    test('should get team rank correctly', () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600 },
          { team: 'DAL', rating: 1550 }
        ]
      };

      const rank = historicalAnalysisService.getTeamRank('PHI', mockEloRatings);
      expect(rank).toBe(1);
    });

    test('should generate team summary', () => {
      const teamHistory = [
        { season: 2024, rating: 1600, wins: 10, losses: 6, winPct: 62.5, rank: 1 },
        { season: 2025, rating: 1650, wins: 12, losses: 4, winPct: 75.0, rank: 1 }
      ];

      const summary = historicalAnalysisService.generateTeamSummary(teamHistory);

      expect(summary).toHaveProperty('totalSeasons', 2);
      expect(summary).toHaveProperty('averageRating');
      expect(summary).toHaveProperty('highestRating');
      expect(summary).toHaveProperty('lowestRating');
      expect(summary).toHaveProperty('averageWins');
      expect(summary).toHaveProperty('averageLosses');
      expect(summary).toHaveProperty('averageWinPct');
      expect(summary).toHaveProperty('bestSeason');
      expect(summary).toHaveProperty('worstSeason');
    });

    test('should analyze team trends', () => {
      const teamHistory = [
        { season: 2024, rating: 1600, winPct: 62.5 },
        { season: 2025, rating: 1650, winPct: 75.0 }
      ];

      const trends = historicalAnalysisService.analyzeTeamTrends(teamHistory);

      expect(trends).toHaveProperty('ratingTrend');
      expect(trends).toHaveProperty('performanceTrend');
      expect(trends).toHaveProperty('consistency');
      expect(trends).toHaveProperty('ratingVariance');
    });
  });

  describe('Trend Analysis', () => {
    test('should calculate trend direction correctly', () => {
      const increasingValues = [100, 110, 120, 130];
      const decreasingValues = [130, 120, 110, 100];
      const stableValues = [100, 102, 98, 101];

      expect(historicalAnalysisService.calculateTrend(increasingValues)).toBe('increasing');
      expect(historicalAnalysisService.calculateTrend(decreasingValues)).toBe('decreasing');
      expect(historicalAnalysisService.calculateTrend(stableValues)).toBe('stable');
    });

    test('should handle insufficient data for trends', () => {
      const insufficientData = [100];

      expect(historicalAnalysisService.calculateTrend(insufficientData)).toBe('insufficient_data');
    });
  });

  describe('League Evolution', () => {
    test('should analyze league evolution', async () => {
      const mockEloRatings = {
        teams: [
          { team: 'PHI', rating: 1600, wins: 10, losses: 6, winPct: 62.5, ratingChange: 25 }
        ]
      };

      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockResolvedValue(mockEloRatings);
      getEloSeasonSummary.mockResolvedValue({ totalGames: 16 });

      const evolution = await historicalAnalysisService.getLeagueEvolution([2024, 2025]);

      expect(evolution).toHaveProperty('timeSpan');
      expect(evolution).toHaveProperty('leagueMetrics');
      expect(evolution).toHaveProperty('teamEvolution');
      expect(evolution).toHaveProperty('competitiveEvolution');
      expect(evolution).toHaveProperty('generatedAt');
    });

    test('should handle insufficient data for evolution', async () => {
      const { getEloRatings, getEloSeasonSummary } = require('../api');
      getEloRatings.mockRejectedValue(new Error('No data'));
      getEloSeasonSummary.mockRejectedValue(new Error('No data'));

      const evolution = await historicalAnalysisService.getLeagueEvolution([2024]);

      expect(evolution).toHaveProperty('error', 'Insufficient data for evolution analysis');
    });
  });

  describe('Cache Management', () => {
    test('should clear cache', () => {
      historicalAnalysisService.clearCache();
      const stats = historicalAnalysisService.getCacheStats();
      expect(stats.size).toBe(0);
    });

    test('should provide cache statistics', () => {
      const stats = historicalAnalysisService.getCacheStats();
      expect(stats).toHaveProperty('size');
      expect(stats).toHaveProperty('keys');
      expect(stats).toHaveProperty('timeout');
      expect(Array.isArray(stats.keys)).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    test('should handle empty team data', () => {
      const emptyEloRatings = { teams: [] };

      expect(historicalAnalysisService.calculateAverageRating(emptyEloRatings)).toBe(0);
      expect(historicalAnalysisService.calculateRatingSpread(emptyEloRatings)).toBe(0);
      expect(historicalAnalysisService.getTopTeam(emptyEloRatings)).toBeNull();
      expect(historicalAnalysisService.getBottomTeam(emptyEloRatings)).toBeNull();
      expect(historicalAnalysisService.calculateCompetitiveBalance(emptyEloRatings)).toBe(0);
    });

    test('should handle null team data', () => {
      expect(historicalAnalysisService.calculateAverageRating(null)).toBe(0);
      expect(historicalAnalysisService.calculateRatingSpread(null)).toBe(0);
      expect(historicalAnalysisService.getTopTeam(null)).toBeNull();
      expect(historicalAnalysisService.getBottomTeam(null)).toBeNull();
      expect(historicalAnalysisService.calculateCompetitiveBalance(null)).toBe(0);
    });

    test('should handle single team data', () => {
      const singleTeamRatings = {
        teams: [{ team: 'PHI', rating: 1600 }]
      };

      expect(historicalAnalysisService.calculateAverageRating(singleTeamRatings)).toBe(1600);
      expect(historicalAnalysisService.calculateRatingSpread(singleTeamRatings)).toBe(0);
      expect(historicalAnalysisService.getTopTeam(singleTeamRatings).team).toBe('PHI');
      expect(historicalAnalysisService.getBottomTeam(singleTeamRatings).team).toBe('PHI');
    });

    test('should handle empty team history', () => {
      const summary = historicalAnalysisService.generateTeamSummary([]);

      expect(summary.totalSeasons).toBe(0);
      expect(summary.averageRating).toBe(0);
      expect(summary.highestRating).toBe(0);
      expect(summary.lowestRating).toBe(0);
    });
  });
});
