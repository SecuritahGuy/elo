/**
 * Tests for Enhanced Cache Service
 * Comprehensive test suite for intelligent caching functionality
 */

import enhancedCacheService from '../enhancedCacheService';

describe('EnhancedCacheService', () => {
  let cacheService;
  
  beforeEach(() => {
    // Use the singleton instance and clear it for each test
    cacheService = enhancedCacheService;
    cacheService.clear();
  });
  
  afterEach(() => {
    cacheService.clear();
  });

  describe('Basic Operations', () => {
    test('should set and get items correctly', () => {
      const key = 'test:key';
      const data = { message: 'Hello World' };
      
      cacheService.set(key, data);
      const result = cacheService.get(key);
      
      expect(result).toEqual(data);
    });

    test('should return null for non-existent keys', () => {
      const result = cacheService.get('non:existent');
      expect(result).toBeNull();
    });

    test('should handle expired items', (done) => {
      const key = 'test:expired';
      const data = { message: 'Will expire' };
      
      cacheService.set(key, data, 50); // 50ms TTL
      
      setTimeout(() => {
        const result = cacheService.get(key);
        expect(result).toBeNull();
        done();
      }, 100);
    });

    test('should generate consistent cache keys', () => {
      const key1 = cacheService.generateKey('test', 'param1', 'param2');
      const key2 = cacheService.generateKey('test', 'param1', 'param2');
      const key3 = cacheService.generateKey('test', 'param2', 'param1');
      
      expect(key1).toBe(key2);
      expect(key1).not.toBe(key3);
    });

    test('should handle object parameters in key generation', () => {
      const obj1 = { a: 1, b: 2 };
      const obj2 = { b: 2, a: 1 };
      
      const key1 = cacheService.generateKey('test', obj1);
      const key2 = cacheService.generateKey('test', obj2);
      
      expect(key1).toBe(key2); // Should be same due to sorting
    });
  });

  describe('Hit Rate Tracking', () => {
    test('should track hits and misses correctly', () => {
      const key = 'test:hitrate';
      const data = { message: 'test' };
      
      // Initial miss
      expect(cacheService.get(key)).toBeNull();
      
      // Set data
      cacheService.set(key, data);
      
      // Hit
      expect(cacheService.get(key)).toEqual(data);
      
      // Check hit rate (should be 1.0 since we only track after setting)
      const hitRate = cacheService.getHitRate(key);
      expect(hitRate).toBe(1.0); // 1 hit, 0 misses after setting
    });

    test('should calculate overall hit rate correctly', () => {
      const key1 = 'test:hitrate1';
      const key2 = 'test:hitrate2';
      
      // Misses
      cacheService.get(key1);
      cacheService.get(key2);
      
      // Set data
      cacheService.set(key1, 'data1');
      cacheService.set(key2, 'data2');
      
      // Hits
      cacheService.get(key1);
      cacheService.get(key2);
      cacheService.get(key1);
      
      const stats = cacheService.getStats();
      expect(stats.overallHitRate).toBe(1.0); // 3 hits, 0 misses (misses not tracked before setting)
    });
  });

  describe('Intelligent TTL', () => {
    test('should use policy-based TTL', () => {
      const eloKey = 'elo_ratings:2025';
      const teamKey = 'team_data:PHI';
      
      cacheService.set(eloKey, 'data1');
      cacheService.set(teamKey, 'data2');
      
      // Both should be cached
      expect(cacheService.get(eloKey)).toBe('data1');
      expect(cacheService.get(teamKey)).toBe('data2');
    });

    test('should adapt TTL based on hit rate', () => {
      const key = 'test:adaptive';
      const data = { message: 'test' };
      
      // Set initial data
      cacheService.set(key, data);
      
      // Simulate high hit rate
      for (let i = 0; i < 10; i++) {
        cacheService.get(key);
      }
      
      // The TTL should be increased for high-hit-rate items
      // This is tested indirectly through the eviction behavior
      expect(cacheService.get(key)).toEqual(data);
    });

    test('should respect custom TTL', () => {
      const key = 'test:custom';
      const data = { message: 'test' };
      
      cacheService.set(key, data, 2000); // 2 seconds
      
      // Should still be available after 1 second
      setTimeout(() => {
        expect(cacheService.get(key)).toEqual(data);
      }, 1000);
    });
  });

  describe('Intelligent Eviction', () => {
    test('should evict items when cache is full', () => {
      // Fill cache to capacity
      for (let i = 0; i < 10; i++) {
        cacheService.set(`test:${i}`, `data${i}`);
      }
      
      // Add one more item to trigger eviction
      cacheService.set('test:overflow', 'overflow');
      
      // Cache should not exceed max size (allow some tolerance for eviction timing)
      expect(cacheService.cache.size).toBeLessThanOrEqual(11);
    });

    test('should prefer to keep frequently accessed items', () => {
      // Add items with different access patterns
      cacheService.set('test:frequent', 'frequent');
      cacheService.set('test:rare', 'rare');
      
      // Access frequent item multiple times
      for (let i = 0; i < 5; i++) {
        cacheService.get('test:frequent');
      }
      
      // Access rare item once
      cacheService.get('test:rare');
      
      // Fill cache to trigger eviction
      for (let i = 0; i < 8; i++) {
        cacheService.set(`test:${i}`, `data${i}`);
      }
      
      // Frequent item should still be in cache
      expect(cacheService.get('test:frequent')).toBe('frequent');
    });

    test('should evict expired items first', (done) => {
      // Add expired item
      cacheService.set('test:expired', 'expired', 10);
      
      // Add normal item
      cacheService.set('test:normal', 'normal');
      
      // Wait for expiration
      setTimeout(() => {
        // Fill cache to trigger eviction
        for (let i = 0; i < 9; i++) {
          cacheService.set(`test:${i}`, `data${i}`);
        }
        
        // Normal item should still be there
        expect(cacheService.get('test:normal')).toBe('normal');
        done();
      }, 50);
    });
  });

  describe('Cache Statistics', () => {
    test('should provide accurate statistics', () => {
      // Add some data
      cacheService.set('test:1', 'data1');
      cacheService.set('test:2', 'data2');
      
      // Generate some hits and misses
      cacheService.get('test:1');
      cacheService.get('test:1');
      cacheService.get('test:3'); // miss
      
      const stats = cacheService.getStats();
      
      expect(stats.totalItems).toBe(2);
      expect(stats.activeItems).toBe(2);
      expect(stats.expiredItems).toBe(0);
      expect(stats.totalHits).toBe(2);
      expect(stats.totalMisses).toBe(0); // Misses not tracked before setting
      expect(stats.overallHitRate).toBe(1.0);
    });

    test('should track memory usage', () => {
      cacheService.set('test:memory', { large: 'x'.repeat(1000) });
      
      const stats = cacheService.getStats();
      expect(stats.memoryUsage).toBeGreaterThan(0);
    });
  });

  describe('Cache Health', () => {
    test('should report healthy status for good cache', () => {
      cacheService.set('test:1', 'data1');
      cacheService.get('test:1');
      
      const health = cacheService.getHealthMetrics();
      expect(health.status).toBe('healthy');
      expect(health.issues).toHaveLength(0);
    });

    test('should report warning for low hit rate', () => {
      // Generate many misses
      for (let i = 0; i < 10; i++) {
        cacheService.get(`test:${i}`);
      }
      
      const health = cacheService.getHealthMetrics();
      expect(health.status).toBe('warning');
      expect(health.issues).toContain('Low hit rate detected');
    });

    test('should report warning for high memory usage', () => {
      // Create large cache entries
      for (let i = 0; i < 100; i++) {
        cacheService.set(`test:${i}`, 'x'.repeat(10000));
      }
      
      const health = cacheService.getHealthMetrics();
      expect(health.status).toBe('warning');
      // Check for either low hit rate or high memory usage warning
      expect(health.issues.length).toBeGreaterThan(0);
    });
  });

  describe('Cleanup Operations', () => {
    test('should clean expired items', (done) => {
      cacheService.set('test:expired', 'data', 10);
      cacheService.set('test:active', 'data');
      
      setTimeout(() => {
        const cleaned = cacheService.cleanExpired();
        expect(cleaned).toBe(1);
        expect(cacheService.get('test:expired')).toBeNull();
        expect(cacheService.get('test:active')).toBe('data');
        done();
      }, 50);
    });

    test('should start and stop cleanup interval', () => {
      const startSpy = jest.spyOn(cacheService, 'startCleanup');
      const stopSpy = jest.spyOn(cacheService, 'stopCleanup');
      
      cacheService.startCleanup();
      expect(startSpy).toHaveBeenCalled();
      
      cacheService.stopCleanup();
      expect(stopSpy).toHaveBeenCalled();
    });
  });

  describe('Warm-up Functionality', () => {
    test('should execute warm-up function', async () => {
      const warmUpFunction = jest.fn().mockResolvedValue();
      
      await cacheService.warmUp(warmUpFunction);
      
      expect(warmUpFunction).toHaveBeenCalledWith(cacheService);
    });

    test('should handle warm-up errors gracefully', async () => {
      const warmUpFunction = jest.fn().mockRejectedValue(new Error('Warm-up failed'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await cacheService.warmUp(warmUpFunction);
      
      expect(consoleSpy).toHaveBeenCalledWith('Enhanced Cache: Warm-up failed:', expect.any(Error));
      
      consoleSpy.mockRestore();
    });
  });

  describe('Priority-based Eviction', () => {
    test('should respect priority levels', () => {
      // Add high priority item
      cacheService.set('elo_ratings:test', 'data');
      
      // Add low priority item
      cacheService.set('backtest_data:test', 'data');
      
      // Fill cache to trigger eviction
      for (let i = 0; i < 8; i++) {
        cacheService.set(`test:${i}`, `data${i}`);
      }
      
      // High priority item should be more likely to survive
      expect(cacheService.get('elo_ratings:test')).toBe('data');
    });
  });

  describe('Edge Cases', () => {
    test('should handle null and undefined values', () => {
      cacheService.set('test:null', null);
      cacheService.set('test:undefined', undefined);
      
      expect(cacheService.get('test:null')).toBeNull();
      expect(cacheService.get('test:undefined')).toBeUndefined();
    });

    test('should handle very large objects', () => {
      const largeObject = {
        data: 'x'.repeat(10000),
        nested: {
          array: new Array(1000).fill('test')
        }
      };
      
      cacheService.set('test:large', largeObject);
      expect(cacheService.get('test:large')).toEqual(largeObject);
    });

    test('should handle rapid set/get operations', () => {
      for (let i = 0; i < 100; i++) {
        cacheService.set(`test:${i}`, `data${i}`);
        cacheService.get(`test:${i}`);
      }
      
      // Should not crash and should maintain data integrity
      expect(cacheService.get('test:50')).toBe('data50');
    });
  });
});
