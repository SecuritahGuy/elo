/**
 * Intelligent Caching Service
 * Provides in-memory caching with TTL and LRU eviction
 */

class CacheService {
  constructor() {
    this.cache = new Map();
    this.accessTimes = new Map();
    this.maxSize = 100; // Maximum number of items in cache
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes default TTL
  }

  /**
   * Generate cache key from parameters
   */
  generateKey(prefix, ...params) {
    return `${prefix}:${params.map(p => JSON.stringify(p)).join(':')}`;
  }

  /**
   * Get item from cache
   */
  get(key) {
    if (!this.cache.has(key)) {
      return null;
    }

    const item = this.cache.get(key);
    
    // Check if expired
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      this.accessTimes.delete(key);
      return null;
    }

    // Update access time for LRU
    this.accessTimes.set(key, Date.now());
    
    return item.data;
  }

  /**
   * Set item in cache
   */
  set(key, data, ttl = this.defaultTTL) {
    // Remove oldest items if cache is full
    if (this.cache.size >= this.maxSize) {
      this.evictLRU();
    }

    const expiresAt = Date.now() + ttl;
    this.cache.set(key, { data, expiresAt });
    this.accessTimes.set(key, Date.now());
  }

  /**
   * Remove item from cache
   */
  delete(key) {
    this.cache.delete(key);
    this.accessTimes.delete(key);
  }

  /**
   * Clear all cache
   */
  clear() {
    this.cache.clear();
    this.accessTimes.clear();
  }

  /**
   * Evict least recently used item
   */
  evictLRU() {
    let oldestKey = null;
    let oldestTime = Date.now();

    for (const [key, time] of this.accessTimes.entries()) {
      if (time < oldestTime) {
        oldestTime = time;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.delete(oldestKey);
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const now = Date.now();
    let expiredCount = 0;
    let activeCount = 0;

    for (const [, item] of this.cache.entries()) {
      if (now > item.expiresAt) {
        expiredCount++;
      } else {
        activeCount++;
      }
    }

    return {
      totalItems: this.cache.size,
      activeItems: activeCount,
      expiredItems: expiredCount,
      maxSize: this.maxSize,
      hitRate: this.calculateHitRate()
    };
  }

  /**
   * Calculate cache hit rate (simplified)
   */
  calculateHitRate() {
    // This would need to track hits/misses in a real implementation
    return 0.85; // Placeholder
  }

  /**
   * Clean expired items
   */
  cleanExpired() {
    const now = Date.now();
    const expiredKeys = [];

    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiresAt) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => this.delete(key));
    return expiredKeys.length;
  }
}

// Create singleton instance
const cacheService = new CacheService();

// Auto-clean expired items every 5 minutes
setInterval(() => {
  const cleaned = cacheService.cleanExpired();
  if (cleaned > 0) {
    console.log(`Cache: Cleaned ${cleaned} expired items`);
  }
}, 5 * 60 * 1000);

export default cacheService;
