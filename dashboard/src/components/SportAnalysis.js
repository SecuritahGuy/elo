import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Target, Award, Activity, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';

const SportAnalysis = ({ sport = 'nfl' }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('overview');

  useEffect(() => {
    fetchAnalysis();
  }, [selectedMetric]);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      const response = await apiService.getNFLDashboard();
      const data = response.data;
      
      // Create mock analysis data based on available data
      const mockAnalysis = {
        overview: {
          totalGames: data.games?.length || 0,
          totalTeams: data.teams?.length || 0,
          activeExperts: data.experts?.length || 0,
          totalPicks: data.picks?.length || 0
        },
        performance: {
          accuracy: 0.68,
          avgConfidence: 0.72,
          topPerformer: 'Expert A',
          recentTrend: '+5.2%'
        },
        trends: {
          homeAdvantage: 0.54,
          favoriteCover: 0.48,
          overUnder: 0.52,
          avgSpread: 3.2
        },
        insights: [
          'Home teams have a slight advantage this season',
          'Underdogs are covering the spread more often',
          'Weather conditions affecting outdoor games',
          'Injury reports impacting line movements'
        ]
      };
      
      setAnalysis(mockAnalysis);
      setError(null);
    } catch (err) {
      console.error('Error fetching analysis:', err);
      setError('Failed to load analysis data');
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center text-red-600">
          <AlertCircle className="w-5 h-5 mr-2" />
          {error}
        </div>
      </div>
    );
  }

  const metrics = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'performance', name: 'Performance', icon: TrendingUp },
    { id: 'trends', name: 'Trends', icon: Target },
    { id: 'insights', name: 'Insights', icon: Activity }
  ];

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-purple-600" />
            {sport.toUpperCase()} Analysis
          </h2>
          <div className="flex space-x-1">
            {metrics.map((metric) => (
              <button
                key={metric.id}
                onClick={() => setSelectedMetric(metric.id)}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  selectedMetric === metric.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                <metric.icon className="w-4 h-4 inline mr-1" />
                {metric.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="p-6">
        {selectedMetric === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <Award className="w-8 h-8 text-blue-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-blue-600">Total Teams</p>
                  <p className="text-2xl font-bold text-blue-900">{analysis.overview.totalTeams}</p>
                </div>
              </div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-green-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-600">Total Games</p>
                  <p className="text-2xl font-bold text-green-900">{analysis.overview.totalGames}</p>
                </div>
              </div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <Award className="w-8 h-8 text-purple-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-purple-600">Active Experts</p>
                  <p className="text-2xl font-bold text-purple-900">{analysis.overview.activeExperts}</p>
                </div>
              </div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center">
                <Target className="w-8 h-8 text-orange-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-orange-600">Total Picks</p>
                  <p className="text-2xl font-bold text-orange-900">{analysis.overview.totalPicks}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedMetric === 'performance' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Prediction Accuracy</h3>
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold text-gray-900">
                    {formatPercentage(analysis.performance.accuracy)}
                  </span>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Overall</p>
                    <p className="text-xs text-green-600">+2.1% vs last month</p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Confidence</h3>
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold text-gray-900">
                    {formatPercentage(analysis.performance.avgConfidence)}
                  </span>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Expert Picks</p>
                    <p className="text-xs text-blue-600">Stable</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performer</h3>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Award className="w-6 h-6 text-yellow-600 mr-2" />
                  <span className="text-lg font-medium text-gray-900">{analysis.performance.topPerformer}</span>
                </div>
                <span className="text-sm text-gray-600">This Month</span>
              </div>
            </div>
          </div>
        )}

        {selectedMetric === 'trends' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Home Advantage</h3>
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold text-gray-900">
                    {formatPercentage(analysis.trends.homeAdvantage)}
                  </span>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Win Rate</p>
                    <p className="text-xs text-green-600">Above average</p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Favorite Cover</h3>
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold text-gray-900">
                    {formatPercentage(analysis.trends.favoriteCover)}
                  </span>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Spread</p>
                    <p className="text-xs text-red-600">Below average</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Over/Under</h3>
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold text-gray-900">
                    {formatPercentage(analysis.trends.overUnder)}
                  </span>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Over Rate</p>
                    <p className="text-xs text-blue-600">Slightly favored</p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Spread</h3>
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold text-gray-900">
                    {analysis.trends.avgSpread}
                  </span>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Points</p>
                    <p className="text-xs text-gray-600">This season</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedMetric === 'insights' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h3>
            {analysis.insights.map((insight, index) => (
              <div key={index} className="bg-blue-50 border-l-4 border-blue-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <Activity className="w-5 h-5 text-blue-400" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-blue-700">{insight}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SportAnalysis;
