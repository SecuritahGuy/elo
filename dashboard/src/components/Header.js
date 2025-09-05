import React from 'react';
import { Trophy, Activity, AlertCircle } from 'lucide-react';

const Header = ({ systemStatus }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'ready':
      case 'healthy':
        return 'text-green-600';
      case 'warning':
      case 'degraded':
        return 'text-yellow-600';
      case 'error':
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ready':
      case 'healthy':
        return <Activity className="w-4 h-4" />;
      case 'warning':
      case 'degraded':
        return <AlertCircle className="w-4 h-4" />;
      case 'error':
      case 'unhealthy':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <Trophy className="w-8 h-8 text-nfl-primary" />
              <div className="ml-3">
                <h1 className="text-xl font-bold text-gray-900">NFL Elo Dashboard</h1>
                <p className="text-sm text-gray-500">Real-time predictions & rankings</p>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {getStatusIcon(systemStatus?.status)}
              <span className={`text-sm font-medium ${getStatusColor(systemStatus?.status)}`}>
                {systemStatus?.status?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
            
            {systemStatus?.details?.num_teams && (
              <div className="text-sm text-gray-500">
                {systemStatus.details.num_teams} teams loaded
              </div>
            )}
            
            <div className="text-sm text-gray-500">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
