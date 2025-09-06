/**
 * Prediction Analytics Component
 * Comprehensive analytics dashboard for prediction performance
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  Activity,
  Calendar,
  Users,
  Zap,
  Award,
  TrendingDown,
  Info
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import predictionAnalyticsService from '../services/predictionAnalyticsService';

const PredictionAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeason, setSelectedSeason] = useState(2025);
  const [selectedWeek, setSelectedWeek] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const report = await predictionAnalyticsService.generateAnalyticsReport(selectedSeason, selectedWeek);
      setAnalytics(report);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSeason, selectedWeek]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const getMetricColor = (value, thresholds) => {
    if (value >= thresholds.excellent) return 'text-green-600';
    if (value >= thresholds.good) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMetricIcon = (value, thresholds) => {
    if (value >= thresholds.excellent) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (value >= thresholds.good) return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
    return <AlertTriangle className="w-5 h-5 text-red-600" />;
  };

  const formatPercentage = (value) => {
    return value ? `${(value * 100).toFixed(1)}%` : 'N/A';
  };

  const formatScore = (value, decimals = 3) => {
    return value ? value.toFixed(decimals) : 'N/A';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-nfl-primary mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading Analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <h2 className="font-bold text-lg mb-2">Error Loading Analytics</h2>
            <p className="text-sm">{error}</p>
            <button 
              onClick={loadAnalytics} 
              className="mt-4 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-gray-600">No analytics data available</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'calibration', name: 'Calibration', icon: Target },
    { id: 'teams', name: 'Team Performance', icon: Users },
    { id: 'trends', name: 'Trends', icon: TrendingUp },
    { id: 'insights', name: 'Insights', icon: Info }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Prediction Analytics</h1>
              <p className="text-gray-600">
                Season {selectedSeason} {selectedWeek ? `- Week ${selectedWeek}` : '(All Weeks)'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={selectedSeason}
                onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-nfl-primary"
              >
                <option value={2025}>2025</option>
                <option value={2024}>2024</option>
                <option value={2023}>2023</option>
                <option value={2022}>2022</option>
              </select>
              <select
                value={selectedWeek || ''}
                onChange={(e) => setSelectedWeek(e.target.value ? parseInt(e.target.value) : null)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-nfl-primary"
              >
                <option value="">All Weeks</option>
                {Array.from({length: 18}, (_, i) => i + 1).map(week => (
                  <option key={week} value={week}>Week {week}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-1 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-nfl-primary text-nfl-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Overall Accuracy</p>
                    <p className={`text-2xl font-bold ${getMetricColor(analytics.overallMetrics.accuracy, { excellent: 0.65, good: 0.55 })}`}>
                      {formatPercentage(analytics.overallMetrics.accuracy)}
                    </p>
                  </div>
                  {getMetricIcon(analytics.overallMetrics.accuracy, { excellent: 0.65, good: 0.55 })}
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Brier Score</p>
                    <p className={`text-2xl font-bold ${getMetricColor(analytics.overallMetrics.brierScore, { excellent: 0.2, good: 0.3 })}`}>
                      {formatScore(analytics.overallMetrics.brierScore)}
                    </p>
                    <p className="text-xs text-gray-500">Lower is better</p>
                  </div>
                  {getMetricIcon(analytics.overallMetrics.brierScore, { excellent: 0.2, good: 0.3 })}
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Log Loss</p>
                    <p className={`text-2xl font-bold ${getMetricColor(analytics.overallMetrics.logLoss, { excellent: 0.5, good: 0.7 })}`}>
                      {formatScore(analytics.overallMetrics.logLoss)}
                    </p>
                    <p className="text-xs text-gray-500">Lower is better</p>
                  </div>
                  {getMetricIcon(analytics.overallMetrics.logLoss, { excellent: 0.5, good: 0.7 })}
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Sharpness</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatScore(analytics.overallMetrics.sharpness, 2)}
                    </p>
                    <p className="text-xs text-gray-500">Confidence level</p>
                  </div>
                  <Zap className="w-5 h-5 text-blue-600" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Resolution</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatScore(analytics.overallMetrics.resolution, 3)}
                    </p>
                    <p className="text-xs text-gray-500">Discrimination ability</p>
                  </div>
                  <Target className="w-5 h-5 text-purple-600" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Weighted Accuracy</p>
                    <p className={`text-2xl font-bold ${getMetricColor(analytics.overallMetrics.confidenceWeightedAccuracy, { excellent: 0.7, good: 0.6 })}`}>
                      {formatPercentage(analytics.overallMetrics.confidenceWeightedAccuracy)}
                    </p>
                    <p className="text-xs text-gray-500">Confidence-weighted</p>
                  </div>
                  <Award className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </div>

            {/* Prediction Count */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Prediction Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-nfl-primary">{analytics.metadata.totalPredictions}</p>
                  <p className="text-sm text-gray-600">Total Predictions</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">
                    {Math.round(analytics.metadata.totalPredictions * (analytics.overallMetrics.accuracy || 0))}
                  </p>
                  <p className="text-sm text-gray-600">Correct Predictions</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">
                    {analytics.calibration?.confidencePerformance?.reduce((sum, level) => sum + level.count, 0) || 0}
                  </p>
                  <p className="text-sm text-gray-600">High Confidence</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-600">
                    {analytics.teamPerformance?.length || 0}
                  </p>
                  <p className="text-sm text-gray-600">Teams Analyzed</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'calibration' && (
          <div className="space-y-6">
            {/* Reliability Diagram */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Reliability Diagram</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart data={analytics.calibration?.reliabilityDiagram}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="binCenter" 
                      name="Expected Accuracy"
                      label={{ value: 'Expected Accuracy', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis 
                      dataKey="accuracy" 
                      name="Actual Accuracy"
                      label={{ value: 'Actual Accuracy', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [value, name === 'accuracy' ? 'Actual Accuracy' : 'Expected Accuracy']}
                      labelFormatter={(label) => `Expected: ${(label * 100).toFixed(1)}%`}
                    />
                    <Scatter 
                      dataKey="accuracy" 
                      fill="#3B82F6" 
                      name="Actual Accuracy"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="binCenter" 
                      stroke="#EF4444" 
                      strokeWidth={2}
                      dot={false}
                      name="Perfect Calibration"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Confidence Performance Table */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Confidence Level Performance</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Confidence Level
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Count
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Accuracy
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Expected
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Calibration Error
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {analytics.calibration?.confidencePerformance?.map((level, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {level.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {level.count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatPercentage(level.accuracy)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatPercentage(level.expectedAccuracy)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatScore(level.calibrationError, 3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'teams' && (
          <div className="space-y-6">
            {/* Team Performance Chart */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Team Prediction Accuracy</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.teamPerformance?.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="team" />
                    <YAxis 
                      label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      formatter={(value) => [formatPercentage(value), 'Accuracy']}
                    />
                    <Bar dataKey="accuracy" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Team Performance Table */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Team Performance</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Team
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Games
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Accuracy
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Confidence
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Home Accuracy
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Away Accuracy
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {analytics.teamPerformance?.map((team, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {team.team}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {team.totalGames}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatPercentage(team.accuracy)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatScore(team.avgConfidence, 2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatPercentage(team.homeAccuracy)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatPercentage(team.awayAccuracy)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="space-y-6">
            {/* Weekly Trends Chart */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Performance Trends</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.temporalTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis 
                      label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [
                        name === 'accuracy' ? formatPercentage(value) : formatScore(value, 2),
                        name === 'accuracy' ? 'Accuracy' : 'Avg Confidence'
                      ]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="accuracy" 
                      stroke="#3B82F6" 
                      strokeWidth={2}
                      name="Accuracy"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avgConfidence" 
                      stroke="#10B981" 
                      strokeWidth={2}
                      name="Avg Confidence"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Model Stability */}
            {analytics.modelStability && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Stability</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">
                      {formatScore(analytics.modelStability.stabilityScore, 2)}
                    </p>
                    <p className="text-sm text-gray-600">Stability Score</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">
                      {formatScore(analytics.modelStability.accuracyStdDev, 3)}
                    </p>
                    <p className="text-sm text-gray-600">Accuracy Std Dev</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">
                      {formatScore(analytics.modelStability.accuracyRange, 3)}
                    </p>
                    <p className="text-sm text-gray-600">Accuracy Range</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">
                      {formatScore(analytics.modelStability.confidenceStdDev, 3)}
                    </p>
                    <p className="text-sm text-gray-600">Confidence Std Dev</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="space-y-6">
            {/* Insights Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {analytics.insights?.map((insight, index) => (
                <div 
                  key={index}
                  className={`p-6 rounded-lg shadow ${
                    insight.type === 'positive' ? 'bg-green-50 border border-green-200' :
                    insight.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                    'bg-blue-50 border border-blue-200'
                  }`}
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      {insight.type === 'positive' ? (
                        <CheckCircle className="w-6 h-6 text-green-600" />
                      ) : insight.type === 'warning' ? (
                        <AlertTriangle className="w-6 h-6 text-yellow-600" />
                      ) : (
                        <Info className="w-6 h-6 text-blue-600" />
                      )}
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-900 capitalize">
                        {insight.category.replace('_', ' ')}
                      </h4>
                      <p className="mt-1 text-sm text-gray-700">
                        {insight.message}
                      </p>
                      <p className="mt-2 text-xs text-gray-600">
                        <strong>Recommendation:</strong> {insight.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Analytics Summary</h3>
              <div className="prose max-w-none">
                <p className="text-gray-700">
                  This analytics report provides comprehensive insights into your prediction model's performance. 
                  The metrics show how well your model is calibrated, which teams are easiest/hardest to predict, 
                  and how performance varies over time. Use these insights to improve your prediction accuracy 
                  and confidence calibration.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PredictionAnalytics;
