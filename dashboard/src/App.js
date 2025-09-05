import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import TeamRankings from './components/TeamRankings';
import Predictions from './components/Predictions';
import ExpertPicks from './components/ExpertPicks';
import Performance from './components/Performance';
import CronStatus from './components/CronStatus';
import TeamComparison from './components/TeamComparison';
import ELOVisualizations from './components/ELOVisualizations';
import InjuryData from './components/InjuryData';
import SystemStatus from './components/SystemStatus';
import apiService from './services/api';
import './App.css';

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        setLoading(true);
        const status = await apiService.getSystemStatus();
        setSystemStatus(status.data);
        setError(null);
      } catch (err) {
        console.error('Failed to initialize app:', err);
        setError('Failed to connect to NFL Elo API. Please ensure the API server is running.');
      } finally {
        setLoading(false);
      }
    };

    initializeApp();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-nfl-primary mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading NFL Elo Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <h2 className="font-bold text-lg mb-2">Connection Error</h2>
            <p className="text-sm">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
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
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="min-h-screen bg-gray-100">
        <Header systemStatus={systemStatus} />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/rankings" element={<TeamRankings />} />
              <Route path="/predictions" element={<Predictions />} />
              <Route path="/expert-picks" element={<ExpertPicks />} />
              <Route path="/team-comparison" element={<TeamComparison />} />
              <Route path="/elo-visualizations" element={<ELOVisualizations />} />
              <Route path="/injury-data" element={<InjuryData />} />
              <Route path="/performance" element={<Performance />} />
              <Route path="/cron-status" element={<CronStatus />} />
              <Route path="/system" element={<SystemStatus />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
