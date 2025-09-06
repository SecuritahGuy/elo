/**
 * Enhanced Intelligent Caching Service
 * Advanced caching with adaptive TTL, hit rate tracking, and smart eviction
 */

class EnhancedCacheService {
  constructor(options = {}) {
    this.cache = new Map();
    this.accessTimes = new Map();
    this.hitCounts = new Map();
    this.missCounts = new Map();
    this.creationTimes = new Map();
    
    // Configuration
    this.maxSize = options.maxSize || 500;
    this.defaultTTL = options.defaultTTL || 5 * 60 * 1000; // 5 minutes
    this.adaptiveTTL = options.adaptiveTTL !== false; // Enable by default
    this.cleanupInterval = options.cleanupInterval || 2 * 60 * 1000; // 2 minutes
    this.maxAge = options.maxAge || 30 * 60 * 1000; // 30 minutes max age
    
    // Cache policies
    this.policies = {
      'elo_ratings': { ttl: 10 * 60 * 1000, priority: 'high' }, // 10 minutes
      'team_data': { ttl: 15 * 60 * 1000, priority: 'high' }, // 15 minutes
      'injury_data': { ttl: 30 * 60 * 1000, priority: 'medium' }, // 30 minutes
      'expert_picks': { ttl: 5 * 60 * 1000, priority: 'high' }, // 5 minutes
      'backtest_data': { ttl: 60 * 60 * 1000, priority: 'low' }, // 1 hour
      'system_status': { ttl: 2 * 60 * 1000, priority: 'high' }, // 2 minutes
      'default': { ttl: this.defaultTTL, priority: 'medium' }
    };
    
    // Start cleanup interval
    this.startCleanup();
  }

  /**
   * Generate cache key from parameters
   */
  generateKey(prefix, ...params) {
    const normalizedParams = params.map(p => {
      if (typeof p === 'object' && p !== null) {
        return JSON.stringify(p, Object.keys(p).sort());
      }
      return JSON.stringify(p);
    });
    return `${prefix}:${normalizedParams.join(':')}`;
  }

  /**
   * Get item from cache with hit tracking
   */
  get(key) {
    if (!this.cache.has(key)) {
      this.recordMiss(key);
      return null;
    }

    const item = this.cache.get(key);
    
    // Check if expired
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      this.accessTimes.delete(key);
      this.creationTimes.delete(key);
      this.recordMiss(key);
      return null;
    }

    // Update access tracking
    this.accessTimes.set(key, Date.now());
    this.hitCounts.set(key, (this.hitCounts.get(key) || 0) + 1);
    
