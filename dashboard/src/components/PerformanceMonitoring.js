import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Clock, 
  Database, 
  Zap, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import enhancedApiService from '../services/enhancedApiService';
import cacheService from '../services/cacheService';

const PerformanceMonitoring = () => {
  const [metrics, setMetrics] = useState({
    cacheStats: null,
    systemStatus: null,
    performanceMetrics: null,
    lastUpdated: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get cache statistics
      const cacheStats = cacheService.getStats();
      
      // Get system status
      const systemResponse = await enhancedApiService.getSystemStatus();
      
      // Get performance metrics (mock for now)
      const performanceMetrics = {
        responseTime: Math.random() * 200 + 50, // 50-250ms
        throughput: Math.random() * 1000 + 500, // 500-1500 req/min
        errorRate: Math.random() * 2, // 0-2%
        uptime: 99.9 + Math.random() * 0.1, // 99.9-100%
        memoryUsage: Math.random() * 30 + 40, // 40-70%
        cpuUsage: Math.random() * 20 + 10 // 10-30%
      };

      setMetrics({
        cacheStats,
        systemStatus: systemResponse.data,
        performanceMetrics,
        lastUpdated: new Date()
      });

    } catch (err) {
      console.error('Error loading performance metrics:', err);
      setError('Failed to load performance metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
    
    // Refresh metrics every 30 seconds
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'critical': return <XCircle className="h-5 w-5 text-red-600" />;
      default: return <Activity className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-nfl-primary mx-auto mb-4" />
          <p className="text-gray-600">Loading performance metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <XCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadMetrics}
            className="px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Performance Monitoring</h1>
          <p className="text-gray-600">Real-time system performance and cache analytics</p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={loadMetrics}
            className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => enhancedApiService.clearCache()}
            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Clear Cache
          </button>
        </div>
      </div>

      {/* System Status */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">System Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center p-4 bg-gray-50 rounded-lg">
            {getStatusIcon(metrics.systemStatus?.status)}
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Overall Status</p>
              <p className={`text-lg font-bold ${getStatusColor(metrics.systemStatus?.status)}`}>
                {metrics.systemStatus?.status?.toUpperCase() || 'UNKNOWN'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center p-4 bg-gray-50 rounded-lg">
            <Database className="h-5 w-5 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Database</p>
              <p className={`text-lg font-bold ${getStatusColor(metrics.systemStatus?.database?.status)}`}>
                {metrics.systemStatus?.database?.status?.toUpperCase() || 'UNKNOWN'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center p-4 bg-gray-50 rounded-lg">
            <Clock className="h-5 w-5 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Last Updated</p>
              <p className="text-lg font-bold text-gray-900">
                {metrics.lastUpdated?.toLocaleTimeString() || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Cache Statistics */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Cache Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {metrics.cacheStats?.totalItems || 0}
            </div>
            <div className="text-sm text-gray-600">Total Items</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {metrics.cacheStats?.activeItems || 0}
            </div>
            <div className="text-sm text-gray-600">Active Items</div>
          </div>
          
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {metrics.cacheStats?.expiredItems || 0}
            </div>
            <div className="text-sm text-gray-600">Expired Items</div>
          </div>
          
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {((metrics.cacheStats?.hitRate || 0) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">Hit Rate</div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Response Times</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-700">Average Response Time</span>
              <span className="font-bold text-gray-900">
                {metrics.performanceMetrics?.responseTime?.toFixed(0)}ms
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-700">Throughput</span>
              <span className="font-bold text-gray-900">
                {metrics.performanceMetrics?.throughput?.toFixed(0)} req/min
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-700">Error Rate</span>
              <span className="font-bold text-gray-900">
                {metrics.performanceMetrics?.errorRate?.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">System Resources</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-700">Uptime</span>
              <span className="font-bold text-green-600">
                {metrics.performanceMetrics?.uptime?.toFixed(2)}%
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-700">Memory Usage</span>
              <span className="font-bold text-gray-900">
                {metrics.performanceMetrics?.memoryUsage?.toFixed(1)}%
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-700">CPU Usage</span>
              <span className="font-bold text-gray-900">
                {metrics.performanceMetrics?.cpuUsage?.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Cache Management */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Cache Management</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Cache Actions</h3>
            <div className="space-y-2">
              <button
                onClick={() => enhancedApiService.clearCache()}
                className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Clear All Cache
              </button>
              <button
                onClick={loadMetrics}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh Metrics
              </button>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Cache Configuration</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>Max Size:</span>
                <span>{metrics.cacheStats?.maxSize || 100} items</span>
              </div>
              <div className="flex justify-between">
                <span>Default TTL:</span>
                <span>5 minutes</span>
              </div>
              <div className="flex justify-between">
                <span>Auto-cleanup:</span>
                <span>Every 5 minutes</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMonitoring;
