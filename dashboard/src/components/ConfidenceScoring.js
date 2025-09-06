/**
 * Confidence Scoring Component
 * Displays confidence calibration and scoring information
 */

import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, AlertTriangle, CheckCircle, BarChart3, PieChart, Activity } from 'lucide-react';
import confidenceService from '../services/confidenceService';

const ConfidenceScoring = () => {
  const [calibration, setCalibration] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeason, setSelectedSeason] = useState(2025);
  const [viewMode, setViewMode] = useState('overview'); // 'overview', 'calibration', 'trends'

  useEffect(() => {
    loadConfidenceData();
  }, [selectedSeason]);

  const loadConfidenceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [calibrationData, trendsData] = await Promise.all([
        confidenceService.generateConfidenceReport(selectedSeason),
        confidenceService.getConfidenceTrends(selectedSeason)
      ]);
      
      setCalibration(calibrationData);
      setTrends(trendsData);
    } catch (err) {
      setError('Failed to load confidence data');
      console.error('Error loading confidence data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'excellent': return 'text-green-600 bg-green-100';
      case 'good': return 'text-blue-600 bg-blue-100';
      case 'fair': return 'text-yellow-600 bg-yellow-100';
      case 'poor': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'excellent': return '🎯';
      case 'good': return '✅';
      case 'fair': return '⚠️';
      case 'poor': return '❌';
      default: return '❓';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      {calibration && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="dashboard-card">
            <div className="flex items-center">
              <Target className="w-8 h-8 text-nfl-primary mr-3" />
              <div>
                <p className="text-sm text-gray-600">Calibration</p>
                <p className="text-2xl font-bold text-gray-900">
                  {calibration.summary.overallCalibration}%
                </p>
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(calibration.status)}`}>
                  {getStatusIcon(calibration.status)} {calibration.status}
                </div>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Reliability</p>
                <p className="text-2xl font-bold text-gray-900">
                  {calibration.summary.reliability}%
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Sharpness</p>
                <p className="text-2xl font-bold text-gray-900">
                  {calibration.summary.sharpness}%
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Total Predictions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {calibration.summary.totalPredictions}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {calibration && calibration.recommendations.length > 0 && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            Calibration Recommendations
          </h3>
          <div className="space-y-3">
            {calibration.recommendations.map((rec, index) => (
              <div key={index} className={`p-3 rounded-lg border-l-4 ${
                rec.severity === 'high' ? 'border-red-500 bg-red-50' :
                rec.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                'border-blue-500 bg-blue-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{rec.message}</h4>
                    {rec.suggestion && (
                      <p className="text-sm text-gray-600 mt-1">{rec.suggestion}</p>
                    )}
                    {rec.affectedBins && (
                      <p className="text-sm text-gray-500 mt-1">
                        Affected ranges: {rec.affectedBins.join(', ')}
                      </p>
                    )}
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    rec.severity === 'high' ? 'bg-red-100 text-red-800' :
                    rec.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {rec.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderCalibration = () => (
    <div className="space-y-6">
      {calibration && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">Confidence Bin Analysis</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Confidence Range</th>
                  <th className="text-right py-2">Predictions</th>
                  <th className="text-right py-2">Actual Accuracy</th>
                  <th className="text-right py-2">Expected Accuracy</th>
                  <th className="text-right py-2">Calibration Error</th>
                  <th className="text-right py-2">Reliability</th>
                </tr>
              </thead>
              <tbody>
                {calibration.bins.map((bin, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-2">
                      <div className="flex items-center">
                        <span className="font-medium">{bin.range}</span>
                        <span className="ml-2 text-sm text-gray-500">({bin.label})</span>
                      </div>
                    </td>
                    <td className="py-2 text-right">{bin.predictedCount}</td>
                    <td className="py-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        bin.actualAccuracy >= bin.expectedAccuracy - 5 ? 'bg-green-100 text-green-800' :
                        bin.actualAccuracy >= bin.expectedAccuracy - 10 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {bin.actualAccuracy}%
                      </span>
                    </td>
                    <td className="py-2 text-right text-gray-600">{bin.expectedAccuracy}%</td>
                    <td className="py-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        bin.calibrationError <= 5 ? 'bg-green-100 text-green-800' :
                        bin.calibrationError <= 10 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {bin.calibrationError}%
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        bin.reliability >= 80 ? 'bg-green-100 text-green-800' :
                        bin.reliability >= 60 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {bin.reliability}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confidence Distribution Chart */}
      {trends && trends.confidenceDistribution && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <PieChart className="w-5 h-5 mr-2" />
            Confidence Distribution
          </h3>
          <div className="space-y-3">
            {Object.entries(trends.confidenceDistribution).map(([range, data]) => (
              <div key={range} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-nfl-primary rounded"></div>
                  <span className="font-medium">{range}</span>
                  <span className="text-sm text-gray-500">({data.count} predictions)</span>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-nfl-primary h-2 rounded-full"
                      style={{ width: `${data.percentage}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium w-12 text-right">{data.percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderTrends = () => (
    <div className="space-y-6">
      {/* Weekly Calibration Trends */}
      {trends && trends.weeklyCalibration && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            Weekly Calibration Trends
          </h3>
          <div className="space-y-4">
            {trends.weeklyCalibration.map((week) => (
              <div key={week.week} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 bg-nfl-primary rounded-full flex items-center justify-center text-white text-sm font-bold">
                    {week.week}
                  </div>
                  <div>
                    <div className="font-medium">Week {week.week}</div>
                    <div className="text-sm text-gray-500">{week.totalPredictions} predictions</div>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-sm text-gray-500">Calibration</div>
                    <div className={`font-semibold ${
                      week.calibration >= 80 ? 'text-green-600' :
                      week.calibration >= 60 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {week.calibration}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-500">Reliability</div>
                    <div className="font-semibold">{week.reliability}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Accuracy by Confidence */}
      {trends && trends.accuracyByConfidence && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">Accuracy by Confidence Level</h3>
          <div className="space-y-3">
            {trends.accuracyByConfidence.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-nfl-primary rounded"></div>
                  <div>
                    <div className="font-medium">{item.range} ({item.label})</div>
                    <div className="text-sm text-gray-500">{item.count} predictions</div>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-sm text-gray-500">Actual</div>
                    <div className={`font-semibold ${
                      item.accuracy >= item.expectedAccuracy - 5 ? 'text-green-600' :
                      item.accuracy >= item.expectedAccuracy - 10 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {item.accuracy}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-500">Expected</div>
                    <div className="font-semibold text-gray-600">{item.expectedAccuracy}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nfl-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Loading confidence data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={loadConfidenceData}
          className="px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-primary-dark transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Confidence Scoring</h1>
          <p className="text-gray-600">Confidence calibration and reliability analysis</p>
        </div>
        
        <div className="flex items-center space-x-4 mt-4 sm:mt-0">
          {/* Season Selector */}
          <select
            value={selectedSeason}
            onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
          </select>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: Target },
            { id: 'calibration', label: 'Calibration', icon: BarChart3 },
            { id: 'trends', label: 'Trends', icon: TrendingUp }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setViewMode(id)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                viewMode === id
                  ? 'border-nfl-primary text-nfl-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {viewMode === 'overview' && renderOverview()}
      {viewMode === 'calibration' && renderCalibration()}
      {viewMode === 'trends' && renderTrends()}
    </div>
  );
};

export default ConfidenceScoring;
