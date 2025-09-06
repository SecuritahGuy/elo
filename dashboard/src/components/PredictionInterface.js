/**
 * Prediction Interface Component
 * Displays game predictions with win probabilities and confidence scores
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, Target, BarChart3, Users, TrendingUp } from 'lucide-react';
import predictionService from '../services/predictionService';

const PredictionInterface = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeason, setSelectedSeason] = useState(2025);
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [accuracy, setAccuracy] = useState(null);
  const [trends, setTrends] = useState(null);
  const [viewMode, setViewMode] = useState('predictions'); // 'predictions', 'accuracy', 'trends'

  const loadPredictions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [predictionsData, accuracyData, trendsData] = await Promise.all([
        predictionService.getGamePredictions(selectedSeason, selectedWeek),
        predictionService.getPredictionAccuracy(selectedSeason, selectedWeek),
        predictionService.getPredictionTrends(selectedSeason)
      ]);
      
      setPredictions(predictionsData);
      setAccuracy(accuracyData);
      setTrends(trendsData);
    } catch (err) {
      setError('Failed to load predictions');
      console.error('Error loading predictions:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSeason, selectedWeek]);

  useEffect(() => {
    loadPredictions();
  }, [loadPredictions]);

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600 bg-green-100';
    if (confidence >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 80) return 'High';
    if (confidence >= 60) return 'Medium';
    return 'Low';
  };

  const formatGameDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const renderPredictions = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {predictions.map((game) => (
          <div key={game.id} className="dashboard-card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">
                  {formatGameDate(game.gameDate)}
                </span>
              </div>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(game.prediction.confidence)}`}>
                {getConfidenceLabel(game.prediction.confidence)} Confidence
              </div>
            </div>

            <div className="space-y-4">
              {/* Teams */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-nfl-primary rounded-full flex items-center justify-center text-white text-sm font-bold">
                    {game.homeTeam.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold">{game.homeTeam}</div>
                    <div className="text-sm text-gray-500">Home</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-nfl-primary">
                    {game.prediction.homeWinProbability}%
                  </div>
                  <div className="text-sm text-gray-500">
                    {game.prediction.predictedScore.home} pts
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                    {game.awayTeam.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold">{game.awayTeam}</div>
                    <div className="text-sm text-gray-500">Away</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-600">
                    {game.prediction.awayWinProbability}%
                  </div>
                  <div className="text-sm text-gray-500">
                    {game.prediction.predictedScore.away} pts
                  </div>
                </div>
              </div>

              {/* Prediction Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-nfl-primary font-medium">
                    {game.prediction.predictedWinner}
                  </span>
                  <span className="text-gray-500">
                    {game.prediction.confidence}% confidence
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-nfl-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${game.prediction.homeWinProbability}%` }}
                  ></div>
                </div>
              </div>

              {/* Additional Stats */}
              <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-200">
                <div className="text-center">
                  <div className="text-xs text-gray-500">Rating Diff</div>
                  <div className="font-semibold">{game.prediction.ratingDifference}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Home Advantage</div>
                  <div className="font-semibold">+{game.prediction.homeFieldAdvantage}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderAccuracy = () => (
    <div className="space-y-6">
      {accuracy && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="dashboard-card">
            <div className="flex items-center">
              <Target className="w-8 h-8 text-nfl-primary mr-3" />
              <div>
                <p className="text-sm text-gray-600">Accuracy</p>
                <p className="text-2xl font-bold text-gray-900">{accuracy.accuracy}%</p>
              </div>
            </div>
          </div>
          <div className="dashboard-card">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Correct</p>
                <p className="text-2xl font-bold text-gray-900">{accuracy.correctPredictions}</p>
              </div>
            </div>
          </div>
          <div className="dashboard-card">
            <div className="flex items-center">
              <Users className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Total Games</p>
                <p className="text-2xl font-bold text-gray-900">{accuracy.totalGames}</p>
              </div>
            </div>
          </div>
          <div className="dashboard-card">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Avg Confidence</p>
                <p className="text-2xl font-bold text-gray-900">{accuracy.confidence}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {trends && trends.teamPerformance && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">Team Prediction Performance</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Team</th>
                  <th className="text-right py-2">Games</th>
                  <th className="text-right py-2">Correct</th>
                  <th className="text-right py-2">Accuracy</th>
                  <th className="text-right py-2">Avg Confidence</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(trends.teamPerformance).map(([team, stats]) => (
                  <tr key={team} className="border-b border-gray-100">
                    <td className="py-2 font-medium">{team}</td>
                    <td className="py-2 text-right">{stats.totalGames}</td>
                    <td className="py-2 text-right">{stats.correctPredictions}</td>
                    <td className="py-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        stats.accuracy >= 70 ? 'bg-green-100 text-green-800' :
                        stats.accuracy >= 50 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {stats.accuracy}%
                      </span>
                    </td>
                    <td className="py-2 text-right">{stats.avgConfidence}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  const renderTrends = () => (
    <div className="space-y-6">
      {trends && trends.weeklyAccuracy && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">Weekly Accuracy Trends</h3>
          <div className="space-y-4">
            {trends.weeklyAccuracy.map((week) => (
              <div key={week.week} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 bg-nfl-primary rounded-full flex items-center justify-center text-white text-sm font-bold">
                    {week.week}
                  </div>
                  <div>
                    <div className="font-medium">Week {week.week}</div>
                    <div className="text-sm text-gray-500">{week.totalGames} games</div>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-sm text-gray-500">Accuracy</div>
                    <div className={`font-semibold ${
                      week.accuracy >= 70 ? 'text-green-600' :
                      week.accuracy >= 50 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {week.accuracy}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-500">Confidence</div>
                    <div className="font-semibold">{week.confidence}%</div>
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
          <p className="text-gray-600">Loading predictions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={loadPredictions}
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
          <h1 className="text-3xl font-bold text-gray-900">Game Predictions</h1>
          <p className="text-gray-600">ELO-based predictions with confidence scoring</p>
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
          
          {/* Week Selector */}
          <select
            value={selectedWeek}
            onChange={(e) => setSelectedWeek(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
          >
            {Array.from({ length: 18 }, (_, i) => i + 1).map(week => (
              <option key={week} value={week}>Week {week}</option>
            ))}
          </select>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'predictions', label: 'Predictions', icon: Target },
            { id: 'accuracy', label: 'Accuracy', icon: BarChart3 },
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
      {viewMode === 'predictions' && renderPredictions()}
      {viewMode === 'accuracy' && renderAccuracy()}
      {viewMode === 'trends' && renderTrends()}
    </div>
  );
};

export default PredictionInterface;
