import React, { useState, useEffect } from 'react';
import { Clock, Play, Pause, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';

const LiveGames = ({ sport = 'nfl' }) => {
  const [liveGames, setLiveGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLiveGames();
    // Set up polling for live updates
    const interval = setInterval(fetchLiveGames, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchLiveGames = async () => {
    try {
      setLoading(true);
      const response = await apiService.getNFLGames();
      const games = response.data.games || [];
      
      // Filter for live games (games that are currently in progress)
      const live = games.filter(game => {
        const gameTime = new Date(game.game_time);
        const now = new Date();
        const gameEnd = new Date(gameTime.getTime() + 3 * 60 * 60 * 1000); // Assume 3 hour games
        
        return gameTime <= now && now <= gameEnd && game.status === 'live';
      });
      
      setLiveGames(live);
      setError(null);
    } catch (err) {
      console.error('Error fetching live games:', err);
      setError('Failed to load live games');
    } finally {
      setLoading(false);
    }
  };

  const formatScore = (score) => {
    return score !== null ? score : '-';
  };

  const getGameStatus = (game) => {
    if (game.status === 'live') {
      return (
        <div className="flex items-center text-red-600">
          <Play className="w-4 h-4 mr-1" />
          LIVE
        </div>
      );
    }
    return (
      <div className="flex items-center text-gray-500">
        <Pause className="w-4 h-4 mr-1" />
        {game.status}
      </div>
    );
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

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-red-600" />
            Live Games
          </h2>
          <span className="text-sm text-gray-500">
            {liveGames.length} game{liveGames.length !== 1 ? 's' : ''} live
          </span>
        </div>
      </div>

      <div className="p-6">
        {liveGames.length === 0 ? (
          <div className="text-center py-8">
            <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">No live games</p>
            <p className="text-gray-400 text-sm">Check back later for live action</p>
          </div>
        ) : (
          <div className="space-y-4">
            {liveGames.map((game) => (
              <div key={game.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-3">
                  {getGameStatus(game)}
                  <div className="text-sm text-gray-500">
                    {new Date(game.game_time).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                          <span className="text-xs font-semibold text-gray-600">
                            {game.home_team?.abbreviation || 'HOME'}
                          </span>
                        </div>
                        <span className="font-medium text-gray-900">
                          {game.home_team?.team_name || 'Home Team'}
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-gray-900">
                        {formatScore(game.home_score)}
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                          <span className="text-xs font-semibold text-gray-600">
                            {game.away_team?.abbreviation || 'AWAY'}
                          </span>
                        </div>
                        <span className="font-medium text-gray-900">
                          {game.away_team?.team_name || 'Away Team'}
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-gray-900">
                        {formatScore(game.away_score)}
                      </div>
                    </div>
                  </div>
                </div>

                {game.quarter && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Quarter {game.quarter}</span>
                      {game.time_remaining && (
                        <span>{game.time_remaining}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveGames;
