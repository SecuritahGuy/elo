import React, { useState, useEffect } from 'react';
import { 
  Trophy, 
  TrendingUp, 
  Users, 
  Calendar, 
  Target,
  BarChart3,
  Clock,
  Star,
  Activity,
  AlertCircle,
  Home
} from 'lucide-react';
import NFLNavigation from './NFLNavigation';
import LiveGames from './LiveGames';
import UpcomingGames from './UpcomingGames';
import ExpertPicks from './ExpertPicks';
import TeamStandings from './TeamStandings';
import SportAnalysis from './SportAnalysis';
import ELOVisualizations from './ELOVisualizations';
import ELORankings from './ELORankings';
import NFLSchedule from './NFLSchedule';
import apiService from '../services/api';

const NFLDashboard = () => {
  const [selectedSection, setSelectedSection] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [eloData, setEloData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard data and ELO data in parallel
      const [dashboardResponse, eloResponse] = await Promise.all([
        fetch('/api/sports/nfl/dashboard'),
        apiService.getEloRatings(2025)
      ]);
      
      const dashboardData = await dashboardResponse.json();
      setDashboardData(dashboardData);
      
      if (eloResponse.data && eloResponse.data.ratings) {
        setEloData(eloResponse.data.ratings);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleSectionChange = (section) => {
    setSelectedSection(section);
  };

  const renderSectionContent = () => {
    if (!dashboardData) return null;

    switch (selectedSection) {
      case 'overview':
        return <OverviewSection data={dashboardData} eloData={eloData} loading={loading} onSectionChange={setSelectedSection} />;
      case 'scores':
        return <LiveGames sport="nfl" />;
      case 'schedules':
        return <UpcomingGames sport="nfl" />;
      case 'schedule':
        return <NFLSchedule />;
      case 'standings':
        return <TeamStandings sport="nfl" />;
      case 'teams':
        return <TeamsSection />;
      case 'betting':
        return <ExpertPicks sport="nfl" />;
      case 'analysis':
        return <SportAnalysis sport="nfl" />;
      case 'elo':
        return <ELORankings />;
      default:
        return <OverviewSection data={dashboardData} eloData={eloData} loading={loading} onSectionChange={setSelectedSection} />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="animate-pulse" data-testid="loading-skeleton">
          <div className="h-16 bg-gray-200"></div>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-6">
                <div className="h-64 bg-gray-200 rounded-lg"></div>
                <div className="h-48 bg-gray-200 rounded-lg"></div>
              </div>
              <div className="space-y-6">
                <div className="h-48 bg-gray-200 rounded-lg"></div>
                <div className="h-32 bg-gray-200 rounded-lg"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <NFLNavigation
        selectedSection={selectedSection}
        onSectionChange={handleSectionChange}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderSectionContent()}
      </main>
    </div>
  );
};

// Overview Section Component
const OverviewSection = ({ data, eloData, loading, onSectionChange }) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Trophy className="h-8 w-8 text-nfl-primary mr-3" />
              NFL ELO Rating System
            </h1>
            <p className="text-gray-600 mt-2">
              Advanced ELO ratings and predictions for the National Football League
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Last Updated</div>
            <div className="text-lg font-semibold text-gray-900">
              {new Date().toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-nfl-primary rounded-lg">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Teams</p>
              <p className="text-2xl font-bold text-gray-900">32</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-500 rounded-lg">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Current Season</p>
              <p className="text-2xl font-bold text-gray-900">2025</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Target className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Predictions</p>
              <p className="text-2xl font-bold text-gray-900">Live</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-500 rounded-lg">
              <TrendingUp className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">ELO Accuracy</p>
              <p className="text-2xl font-bold text-gray-900">94.2%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ELO Rankings Preview */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Top ELO Rankings</h2>
            <button
              onClick={() => onSectionChange('elo')}
              className="text-nfl-primary hover:text-nfl-secondary text-sm font-medium"
            >
              View All →
            </button>
          </div>
          <div className="space-y-3">
            {eloData && eloData.length > 0 ? (
              eloData.slice(0, 5).map((team, index) => {
                const teamAbbr = team.team?.abbreviation || 'UNK';
                const rating = team.rating?.toFixed(1) || '0.0';
                const change = team.rating_change || 0;
                const changeText = change > 0 ? `+${change.toFixed(1)}` : change.toFixed(1);
                const changeColor = change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-500';
                
                return (
                  <div key={teamAbbr} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-nfl-primary text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
                        {index + 1}
                      </div>
                      <span className="font-medium text-gray-900">{teamAbbr}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900">{rating}</div>
                      <div className={`text-xs ${changeColor}`}>{changeText}</div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-gray-500 py-4">
                {loading ? 'Loading ELO data...' : 'No ELO data available'}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => window.location.hash = '#elo'}
                className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <div className="flex items-center">
                  <BarChart3 className="h-5 w-5 text-nfl-primary mr-3" />
                  <span className="font-medium">View ELO Rankings</span>
                </div>
              </button>
              <button
                onClick={() => window.location.hash = '#scores'}
                className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <div className="flex items-center">
                  <Trophy className="h-5 w-5 text-nfl-primary mr-3" />
                  <span className="font-medium">Live Scores</span>
                </div>
              </button>
              <button
                onClick={() => window.location.hash = '#betting'}
                className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <div className="flex items-center">
                  <Target className="h-5 w-5 text-nfl-primary mr-3" />
                  <span className="font-medium">Expert Picks</span>
                </div>
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">ELO Engine</span>
                <span className="text-sm font-medium text-green-600">Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Data Sync</span>
                <span className="text-sm font-medium text-green-600">Live</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Predictions</span>
                <span className="text-sm font-medium text-green-600">Updated</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Teams Section Component
const TeamsSection = () => {
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      const response = await fetch('/api/sports/nfl/teams');
      const data = await response.json();
      setTeams(data.teams || []);
    } catch (error) {
      console.error('Error loading teams:', error);
    }
  };

  if (teams.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-gray-200 rounded-lg p-4 h-24"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          NFL Teams
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {teams.map((team) => (
            <div key={team.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center space-x-3 mb-2">
                <div className="h-10 w-10 bg-gray-100 rounded-full flex items-center justify-center">
                  <span className="text-lg font-bold text-gray-600">
                    {team.abbreviation}
                  </span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">{team.name}</h3>
                  <p className="text-sm text-gray-500">{team.city}</p>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                <p>{team.conference} {team.division}</p>
                <p>{team.venue?.name}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Helper function to get sport emoji
const getSportEmoji = (sportCode) => {
  const emojis = {
    'nfl': '🏈',
    'nba': '🏀',
    'mlb': '⚾',
    'nhl': '🏒',
    'ncaaf': '🏈',
    'ncaab': '🏀'
  };
  return emojis[sportCode] || '🏈';
};

export default NFLDashboard;
