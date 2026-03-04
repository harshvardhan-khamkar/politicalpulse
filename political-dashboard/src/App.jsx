import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';

// Pages — named 1:1 with sidebar labels
import LeaderboardPage from './pages/LeaderboardPage';
import InsightsPage from './pages/InsightsPage';
import PartyInfoPage from './pages/PartyInfoPage';
import ElectionResultsPage from './pages/ElectionResultsPage';
import VisualizationsPage from './pages/VisualizationsPage';
import PollsPage from './pages/PollsPage';
import PollResultsPage from './pages/PollResultsPage';
import LocalNewsPage from './pages/LocalNewsPage';
import GlobalNewsPage from './pages/GlobalNewsPage';
import PartyDetailPage from './pages/PartyDetailPage';
import AuthPage from './pages/AuthPage';
import SettingsPage from './pages/SettingsPage';
import SupportPage from './pages/SupportPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminRoute from './components/AdminRoute';
import AdminLayout from './layouts/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import PollManagement from './pages/admin/PollManagement';
import PartyManagement from './pages/admin/PartyManagement';
import SystemControl from './pages/admin/SystemControl';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>

          {/* Account */}
          <Route path="login" element={<AuthPage />} />

          {/* Analytics */}
          <Route index element={<LeaderboardPage />} />
          <Route path="analytics" element={<InsightsPage />} />
          <Route path="party-info" element={<PartyInfoPage />} />
          <Route path="party-information" element={<PartyInfoPage />} />
          <Route path="party-information/:partyId" element={<PartyDetailPage />} />

          {/* Election Data */}
          <Route path="election-results" element={<ElectionResultsPage />} />
          <Route path="election-charts" element={<VisualizationsPage />} />

          {/* Polls */}
          <Route path="polls" element={<PollsPage />} />
          <Route path="poll-results" element={<PollResultsPage />} />

          {/* News */}
          <Route path="news/global" element={<GlobalNewsPage />} />
          <Route path="news/local" element={<LocalNewsPage />} />

          {/* Others */}
          <Route path="settings" element={<SettingsPage />} />
          <Route path="support" element={<SupportPage />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>

        {/* Admin — own layout + sidebar, protected by AdminRoute inside AdminLayout */}
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="polls" element={<PollManagement />} />
          <Route path="parties" element={<PartyManagement />} />
          <Route path="system" element={<SystemControl />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
