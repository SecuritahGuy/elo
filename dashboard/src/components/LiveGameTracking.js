/**
 * Live Game Tracking Component
 * Real-time tracking of NFL games with prediction monitoring
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Target, 
  TrendingUp, 
  Clock, 
  MapPin, 
  Wind,
  Thermometer,
  Zap,
  Award,
  AlertTriangle,
  CheckCircle,
  Activity,
  XCircle
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
  PieChart,
  Pie,
  Cell
} from 'recharts';
import liveGameTrackingService from '../services/liveGameTrackingService';

const LiveGameTracking = () => {
  const [games, setGames] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [pollingStatus, setPollingStatus] = useState(null);

  const loadLiveGames = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const liveGames = await liveGameTrackingService.getLiveGames();
      setGames(liveGames);
      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to load live games');
      console.error('Error loading live games:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const startTracking = useCallback(() => {
    liveGameTrackingService.startTracking();
    setIsTracking(true);
  }, []);

  const stopTracking = useCallback(() => {
    liveGameTrackingService.stopTracking();
    setIsTracking(false);
  }, []);

  const updateAnalytics = useCallback(() => {
    const liveAnalytics = liveGameTrackingService.getLiveAnalytics();
    setAnalytics(liveAnalytics);
    
    // Update polling status
    const status = liveGameTrackingService.getPollingStatus();
    setPollingStatus(status);
  }, []);

  useEffect(() => {
    loadLiveGames();
    updateAnalytics();

    // Subscribe to game updates
    const unsubscribeFunctions = [];
    
    games.forEach(game => {
      const unsubscribe = liveGameTrackingService.subscribe(game.id, (updatedGame) => {
        setGames(prevGames => 
          prevGames.map(g => g.id === game.id ? updatedGame : g)
        );
        updateAnalytics();
        setLastUpdate(new Date());
      });
      unsubscribeFunctions.push(unsubscribe);
    });

    return () => {
      unsubscribeFunctions.forEach(unsubscribe => unsubscribe());
    };
  }, [games.length, loadLiveGames, updateAnalytics]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'in_progress': return 'text-green-600 bg-green-100';
      case 'final': return 'text-gray-600 bg-gray-100';
      case 'scheduled': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'in_progress': return <Play className="w-4 h-4" />;
      case 'final': return <CheckCircle className="w-4 h-4" />;
      case 'scheduled': return <Clock className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getPredictionIcon = (predictionCorrect) => {
    if (predictionCorrect === true) return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (predictionCorrect === false) return <XCircle className="w-4 h-4 text-red-600" />;
    return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
  };

  const formatTime = (timeString) => {
    if (!timeString) return 'N/A';
    return timeString;
  };

  const getExcitementColor = (excitement) => {
    if (excitement >= 8) return 'text-red-600';
    if (excitement >= 6) return 'text-orange-600';
    if (excitement >= 4) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getExcitementLabel = (excitement) => {
    if (excitement >= 8) return 'Extreme';
    if (excitement >= 6) return 'High';
    if (excitement >= 4) return 'Medium';
    return 'Low';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-nfl-primary mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading Live Games...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <h2 className="font-bold text-lg mb-2">Error Loading Live Games</h2>
            <p className="text-sm">{error}</p>
            <button 
              onClick={loadLiveGames} 
              className="mt-4 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Live Game Tracking</h1>
              <p className="text-gray-600">
                Real-time NFL game monitoring with prediction analytics
                {lastUpdate && (
                  <span className="ml-2 text-sm">
                    Last updated: {lastUpdate.toLocaleTimeString()}
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={isTracking ? stopTracking : startTracking}
                className={`flex items-center px-4 py-2 rounded-md font-medium ${
                  isTracking
                    ? 'bg-red-500 text-white hover:bg-red-600'
                    : 'bg-green-500 text-white hover:bg-green-600'
                }`}
              >
                {isTracking ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                {isTracking ? 'Stop Tracking' : 'Start Tracking'}
              </button>
              <button
                onClick={loadLiveGames}
                className="flex items-center px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Polling Status Indicator */}
      {pollingStatus && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mx-6 mb-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-5 w-5 text-blue-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>Smart Polling Active:</strong> 
                {pollingStatus.hasLiveGames ? 
                  ` Updating every ${pollingStatus.updateFrequency / 1000}s (${pollingStatus.liveGamesCount} live games)` :
                  ' No live games detected, reduced API calls'
                }
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="p-6">
        {/* Analytics Summary */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Live Games</p>
                  <p className="text-2xl font-bold text-nfl-primary">{analytics.inProgressGames}</p>
                </div>
                <Play className="w-8 h-8 text-green-600" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Prediction Accuracy</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {analytics.predictionAccuracy ? `${(analytics.predictionAccuracy * 100).toFixed(1)}%` : 'N/A'}
                  </p>
                </div>
                <Target className="w-8 h-8 text-blue-600" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Excitement</p>
                  <p className={`text-2xl font-bold ${getExcitementColor(analytics.averageExcitement)}`}>
                    {analytics.averageExcitement.toFixed(1)}
                  </p>
                </div>
                <Zap className="w-8 h-8 text-yellow-600" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Competitiveness</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {analytics.averageCompetitiveness ? `${(analytics.averageCompetitiveness * 100).toFixed(1)}%` : 'N/A'}
                  </p>
                </div>
                <Award className="w-8 h-8 text-purple-600" />
              </div>
            </div>
          </div>
        )}

        {/* Games List */}
        <div className="space-y-6">
          {games.length === 0 ? (
            <div className="bg-white p-8 rounded-lg shadow text-center">
              <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Live Games</h3>
              <p className="text-gray-600">There are currently no live NFL games to track.</p>
            </div>
          ) : (
            games.map((game) => (
              <div key={game.id} className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-6">
                  {/* Game Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(game.status)}`}>
                        {getStatusIcon(game.status)}
                        <span className="ml-2 capitalize">{game.status.replace('_', ' ')}</span>
                      </div>
                      <div className="text-sm text-gray-600">
                        Q{game.quarter} - {formatTime(game.timeRemaining)}
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(game.gameDate).toLocaleString()}
                    </div>
                  </div>

                  {/* Score Display */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{game.awayTeam}</div>
                      <div className="text-4xl font-bold text-nfl-primary">{game.awayScore}</div>
                    </div>
                    <div className="text-center flex items-center justify-center">
                      <div className="text-gray-400">@</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{game.homeTeam}</div>
                      <div className="text-4xl font-bold text-nfl-primary">{game.homeScore}</div>
                    </div>
                  </div>

                  {/* Game Details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="flex items-center space-x-2">
                      <Target className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">Possession:</span>
                      <span className="text-sm font-medium">{game.possession}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">Down:</span>
                      <span className="text-sm font-medium">{game.down} & {game.distance}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <MapPin className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">Yard Line:</span>
                      <span className="text-sm font-medium">{game.yardLine}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Wind className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">Weather:</span>
                      <span className="text-sm font-medium">{game.weather}</span>
                    </div>
                  </div>

                  {/* Prediction Data */}
                  {game.predictionData && (
                    <div className="bg-gray-50 p-4 rounded-lg mb-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Prediction Analysis</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">Predicted Winner:</span>
                          <span className="text-sm font-medium">{game.predictionData.predictedWinner}</span>
                          {getPredictionIcon(game.predictionData.predictionCorrect)}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">Confidence:</span>
                          <span className="text-sm font-medium">
                            {game.predictionData.confidence ? `${(game.predictionData.confidence * 100).toFixed(1)}%` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">Current Winner:</span>
                          <span className="text-sm font-medium">
                            {game.predictionData.currentWinner || 'Tied'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Live Metrics */}
                  {game.liveMetrics && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-sm text-gray-600 mb-1">Excitement Level</div>
                        <div className={`text-lg font-bold ${getExcitementColor(game.liveMetrics.excitement)}`}>
                          {game.liveMetrics.excitement.toFixed(1)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {getExcitementLabel(game.liveMetrics.excitement)}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-600 mb-1">Competitiveness</div>
                        <div className="text-lg font-bold text-purple-600">
                          {(game.liveMetrics.competitiveness * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-600 mb-1">Momentum</div>
                        <div className="text-lg font-bold capitalize">
                          {game.liveMetrics.momentum.replace('_', ' ')}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveGameTracking;
