import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Activity, Target, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { apiService } from '../services/api';

const Performance = () => {
  const [metrics, setMetrics] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [historicalData, setHistoricalData] = useState([]);

  const loadPerformanceData = async () => {
    try {
      setLoading(true);
      
      // Load performance metrics
      const metricsResponse = await apiService.getPerformanceMetrics();
      setMetrics(metricsResponse.data);
      
      // Load system health
      const healthResponse = await apiService.getSystemHealth();
      setSystemHealth(healthResponse.data);
      
      // Generate sample historical data (in real app, this would come from API)
      const sampleData = generateSampleHistoricalData();
      setHistoricalData(sampleData);
      
    } catch (error) {
      console.error('Failed to load performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateSampleHistoricalData = () => {
    const data = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    for (let i = 0; i < 30; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      
      data.push({
        date: date.toISOString().split('T')[0],
        accuracy: 58 + Math.random() * 8, // 58-66% range
        brierScore: 0.21 + Math.random() * 0.02, // 0.21-0.23 range
        gamesProcessed: Math.floor(Math.random() * 20) + 10, // 10-30 games
        confidence: 0.6 + Math.random() * 0.3 // 0.6-0.9 range
      });
    }
    
    return data;
  };

  useEffect(() => {
    loadPerformanceData();
  }, []);

  const MetricCard = ({ title, value, icon: Icon, color = 'nfl-primary', trend = null }) => (
    <div className="dashboard-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {trend && (
            <div className="flex items-center mt-1">
              <TrendingUp className={`w-4 h-4 ${trend > 0 ? 'text-green-500' : 'text-red-500'}`} />
              <span className={`text-sm ml-1 ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {trend > 0 ? '+' : ''}{trend}%
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-${color} bg-opacity-10`}>
          <Icon className={`w-6 h-6 text-${color}`} />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8"></div>
        <span className="ml-2 text-gray-600">Loading performance data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Performance Metrics</h1>
          <p className="text-gray-600">System performance and accuracy analytics</p>
        </div>
        <button
          onClick={loadPerformanceData}
          className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="System Accuracy"
          value={metrics?.system_accuracy || 'N/A'}
          icon={Target}
          color="nfl-primary"
          trend={2.3}
        />
        <MetricCard
          title="Brier Score"
          value={metrics?.brier_score || 'N/A'}
          icon={BarChart3}
          color="nfl-secondary"
          trend={-1.2}
        />
        <MetricCard
          title="Games Processed"
          value={metrics?.total_games_processed || 'N/A'}
          icon={Activity}
          color="green-600"
          trend={5.7}
        />
        <MetricCard
          title="Log Loss"
          value={metrics?.log_loss || 'N/A'}
          icon={TrendingUp}
          color="purple-600"
          trend={-0.8}
        />
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Accuracy Trend */}
        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Accuracy Trend (30 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                domain={[50, 70]}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value) => [`${value.toFixed(1)}%`, 'Accuracy']}
              />
              <Line 
                type="monotone" 
                dataKey="accuracy" 
                stroke="#013369" 
                strokeWidth={2}
                dot={{ fill: '#013369', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Brier Score Trend */}
        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Brier Score Trend (30 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                domain={[0.20, 0.25]}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => value.toFixed(3)}
              />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value) => [value.toFixed(4), 'Brier Score']}
              />
              <Line 
                type="monotone" 
                dataKey="brierScore" 
                stroke="#D50A0A" 
                strokeWidth={2}
                dot={{ fill: '#D50A0A', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Health */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">System Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <Activity className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Overall Status</p>
            <p className="text-lg font-semibold text-green-600">
              {systemHealth?.status || 'Unknown'}
            </p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600">Teams Loaded</p>
            <p className="text-2xl font-bold text-blue-600">
              {systemHealth?.metrics?.teams_loaded || 'N/A'}
            </p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-gray-600">Data Quality</p>
            <p className="text-lg font-semibold text-purple-600">
              {metrics?.data_quality?.completeness || 'N/A'}
            </p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-sm text-gray-600">Last Validation</p>
            <p className="text-sm font-semibold text-yellow-600">
              {metrics?.data_quality?.last_validation || 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Component Status */}
      {systemHealth?.components && (
        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Component Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(systemHealth.components).map(([component, status]) => (
              <div key={component} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-700 capitalize">
                  {component.replace('_', ' ')}
                </span>
                <span className={`status-indicator ${
                  status === 'operational' ? 'status-healthy' : 'status-error'
                }`}>
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Summary */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Performance Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Current Performance</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Accuracy:</span>
                <span className="font-semibold">{metrics?.system_accuracy || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Brier Score:</span>
                <span className="font-semibold">{metrics?.brier_score || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Log Loss:</span>
                <span className="font-semibold">{metrics?.log_loss || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Games Processed:</span>
                <span className="font-semibold">{metrics?.total_games_processed || 'N/A'}</span>
              </div>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Data Quality</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Completeness:</span>
                <span className="font-semibold text-green-600">
                  {metrics?.data_quality?.completeness || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Accuracy:</span>
                <span className="font-semibold text-green-600">
                  {metrics?.data_quality?.accuracy || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Last Validation:</span>
                <span className="font-semibold">
                  {metrics?.data_quality?.last_validation || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Performance;
