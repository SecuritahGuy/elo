import React, { useState, useEffect } from 'react';
import { Calendar, Clock, MapPin, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';

const UpcomingGames = ({ sport = 'nfl' }) => {
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUpcomingGames();
  }, []);

  const fetchUpcomingGames = async () => {
    try {
      setLoading(true);
      const response = await apiService.getNFLGames();
      const games = response.data.games || [];
      
      // Filter for upcoming games
      const now = new Date();
      const upcoming = games.filter(game => {
        const gameTime = new Date(game.game_time);
        return gameTime > now && game.status === 'scheduled';
      }).sort((a, b) => new Date(a.game_time) - new Date(b.game_time));
      
      setUpcomingGames(upcoming);
      setError(null);
    } catch (err) {
      console.error('Error fetching upcoming games:', err);
      setError('Failed to load upcoming games');
    } finally {
      setLoading(false);
    }
  };

  const formatGameTime = (gameTime) => {
    const date = new Date(gameTime);
    const now = new Date();
    const diffInHours = (date - now) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } else if (diffInHours < 48) {
      return `Tomorrow ${date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      })}`;
    } else {
      return date.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  };

  const getGameDay = (gameTime) => {
    const date = new Date(gameTime);
    const now = new Date();
    const diffInDays = Math.floor((date - now) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Tomorrow';
    if (diffInDays < 7) return date.toLocaleDateString([], { weekday: 'long' });
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const groupGamesByDay = (games) => {
    const grouped = {};
    games.forEach(game => {
      const day = getGameDay(game.game_time);
      if (!grouped[day]) {
        grouped[day] = [];
      }
      grouped[day].push(game);
    });
    return grouped;
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

  const groupedGames = groupGamesByDay(upcomingGames);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-blue-600" />
            Upcoming Games
          </h2>
          <span className="text-sm text-gray-500">
            {upcomingGames.length} game{upcomingGames.length !== 1 ? 's' : ''} scheduled
          </span>
        </div>
      </div>

      <div className="p-6">
        {upcomingGames.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">No upcoming games</p>
            <p className="text-gray-400 text-sm">Check back later for new schedules</p>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedGames).map(([day, games]) => (
              <div key={day}>
                <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                  <Clock className="w-4 h-4 mr-2 text-gray-500" />
                  {day}
                </h3>
                <div className="space-y-3">
                  {games.map((game) => (
                    <div key={game.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center text-sm text-gray-600">
                          <MapPin className="w-4 h-4 mr-1" />
                          {game.venue || 'TBD'}
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Clock className="w-4 h-4 mr-1" />
                          {formatGameTime(game.game_time)}
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
                            <div className="text-sm text-gray-500">
                              vs
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
                            <div className="text-sm text-gray-500">
                              {game.week ? `Week ${game.week}` : ''}
                            </div>
                          </div>
                        </div>
                      </div>

                      {game.odds && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Spread:</span>
                            <span className="font-medium">
                              {game.odds.spread ? `${game.odds.spread > 0 ? '+' : ''}${game.odds.spread}` : 'N/A'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UpcomingGames;
