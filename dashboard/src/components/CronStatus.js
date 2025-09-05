import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Database,
  Activity,
  RefreshCw,
  Calendar,
  Timer
} from 'lucide-react';
import { apiService } from '../services/api';

const CronStatus = () => {
  const [cronData, setCronData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadCronStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Call the cron monitor API
      const response = await apiService.getCronStatus();
      setCronData(response.data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error loading cron status:', err);
      setError('Failed to load cron job status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCronStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadCronStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatRuntime = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error': return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running': return <Activity className="h-5 w-5 text-blue-500 animate-pulse" />;
      default: return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getHealthStatus = (successRate) => {
    if (successRate >= 90) return { status: 'excellent', color: 'green', text: 'Excellent' };
    if (successRate >= 70) return { status: 'good', color: 'yellow', text: 'Good' };
    return { status: 'poor', color: 'red', text: 'Poor' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nfl-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!cronData) {
    return (
      <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
        No cron job data available
      </div>
    );
  }

  const { summary, recent_logs, database_status } = cronData;
  const health = getHealthStatus(summary.success_rate);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cron Job Monitor</h1>
          <p className="text-gray-600">Automated data collection status and performance</p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={loadCronStatus}
            className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Never'}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Runs (24h)</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_runs_24h}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900">{summary.success_rate.toFixed(1)}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Timer className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Runtime</p>
              <p className="text-2xl font-bold text-gray-900">{formatRuntime(summary.avg_runtime_seconds)}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className={`p-2 bg-${health.color}-100 rounded-lg`}>
              <Activity className={`h-6 w-6 text-${health.color}-600`} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Health Status</p>
              <p className={`text-2xl font-bold text-${health.color}-600`}>{health.text}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Database Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center">
              <Database className="h-5 w-5 text-nfl-primary mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Database Status</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Size:</span>
                <span className="font-medium">{database_status.database_size_mb?.toFixed(1) || 0} MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Latest Activity:</span>
                <span className="font-medium">
                  {database_status.latest_activity ? 
                    new Date(database_status.latest_activity).toLocaleString() : 
                    'None'
                  }
                </span>
              </div>
              <div className="space-y-2">
                <span className="text-gray-600">Table Counts:</span>
                {Object.entries(database_status.table_counts || {}).map(([table, count]) => (
                  <div key={table} className="flex justify-between text-sm">
                    <span className="text-gray-500">{table}:</span>
                    <span className="font-medium">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Recent Runs */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center">
              <Calendar className="h-5 w-5 text-nfl-primary mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Recent Runs</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {recent_logs.slice(0, 8).map((log, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(log.status)}
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {log.start_time ? new Date(log.start_time).toLocaleString() : 'Unknown'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {log.file ? log.file.split('/').pop() : 'No file'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {formatRuntime(log.runtime_seconds)}
                    </p>
                    <p className="text-xs text-gray-500 capitalize">
                      {log.status || 'unknown'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Cron Jobs List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Scheduled Cron Jobs</h2>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            {cronData.cron_jobs?.map((job, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <Clock className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <code className="text-sm text-gray-800 break-all">{job}</code>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CronStatus;
