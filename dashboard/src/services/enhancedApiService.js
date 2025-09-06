/**
 * Enhanced API Service with Intelligent Caching
 * Wraps the base API service with advanced caching capabilities
 */

import apiService from './api';
import enhancedCacheService from './enhancedCacheService';

class EnhancedApiService {
  constructor() {
    this.cache = enhancedCacheService;
    this.requestQueue = new Map(); // Prevent duplicate requests
    this.retryConfig = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 10000
    };
  }

  /**
   * Generic cached request method
   */
  async cachedRequest(requestFunction, cacheKey, options = {}) {
    const {
      ttl = null,
      forceRefresh = false,
      retryOnError = true,
      fallbackData = null
    } = options;

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cachedData = this.cache.get(cacheKey);
      if (cachedData !== null) {
        return cachedData;
      }
    }

    // Check if request is already in progress
    if (this.requestQueue.has(cacheKey)) {
      return this.requestQueue.get(cacheKey);
    }

    // Create request promise
    const requestPromise = this._executeRequestWithRetry(
      requestFunction,
      retryOnError,
      fallbackData
    );

    // Store in queue to prevent duplicates
    this.requestQueue.set(cacheKey, requestPromise);

    try {
      const data = await requestPromise;
      
      // Cache the result
      this.cache.set(cacheKey, data, ttl);
      
      return data;
    } catch (error) {
      // Return fallback data if available
      if (fallbackData) {
        console.warn(`API request failed, using fallback data for ${cacheKey}:`, error.message);
        this.cache.set(cacheKey, fallbackData, ttl);
        return fallbackData;
      }
      throw error;
    } finally {
      // Remove from queue
      this.requestQueue.delete(cacheKey);
    }
  }

  /**
   * Execute request with retry logic
   */
  async _executeRequestWithRetry(requestFunction, retryOnError, fallbackData) {
    let lastError;
    
    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        return await requestFunction();
      } catch (error) {
        lastError = error;
        
        if (!retryOnError || attempt === this.retryConfig.maxRetries) {
          break;
        }
        
        // Calculate delay with exponential backoff
        const delay = Math.min(
          this.retryConfig.baseDelay * Math.pow(2, attempt),
          this.retryConfig.maxDelay
        );
        
        console.warn(`API request failed (attempt ${attempt + 1}), retrying in ${delay}ms:`, error.message);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError;
  }

  /**
   * ELO Ratings with intelligent caching
   */
  async getEloRatings(season = 2025, config = 'comprehensive') {
    const cacheKey = this.cache.generateKey('elo_ratings', season, config);
    
    return this.cachedRequest(
      () => apiService.getEloRatings(season, config),
      cacheKey,
      {
        ttl: 10 * 60 * 1000, // 10 minutes
        fallbackData: this._getFallbackEloRatings(season)
      }
    );
  }

  /**
   * Team Rankings with caching
   */
  async getTeamRankings(season = 2025, config = 'comprehensive') {
    const cacheKey = this.cache.generateKey('team_rankings', season, config);
    
    return this.cachedRequest(
      () => apiService.getTeamRankings(season, config),
      cacheKey,
      {
        ttl: 15 * 60 * 1000, // 15 minutes
        fallbackData: this._getFallbackTeamRankings(season)
      }
    );
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return this.cache.getStats();
  }

  /**
   * Get cache health metrics
   */
  getCacheHealth() {
    return this.cache.getHealthMetrics();
  }

  /**
   * Clear specific cache entries
   */
  clearCache(pattern = null) {
    if (pattern) {
      // Clear entries matching pattern
      const keysToDelete = [];
      for (const key of this.cache.cache.keys()) {
        if (key.includes(pattern)) {
          keysToDelete.push(key);
        }
      }
      keysToDelete.forEach(key => this.cache.delete(key));
    } else {
      // Clear all cache
      this.cache.clear();
    }
  }

  // Fallback data methods
  _getFallbackEloRatings(season) {
    return {
      season,
      config: 'comprehensive',
      teams: [],
      lastUpdated: new Date().toISOString(),
      fallback: true
    };
  }

  _getFallbackTeamRankings(season) {
    return {
      season,
      config: 'comprehensive',
      rankings: [],
      lastUpdated: new Date().toISOString(),
      fallback: true
    };
  }
}

// Create singleton instance
const enhancedApiService = new EnhancedApiService();

export default enhancedApiService;