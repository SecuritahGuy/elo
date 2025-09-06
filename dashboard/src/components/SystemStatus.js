import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import apiService from '../services/api';

const SystemStatus = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [configuration, setConfiguration] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadSystemData = async () => {
    try {
      setLoading(true);
      
      const [statusResponse, healthResponse, configResponse] = await Promise.all([
        apiService.getSystemStatus(),
        apiService.getSystemHealth(),
        apiService.getConfiguration()
      ]);
      
      setSystemStatus(statusResponse.data);
      setSystemHealth(healthResponse.data);
      setConfiguration(configResponse.data);
      
    } catch (error) {
      console.error('Failed to load system data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSystemData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadSystemData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ready':
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'warning':
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'error':
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ready':
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8"></div>
        <span className="ml-2 text-gray-600">Loading system status...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Status</h1>
          <p className="text-gray-600">NFL Elo system health and configuration</p>
        </div>
        <button
          onClick={loadSystemData}
          className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="dashboard-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overall Status</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemStatus?.status || 'Unknown'}
              </p>
            </div>
            {getStatusIcon(systemStatus?.status)}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Teams Loaded</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemStatus?.details?.num_teams || 'N/A'}
              </p>
            </div>
            <Activity className="w-6 h-6 text-nfl-primary" />
          </div>
        </div>

        <div className="dashboard-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemHealth?.status || 'Unknown'}
              </p>
            </div>
            {getStatusIcon(systemHealth?.status)}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Last Updated</p>
              <p className="text-sm font-bold text-gray-900">
                {systemStatus?.details?.last_updated ? 
                  new Date(systemStatus.details.last_updated).toLocaleTimeString() : 
                  'N/A'
                }
              </p>
            </div>
            <RefreshCw className="w-6 h-6 text-nfl-secondary" />
          </div>
        </div>
      </div>

      {/* System Health Details */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">System Health Details</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <Activity className="w-5 h-5 text-nfl-primary mr-3" />
              <div>
                <p className="font-semibold text-gray-900">Overall Status</p>
                <p className="text-sm text-gray-600">System operational status</p>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(systemHealth?.status)}`}>
              {systemHealth?.status || 'Unknown'}
            </span>
          </div>

          {systemHealth?.components && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900">Component Status</h3>
              {Object.entries(systemHealth.components).map(([component, status]) => (
                <div key={component} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <Activity className="w-4 h-4 text-gray-600 mr-3" />
                    <span className="font-medium text-gray-700 capitalize">
                      {component.replace('_', ' ')}
                    </span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    status === 'operational' ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                  }`}>
                    {status}
                  </span>
                </div>
              ))}
            </div>
          )}

          {systemHealth?.metrics && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900">System Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(systemHealth.metrics).map(([metric, value]) => (
                  <div key={metric} className="flex justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium text-gray-700 capitalize">
                      {metric.replace('_', ' ')}
                    </span>
                    <span className="text-gray-900">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Configuration Details */}
      {configuration && (
        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">System Configuration</h2>
          <div className="space-y-6">
            {/* Core Parameters */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Core Parameters</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Base Rating</p>
                  <p className="text-lg font-bold text-gray-900">
                    {configuration.configuration.base_rating}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">K Factor</p>
                  <p className="text-lg font-bold text-gray-900">
                    {configuration.configuration.k_factor}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">HFA Points</p>
                  <p className="text-lg font-bold text-gray-900">
                    {configuration.configuration.hfa_points}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Preseason Regress</p>
                  <p className="text-lg font-bold text-gray-900">
                    {configuration.configuration.preseason_regress}
                  </p>
                </div>
              </div>
            </div>

            {/* Feature Status */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Feature Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(configuration.configuration.features).map(([feature, enabled]) => (
                  <div key={feature} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium text-gray-700 capitalize">
                      {feature.replace('_', ' ')}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      enabled ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                    }`}>
                      {enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* System Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">System Information</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Configuration Last Updated:</span>
                  <span className="font-semibold">
                    {configuration.last_updated ? 
                      new Date(configuration.last_updated).toLocaleString() : 
                      'N/A'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">MOV Enabled:</span>
                  <span className="font-semibold">
                    {configuration.configuration.mov_enabled ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Messages */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">System Messages</h2>
        <div className="space-y-3">
          <div className="flex items-start p-3 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5" />
            <div>
              <p className="font-semibold text-green-800">System Operational</p>
              <p className="text-sm text-green-700">
                All components are functioning normally. The NFL Elo system is ready for predictions.
              </p>
            </div>
          </div>
          
          <div className="flex items-start p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <Activity className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
            <div>
              <p className="font-semibold text-blue-800">Real-time Updates</p>
              <p className="text-sm text-blue-700">
                System automatically refreshes data every 30 seconds to ensure up-to-date information.
              </p>
            </div>
          </div>
          
          <div className="flex items-start p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
            <div>
              <p className="font-semibold text-yellow-800">Configuration Note</p>
              <p className="text-sm text-yellow-700">
                Only Travel and QB adjustments are currently enabled based on performance testing results.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
