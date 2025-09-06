import React, { useState } from 'react';
import { 
  ChevronDown, 
  Menu, 
  X, 
  Home, 
  Trophy, 
  TrendingUp, 
  Target,
  BarChart3,
  Users,
  Calendar,
  Star
} from 'lucide-react';

const NFLNavigation = ({ selectedSection, onSectionChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const nflSections = {
    overview: { name: 'Overview', icon: Home, path: '' },
    scores: { name: 'Live Scores', icon: Trophy, path: '/scores' },
    schedules: { name: 'Schedules', icon: Calendar, path: '/schedules' },
    schedule: { name: 'Schedule', icon: Calendar, path: '/schedule' },
    standings: { name: 'Standings', icon: BarChart3, path: '/standings' },
    teams: { name: 'Teams', icon: Users, path: '/teams' },
    betting: { name: 'Expert Picks', icon: Target, path: '/betting' },
    analysis: { name: 'Analysis', icon: TrendingUp, path: '/analysis' },
    elo: { name: 'ELO Ratings', icon: BarChart3, path: '/elo' }
  };

  const handleSectionSelect = (section) => {
    onSectionChange(section);
    setIsOpen(false);
  };

  return (
    <nav className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-2xl mr-2">🏈</span>
              <div>
                <h1 className="text-xl font-bold text-gray-900">NFL ELO System</h1>
                <p className="text-xs text-gray-500">Advanced Rating System</p>
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {Object.entries(nflSections).map(([key, section]) => {
                const Icon = section.icon;
                const isActive = selectedSection === key;
                return (
                  <button
                    key={key}
                    onClick={() => handleSectionSelect(key)}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-nfl-primary text-white'
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center">
                      <Icon className="h-4 w-4 mr-2" />
                      {section.name}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-nfl-primary"
            >
              <span className="sr-only">Open main menu</span>
              {isOpen ? (
                <X className="block h-6 w-6" />
              ) : (
                <Menu className="block h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-50">
            {Object.entries(nflSections).map(([key, section]) => {
              const Icon = section.icon;
              const isActive = selectedSection === key;
              return (
                <button
                  key={key}
                  onClick={() => handleSectionSelect(key)}
                  className={`w-full text-left px-3 py-2 rounded-md text-base font-medium transition-colors ${
                    isActive
                      ? 'bg-nfl-primary text-white'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center">
                    <Icon className="h-5 w-5 mr-3" />
                    {section.name}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
};

export default NFLNavigation;
