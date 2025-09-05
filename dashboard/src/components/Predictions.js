import React, { useState, useEffect } from 'react';
import { Target, RefreshCw, Calendar, TrendingUp } from 'lucide-react';
import apiService from '../services/api';

const Predictions = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [customPrediction, setCustomPrediction] = useState({
    homeTeam: '',
    awayTeam: '',
    result: null
  });

  const loadWeekPredictions = async (week) => {
    try {
      setLoading(true);
      const response = await apiService.getWeekPredictions(week);
      setPredictions(response.data.predictions);
    } catch (error) {
      console.error('Failed to load predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCustomPrediction = async () => {
    if (!customPrediction.homeTeam || !customPrediction.awayTeam) return;
    
    try {
      const response = await apiService.getGamePrediction(
        customPrediction.homeTeam,
        customPrediction.awayTeam
      );
      setCustomPrediction(prev => ({
        ...prev,
        result: response.data.prediction
      }));
    } catch (error) {
      console.error('Failed to load custom prediction:', error);
    }
  };

  useEffect(() => {
    loadWeekPredictions(selectedWeek);
  }, [selectedWeek]);

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return 'text-green-600';
    if (confidence >= 0.6) return 'text-blue-600';
    if (confidence >= 0.55) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBarColor = (confidence) => {
    if (confidence >= 0.7) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-blue-500';
    if (confidence >= 0.55) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8"></div>
        <span className="ml-2 text-gray-600">Loading predictions...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Game Predictions</h1>
          <p className="text-gray-600">NFL game predictions and win probabilities</p>
        </div>
        <button
          onClick={() => loadWeekPredictions(selectedWeek)}
          className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Week Selector */}
      <div className="dashboard-card">
        <div className="flex items-center space-x-4">
          <Calendar className="w-5 h-5 text-nfl-primary" />
          <label className="text-sm font-medium text-gray-700">Select Week:</label>
          <select
            value={selectedWeek}
            onChange={(e) => setSelectedWeek(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18].map(week => (
              <option key={week} value={week}>Week {week}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Custom Prediction Tool */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Custom Game Prediction</h2>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">Home Team</label>
            <input
              type="text"
              placeholder="e.g., KC"
              value={customPrediction.homeTeam}
              onChange={(e) => setCustomPrediction(prev => ({ ...prev, homeTeam: e.target.value.toUpperCase() }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">Away Team</label>
            <input
              type="text"
              placeholder="e.g., BUF"
              value={customPrediction.awayTeam}
              onChange={(e) => setCustomPrediction(prev => ({ ...prev, awayTeam: e.target.value.toUpperCase() }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={loadCustomPrediction}
              className="px-6 py-2 bg-nfl-secondary text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Predict
            </button>
          </div>
        </div>

        {customPrediction.result && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Prediction Result</h3>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="font-semibold">{customPrediction.homeTeam}</span>
                <span className="text-gray-400">vs</span>
                <span className="font-semibold">{customPrediction.awayTeam}</span>
              </div>
              <div className="text-right">
                <p className="font-bold text-nfl-primary">
                  {customPrediction.result.predicted_winner}
                </p>
                <p className={`text-sm ${getConfidenceColor(customPrediction.result.confidence)}`}>
                  {(customPrediction.result.confidence * 100).toFixed(1)}% confidence
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Week Predictions */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Week {selectedWeek} Predictions</h2>
          <Target className="w-5 h-5 text-nfl-secondary" />
        </div>
        <div className="space-y-4">
          {predictions.map((prediction, index) => (
            <div key={index} className="prediction-card">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="team-logo team-{prediction.home_team.toLowerCase()}">
                    {prediction.home_team}
                  </div>
                  <span className="text-gray-400">vs</span>
                  <div className="team-logo team-{prediction.away_team.toLowerCase()}">
                    {prediction.away_team}
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600">Predicted Winner</p>
                    <p className="font-bold text-nfl-primary">
                      {prediction.prediction.predicted_winner}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600">Confidence</p>
                    <p className={`font-bold ${getConfidenceColor(prediction.prediction.confidence)}`}>
                      {(prediction.prediction.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="w-24">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${getConfidenceBarColor(prediction.prediction.confidence)}`}
                        style={{ width: `${prediction.prediction.confidence * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Additional prediction details */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Home Win Prob:</span>
                    <span className="ml-2 font-semibold">
                      {(prediction.prediction.home_win_probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Expected Margin:</span>
                    <span className="ml-2 font-semibold">
                      {prediction.prediction.expected_margin.toFixed(1)} pts
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Confidence Level:</span>
                    <span className={`ml-2 font-semibold ${getConfidenceColor(prediction.prediction.confidence)}`}>
                      {prediction.prediction.confidence >= 0.7 ? 'High' : 
                       prediction.prediction.confidence >= 0.6 ? 'Medium' : 'Low'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Prediction Time:</span>
                    <span className="ml-2 font-semibold">
                      {new Date().toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Prediction Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="dashboard-card text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Predictions</h3>
          <p className="text-2xl font-bold text-nfl-primary">{predictions.length}</p>
        </div>
        <div className="dashboard-card text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">High Confidence</h3>
          <p className="text-2xl font-bold text-green-600">
            {predictions.filter(p => p.prediction.confidence >= 0.7).length}
          </p>
        </div>
        <div className="dashboard-card text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Average Confidence</h3>
          <p className="text-2xl font-bold text-nfl-secondary">
            {predictions.length > 0 ? 
              (predictions.reduce((sum, p) => sum + p.prediction.confidence, 0) / predictions.length * 100).toFixed(1) + '%' : 
              'N/A'
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default Predictions;