    return item.data;
  }

  /**
   * Set item in cache with intelligent TTL
   */
  set(key, data, customTTL = null) {
    // Determine TTL based on key prefix and usage patterns
    const ttl = this.calculateTTL(key, customTTL);
    
    // Remove oldest items if cache is full
    if (this.cache.size >= this.maxSize) {
      this.evictIntelligent();
    }

    const now = Date.now();
    const expiresAt = now + ttl;
    
    this.cache.set(key, { data, expiresAt });
    this.accessTimes.set(key, now);
    this.creationTimes.set(key, now);
    
    // Initialize hit/miss counts
    if (!this.hitCounts.has(key)) {
      this.hitCounts.set(key, 0);
      this.missCounts.set(key, 0);
    }
  }

  /**
   * Calculate intelligent TTL based on key patterns and usage
   */
  calculateTTL(key, customTTL) {
    if (customTTL) return customTTL;
    
    // Extract prefix from key
    const prefix = key.split(':')[0];
    const policy = this.policies[prefix] || this.policies['default'];
    
    let baseTTL = policy.ttl;
    
    // Adaptive TTL based on hit rate
    if (this.adaptiveTTL) {
      const hitRate = this.getHitRate(key);
      if (hitRate > 0.8) {
        baseTTL *= 1.5; // Increase TTL for frequently accessed items
      } else if (hitRate < 0.2) {
        baseTTL *= 0.7; // Decrease TTL for rarely accessed items
      }
    }
    
    return Math.min(baseTTL, this.maxAge);
  }

  /**
   * Get hit rate for a specific key
   */
  getHitRate(key) {
    const hits = this.hitCounts.get(key) || 0;
    const misses = this.missCounts.get(key) || 0;
    const total = hits + misses;
    return total > 0 ? hits / total : 0;
  }

  /**
   * Record cache miss
   */
  recordMiss(key) {
    this.missCounts.set(key, (this.missCounts.get(key) || 0) + 1);
  }

  /**
   * Intelligent eviction based on multiple factors
   */
  evictIntelligent() {
    const now = Date.now();
    const candidates = [];
    
    for (const [key, item] of this.cache.entries()) {
      const accessTime = this.accessTimes.get(key) || 0;
      const creationTime = this.creationTimes.get(key) || 0;
      const hitRate = this.getHitRate(key);
      const age = now - creationTime;
      const timeSinceAccess = now - accessTime;
      
      // Calculate eviction score (lower is better to keep)
      const score = this.calculateEvictionScore({
        hitRate,
        age,
        timeSinceAccess,
        priority: this.getPriority(key),
        isExpired: now > item.expiresAt
      });
      
      candidates.push({ key, score, accessTime, creationTime });
    }
    
    // Sort by eviction score (highest first)
    candidates.sort((a, b) => b.score - a.score);
    
    // Remove top 10% of candidates
    const toRemove = Math.max(1, Math.floor(candidates.length * 0.1));
    for (let i = 0; i < toRemove; i++) {
      this.delete(candidates[i].key);
    }
  }

  /**
   * Calculate eviction score for intelligent eviction
   */
  calculateEvictionScore({ hitRate, age, timeSinceAccess, priority, isExpired }) {
    let score = 0;
    
    // Expired items get highest priority for removal
    if (isExpired) return 1000;
    
    // Lower hit rate = higher eviction score
    score += (1 - hitRate) * 30;
    
    // Older items = higher eviction score
    score += Math.min(age / (60 * 1000), 20); // Cap at 20 minutes
    
    // Longer since access = higher eviction score
    score += Math.min(timeSinceAccess / (5 * 60 * 1000), 15); // Cap at 15 minutes
    
    // Priority adjustment
    const priorityMultiplier = {
      'high': 0.5,
      'medium': 1.0,
      'low': 1.5
    };
    score *= priorityMultiplier[priority] || 1.0;
    
    return score;
  }

  /**
   * Get priority for a key based on prefix
   */
  getPriority(key) {
    const prefix = key.split(':')[0];
    const policy = this.policies[prefix] || this.policies['default'];
    return policy.priority;
  }

  /**
   * Remove item from cache
   */
  delete(key) {
    this.cache.delete(key);
    this.accessTimes.delete(key);
    this.creationTimes.delete(key);
    this.hitCounts.delete(key);
    this.missCounts.delete(key);
  }

  /**
   * Clear all cache
   */
  clear() {
    this.cache.clear();
    this.accessTimes.clear();
    this.creationTimes.clear();
    this.hitCounts.clear();
    this.missCounts.clear();
  }

  /**
   * Get comprehensive cache statistics
   */
  getStats() {
    const now = Date.now();
    let expiredCount = 0;
    let activeCount = 0;
    let totalHits = 0;
    let totalMisses = 0;
    const hitRates = [];
    
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiresAt) {
        expiredCount++;
      } else {
        activeCount++;
      }
      
      const hits = this.hitCounts.get(key) || 0;
      const misses = this.missCounts.get(key) || 0;
      totalHits += hits;
      totalMisses += misses;
      
      if (hits + misses > 0) {
        hitRates.push(hits / (hits + misses));
      }
    }
    
    const avgHitRate = hitRates.length > 0 
      ? hitRates.reduce((a, b) => a + b, 0) / hitRates.length 
      : 0;
    
    const overallHitRate = totalHits + totalMisses > 0 
      ? totalHits / (totalHits + totalMisses) 
      : 0;
    
    return {
      totalItems: this.cache.size,
      activeItems: activeCount,
      expiredItems: expiredCount,
      maxSize: this.maxSize,
      totalHits,
      totalMisses,
      overallHitRate: Math.round(overallHitRate * 100) / 100,
      avgHitRate: Math.round(avgHitRate * 100) / 100,
      memoryUsage: this.estimateMemoryUsage(),
      policies: Object.keys(this.policies).length
    };
  }

  /**
   * Estimate memory usage (rough calculation)
   */
  estimateMemoryUsage() {
    let totalSize = 0;
    for (const [key, item] of this.cache.entries()) {
      totalSize += key.length * 2; // Rough estimate for string
      totalSize += JSON.stringify(item.data).length * 2; // Rough estimate for data
    }
    return Math.round(totalSize / 1024); // KB
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

  /**
   * Start automatic cleanup
   */
  startCleanup() {
    if (this.cleanupIntervalId) {
      clearInterval(this.cleanupIntervalId);
    }
    
    this.cleanupIntervalId = setInterval(() => {
      const cleaned = this.cleanExpired();
      if (cleaned > 0) {
        console.log(`Enhanced Cache: Cleaned ${cleaned} expired items`);
      }
    }, this.cleanupInterval);
  }

  /**
   * Stop automatic cleanup
   */
  stopCleanup() {
    if (this.cleanupIntervalId) {
      clearInterval(this.cleanupIntervalId);
      this.cleanupIntervalId = null;
    }
  }

  /**
   * Warm up cache with frequently accessed data
   */
  async warmUp(warmUpFunction) {
    try {
      console.log('Enhanced Cache: Starting warm-up...');
      await warmUpFunction(this);
      console.log('Enhanced Cache: Warm-up completed');
    } catch (error) {
      console.error('Enhanced Cache: Warm-up failed:', error);
    }
  }

  /**
   * Get cache health metrics
   */
  getHealthMetrics() {
    const stats = this.getStats();
    const health = {
      status: 'healthy',
      issues: []
    };
    
    if (stats.overallHitRate < 0.5) {
      health.status = 'warning';
      health.issues.push('Low hit rate detected');
    }
    
    if (stats.activeItems / stats.maxSize > 0.9) {
      health.status = 'warning';
      health.issues.push('Cache near capacity');
    }
    
    if (stats.memoryUsage > 10000) { // 10MB
      health.status = 'warning';
      health.issues.push('High memory usage');
    }
    
    if (stats.expiredItems > stats.activeItems) {
      health.status = 'warning';
      health.issues.push('Many expired items');
    }
    
    return health;
  }
}

// Create singleton instance
const enhancedCacheService = new EnhancedCacheService();

export default enhancedCacheService;
