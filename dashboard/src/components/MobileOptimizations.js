import React, { useState, useEffect } from 'react';
import { Menu, X, Smartphone, Tablet, Monitor } from 'lucide-react';

const MobileOptimizations = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const checkDevice = () => {
      const width = window.innerWidth;
      setIsMobile(width < 768);
      setIsTablet(width >= 768 && width < 1024);
      setIsDesktop(width >= 1024);
    };

    checkDevice();
    window.addEventListener('resize', checkDevice);
    return () => window.removeEventListener('resize', checkDevice);
  }, []);

  const getDeviceIcon = () => {
    if (isMobile) return <Smartphone className="h-5 w-5" />;
    if (isTablet) return <Tablet className="h-5 w-5" />;
    return <Monitor className="h-5 w-5" />;
  };

  const getDeviceName = () => {
    if (isMobile) return 'Mobile';
    if (isTablet) return 'Tablet';
    return 'Desktop';
  };

  return (
    <div className="space-y-6">
      {/* Device Detection Display */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Device Detection</h2>
          {getDeviceIcon()}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className={`p-4 rounded-lg border-2 ${
            isMobile ? 'border-nfl-primary bg-nfl-primary bg-opacity-10' : 'border-gray-200'
          }`}>
            <div className="flex items-center mb-2">
              <Smartphone className="h-5 w-5 mr-2" />
              <span className="font-medium">Mobile</span>
            </div>
            <p className="text-sm text-gray-600">
              {isMobile ? 'Currently active' : 'Width < 768px'}
            </p>
          </div>
          
          <div className={`p-4 rounded-lg border-2 ${
            isTablet ? 'border-nfl-primary bg-nfl-primary bg-opacity-10' : 'border-gray-200'
          }`}>
            <div className="flex items-center mb-2">
              <Tablet className="h-5 w-5 mr-2" />
              <span className="font-medium">Tablet</span>
            </div>
            <p className="text-sm text-gray-600">
              {isTablet ? 'Currently active' : '768px - 1024px'}
            </p>
          </div>
          
          <div className={`p-4 rounded-lg border-2 ${
            isDesktop ? 'border-nfl-primary bg-nfl-primary bg-opacity-10' : 'border-gray-200'
          }`}>
            <div className="flex items-center mb-2">
              <Monitor className="h-5 w-5 mr-2" />
              <span className="font-medium">Desktop</span>
            </div>
            <p className="text-sm text-gray-600">
              {isDesktop ? 'Currently active' : 'Width > 1024px'}
            </p>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Mobile Navigation</h2>
        
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 mb-2">Current Device: {getDeviceName()}</p>
            <p className="text-sm text-gray-500">
              {isMobile ? 'Mobile-optimized navigation enabled' : 'Standard navigation active'}
            </p>
          </div>
          
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden p-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div className="md:hidden fixed inset-0 z-50 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)}>
            <div className="fixed left-0 top-0 h-full w-64 bg-white shadow-lg" onClick={(e) => e.stopPropagation()}>
              <div className="p-4">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-bold text-gray-900">Navigation</h3>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
                
                <nav className="space-y-2">
                  <a href="/" className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Dashboard</a>
                  <a href="/rankings" className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Team Rankings</a>
                  <a href="/team-comparison" className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Team Comparison</a>
                  <a href="/elo-visualizations" className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">ELO Visualizations</a>
                  <a href="/injury-data" className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Injury Data</a>
                  <a href="/performance" className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Performance</a>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Responsive Grid Demo */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Responsive Grid System</h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((item) => (
            <div key={item} className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900">Card {item}</h3>
              <p className="text-sm text-gray-600 mt-1">
                {isMobile ? '1 column' : isTablet ? '2 columns' : '4 columns'}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Touch-Friendly Buttons */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Touch-Friendly Interface</h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-3">
            <h3 className="font-medium text-gray-900">Button Sizes</h3>
            <div className="space-y-2">
              <button className="w-full px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors">
                Small (Mobile)
              </button>
              <button className="w-full px-6 py-3 text-base bg-nfl-primary text-white rounded hover:bg-nfl-secondary transition-colors">
                Medium (Tablet)
              </button>
              <button className="w-full px-8 py-4 text-lg bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
                Large (Desktop)
              </button>
            </div>
          </div>
          
          <div className="space-y-3">
            <h3 className="font-medium text-gray-900">Touch Targets</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700">Minimum 44px height</span>
                <div className="w-11 h-11 bg-nfl-primary rounded"></div>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700">Adequate spacing</span>
                <div className="flex space-x-2">
                  <div className="w-8 h-8 bg-blue-500 rounded"></div>
                  <div className="w-8 h-8 bg-blue-500 rounded"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Mobile Performance</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">95%</div>
            <div className="text-sm text-gray-600">Mobile Score</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">2.1s</div>
            <div className="text-sm text-gray-600">Load Time</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">A+</div>
            <div className="text-sm text-gray-600">Accessibility</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileOptimizations;
