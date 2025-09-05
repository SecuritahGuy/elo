import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  Trophy,
  Target,
  BarChart3,
  Settings,
  Activity,
  Users,
  Clock,
  GitCompare,
  LineChart,
  AlertTriangle,
  Smartphone,
  Monitor
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Team Rankings', href: '/rankings', icon: Trophy },
    { name: 'Team Comparison', href: '/team-comparison', icon: GitCompare },
    { name: 'ELO Visualizations', href: '/elo-visualizations', icon: LineChart },
    { name: 'Injury Data', href: '/injury-data', icon: AlertTriangle },
    { name: 'Mobile Optimizations', href: '/mobile-optimizations', icon: Smartphone },
    { name: 'Performance Monitoring', href: '/performance-monitoring', icon: Monitor },
    { name: 'Predictions', href: '/predictions', icon: Target },
    { name: 'Expert Picks', href: '/expert-picks', icon: Users },
    { name: 'Performance', href: '/performance', icon: BarChart3 },
    { name: 'Cron Status', href: '/cron-status', icon: Clock },
    { name: 'System Status', href: '/system', icon: Activity },
  ];

  return (
    <div className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
      <nav className="mt-8 px-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${
                    isActive
                      ? 'bg-nfl-primary text-white'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-nfl-primary'
                  }`}
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 ${
                      isActive ? 'text-white' : 'text-gray-400 group-hover:text-nfl-primary'
                    }`}
                  />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* System Info */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <div className="flex items-center justify-between">
            <span>Version 1.0.0</span>
            <span className="flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
              Online
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
