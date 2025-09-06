/**
 * Tests for Live Game Tracking Service
 */

import liveGameTrackingService from '../liveGameTrackingService';

// Mock the API service
jest.mock('../api', () => ({
  getLiveGames: jest.fn()
}));

// Mock the prediction service
jest.mock('../predictionService', () => ({
  getPredictions: jest.fn()
}));

describe('LiveGameTrackingService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    liveGameTrackingService.stopTracking();
    liveGameTrackingService.activeGames.clear();
    liveGameTrackingService.subscribers.clear();
  });

  afterEach(() => {
    liveGameTrackingService.stopTracking();
  });

  describe('startTracking and stopTracking', () => {
    it('should start and stop tracking', () => {
      expect(liveGameTrackingService.isTracking).toBe(false);
      
      liveGameTrackingService.startTracking();
      expect(liveGameTrackingService.isTracking).toBe(true);
      
      liveGameTrackingService.stopTracking();
      expect(liveGameTrackingService.isTracking).toBe(false);
    });

    it('should not start tracking if already tracking', () => {
      liveGameTrackingService.startTracking();
      const initialInterval = liveGameTrackingService.updateInterval;
      
      liveGameTrackingService.startTracking();
      expect(liveGameTrackingService.updateInterval).toBe(initialInterval);
    });
  });

  describe('generateMockLiveGames', () => {
    it('should generate mock live games', () => {
      const mockGames = liveGameTrackingService.generateMockLiveGames();
      
      expect(Array.isArray(mockGames)).toBe(true);
      expect(mockGames.length).toBeGreaterThan(0);
      
      mockGames.forEach(game => {
        expect(game).toHaveProperty('id');
        expect(game).toHaveProperty('homeTeam');
        expect(game).toHaveProperty('awayTeam');
        expect(game).toHaveProperty('homeScore');
        expect(game).toHaveProperty('awayScore');
        expect(game).toHaveProperty('quarter');
        expect(game).toHaveProperty('timeRemaining');
        expect(game).toHaveProperty('status');
        expect(game).toHaveProperty('possession');
        expect(game).toHaveProperty('down');
        expect(game).toHaveProperty('distance');
        expect(game).toHaveProperty('yardLine');
        expect(game).toHaveProperty('redZone');
        expect(game).toHaveProperty('weather');
        expect(game).toHaveProperty('temperature');
        expect(game).toHaveProperty('windSpeed');
        expect(game).toHaveProperty('gameDate');
        expect(game).toHaveProperty('lastUpdate');
      });
    });
  });

  describe('calculateMomentum', () => {
    it('should calculate home momentum', () => {
      const currentGame = { homeScore: 21, awayScore: 7 };
      const previousGame = { homeScore: 7, awayScore: 7 };
      
      const momentum = liveGameTrackingService.calculateMomentum(currentGame, previousGame);
      expect(momentum).toBe('home_momentum');
    });

    it('should calculate away momentum', () => {
      const currentGame = { homeScore: 7, awayScore: 21 };
      const previousGame = { homeScore: 7, awayScore: 7 };
      
      const momentum = liveGameTrackingService.calculateMomentum(currentGame, previousGame);
      expect(momentum).toBe('away_momentum');
    });

    it('should calculate neutral momentum', () => {
      const currentGame = { homeScore: 14, awayScore: 14 };
      const previousGame = { homeScore: 7, awayScore: 7 };
      
      const momentum = liveGameTrackingService.calculateMomentum(currentGame, previousGame);
      expect(momentum).toBe('neutral');
    });
  });

  describe('calculateExcitementLevel', () => {
    it('should calculate high excitement for high-scoring close games', () => {
      const game = {
        homeScore: 28,
        awayScore: 24,
        quarter: 4,
        redZone: true
      };
      
      const excitement = liveGameTrackingService.calculateExcitementLevel(game);
      expect(excitement).toBeGreaterThan(7);
    });

    it('should calculate low excitement for low-scoring games', () => {
      const game = {
        homeScore: 3,
        awayScore: 0,
        quarter: 1,
        redZone: false
      };
      
      const excitement = liveGameTrackingService.calculateExcitementLevel(game);
      expect(excitement).toBeLessThan(4);
    });
  });

  describe('calculateCompetitiveness', () => {
    it('should calculate high competitiveness for close games', () => {
      const game = {
        homeScore: 21,
        awayScore: 20
      };
      
      const competitiveness = liveGameTrackingService.calculateCompetitiveness(game);
      expect(competitiveness).toBeGreaterThan(0.8);
    });

    it('should calculate low competitiveness for blowouts', () => {
      const game = {
        homeScore: 35,
        awayScore: 0
      };
      
      const competitiveness = liveGameTrackingService.calculateCompetitiveness(game);
      expect(competitiveness).toBeLessThan(0.3);
    });
  });

  describe('parseTimeRemaining', () => {
    it('should parse time correctly', () => {
      const timeData = liveGameTrackingService.parseTimeRemaining('8:42', 2);
      
      expect(timeData).toEqual({
        minutes: 8,
        seconds: 42,
        totalSeconds: 522,
        quarter: 2,
        formatted: '8:42'
      });
    });

    it('should handle null time', () => {
      const timeData = liveGameTrackingService.parseTimeRemaining(null, 1);
      expect(timeData).toBeNull();
    });
  });

  describe('subscribe and notifySubscribers', () => {
    it('should subscribe to game updates', () => {
      const gameId = 'test_game';
      const callback = jest.fn();
      
      const unsubscribe = liveGameTrackingService.subscribe(gameId, callback);
      expect(typeof unsubscribe).toBe('function');
      
      // Simulate game update
      const gameData = { id: gameId, homeScore: 14, awayScore: 10 };
      liveGameTrackingService.activeGames.set(gameId, gameData);
      liveGameTrackingService.notifySubscribers(gameId, gameData);
      
      expect(callback).toHaveBeenCalledWith(gameData);
    });

    it('should unsubscribe from game updates', () => {
      const gameId = 'test_game';
      const callback = jest.fn();
      
      const unsubscribe = liveGameTrackingService.subscribe(gameId, callback);
      unsubscribe();
      
      // Simulate game update
      const gameData = { id: gameId, homeScore: 14, awayScore: 10 };
      liveGameTrackingService.notifySubscribers(gameId, gameData);
      
      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('getGame and getAllGames', () => {
    it('should get specific game', () => {
      const gameId = 'test_game';
      const gameData = { id: gameId, homeScore: 14, awayScore: 10 };
      
      liveGameTrackingService.activeGames.set(gameId, gameData);
      const retrievedGame = liveGameTrackingService.getGame(gameId);
      
      expect(retrievedGame).toEqual(gameData);
    });

    it('should get all games', () => {
      const game1 = { id: 'game1', homeScore: 14, awayScore: 10 };
      const game2 = { id: 'game2', homeScore: 21, awayScore: 17 };
      
      liveGameTrackingService.activeGames.set('game1', game1);
      liveGameTrackingService.activeGames.set('game2', game2);
      
      const allGames = liveGameTrackingService.getAllGames();
      expect(allGames).toHaveLength(2);
      expect(allGames).toContain(game1);
      expect(allGames).toContain(game2);
    });
  });

  describe('getGamesByTeam', () => {
    it('should filter games by team', () => {
      const game1 = { id: 'game1', homeTeam: 'KC', awayTeam: 'BUF' };
      const game2 = { id: 'game2', homeTeam: 'BUF', awayTeam: 'NE' };
      const game3 = { id: 'game3', homeTeam: 'SF', awayTeam: 'DAL' };
      
      liveGameTrackingService.activeGames.set('game1', game1);
      liveGameTrackingService.activeGames.set('game2', game2);
      liveGameTrackingService.activeGames.set('game3', game3);
      
      const kcGames = liveGameTrackingService.getGamesByTeam('KC');
      expect(kcGames).toHaveLength(1);
      expect(kcGames[0]).toEqual(game1);
      
      const bufGames = liveGameTrackingService.getGamesByTeam('BUF');
      expect(bufGames).toHaveLength(2);
    });
  });

  describe('getGamesByStatus', () => {
    it('should filter games by status', () => {
      const game1 = { id: 'game1', status: 'in_progress' };
      const game2 = { id: 'game2', status: 'final' };
      const game3 = { id: 'game3', status: 'in_progress' };
      
      liveGameTrackingService.activeGames.set('game1', game1);
      liveGameTrackingService.activeGames.set('game2', game2);
      liveGameTrackingService.activeGames.set('game3', game3);
      
      const inProgressGames = liveGameTrackingService.getGamesByStatus('in_progress');
      expect(inProgressGames).toHaveLength(2);
      
      const finalGames = liveGameTrackingService.getGamesByStatus('final');
      expect(finalGames).toHaveLength(1);
    });
  });

  describe('getLiveAnalytics', () => {
    it('should return analytics for active games', () => {
      const game1 = {
        id: 'game1',
        status: 'in_progress',
        homeScore: 14,
        awayScore: 10,
        liveMetrics: {
          excitement: 8,
          competitiveness: 0.8
        },
        predictionData: {
          predictionCorrect: true
        }
      };
      
      const game2 = {
        id: 'game2',
        status: 'in_progress',
        homeScore: 21,
        awayScore: 17,
        liveMetrics: {
          excitement: 6,
          competitiveness: 0.6
        },
        predictionData: {
          predictionCorrect: false
        }
      };
      
      liveGameTrackingService.activeGames.set('game1', game1);
      liveGameTrackingService.activeGames.set('game2', game2);
      
      const analytics = liveGameTrackingService.getLiveAnalytics();
      
      expect(analytics.totalGames).toBe(2);
      expect(analytics.inProgressGames).toBe(2);
      expect(analytics.averageExcitement).toBe(7);
      expect(analytics.averageCompetitiveness).toBe(0.7);
      expect(analytics.predictionAccuracy).toBe(0.5);
      expect(analytics.totalPredictions).toBe(2);
      expect(analytics.correctPredictions).toBe(1);
    });

    it('should return zero analytics for no games', () => {
      const analytics = liveGameTrackingService.getLiveAnalytics();
      
      expect(analytics.totalGames).toBe(0);
      expect(analytics.inProgressGames).toBe(0);
      expect(analytics.averageExcitement).toBe(0);
      expect(analytics.averageCompetitiveness).toBe(0);
      expect(analytics.predictionAccuracy).toBe(0);
    });
  });

  describe('getGameHighlights', () => {
    it('should generate game highlights', () => {
      const game = {
        id: 'test_game',
        homeTeam: 'KC',
        awayTeam: 'BUF',
        homeScore: 24,
        awayScore: 21,
        redZone: true,
        possession: 'KC',
        liveMetrics: {
          excitement: 8
        },
        lastUpdate: new Date().toISOString()
      };
      
      liveGameTrackingService.activeGames.set('test_game', game);
      const highlights = liveGameTrackingService.getGameHighlights('test_game');
      
      expect(Array.isArray(highlights)).toBe(true);
      expect(highlights.length).toBeGreaterThan(0);
      
      highlights.forEach(highlight => {
        expect(highlight).toHaveProperty('type');
        expect(highlight).toHaveProperty('message');
        expect(highlight).toHaveProperty('timestamp');
      });
    });

    it('should return empty highlights for non-existent game', () => {
      const highlights = liveGameTrackingService.getGameHighlights('non_existent');
      expect(highlights).toEqual([]);
    });
  });

  describe('cleanupCompletedGames', () => {
    it('should remove completed games', () => {
      const game1 = { id: 'game1', status: 'in_progress' };
      const game2 = { id: 'game2', status: 'final' };
      const game3 = { id: 'game3', status: 'completed' };
      
      liveGameTrackingService.activeGames.set('game1', game1);
      liveGameTrackingService.activeGames.set('game2', game2);
      liveGameTrackingService.activeGames.set('game3', game3);
      
      liveGameTrackingService.cleanupCompletedGames();
      
      const remainingGames = liveGameTrackingService.getAllGames();
      expect(remainingGames).toHaveLength(1);
      expect(remainingGames[0].id).toBe('game1');
    });
  });

  describe('destroy', () => {
    it('should clean up all resources', () => {
      liveGameTrackingService.startTracking();
      liveGameTrackingService.activeGames.set('test', { id: 'test' });
      liveGameTrackingService.subscribe('test', jest.fn());
      
      liveGameTrackingService.destroy();
      
      expect(liveGameTrackingService.isTracking).toBe(false);
      expect(liveGameTrackingService.activeGames.size).toBe(0);
      expect(liveGameTrackingService.subscribers.size).toBe(0);
    });
  });
});
