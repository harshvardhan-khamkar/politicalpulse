import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';

// Pages — named 1:1 with sidebar labels
import LeaderboardPage from './pages/LeaderboardPage';
import InsightsPage from './pages/InsightsPage';
import PartyInfoPage from './pages/PartyInfoPage';
import TrendingPage from './pages/TrendingPage';
import ElectionResultsPage from './pages/ElectionResultsPage';
import EBookPage from './pages/EBookPage';
import VisualizationsPage from './pages/VisualizationsPage';
import PollsPage from './pages/PollsPage';
import PollResultsPage from './pages/PollResultsPage';
import LocalNewsPage from './pages/LocalNewsPage';
import GlobalNewsPage from './pages/GlobalNewsPage';
import PartyDetailPage from './pages/PartyDetailPage';
import LeaderInfoPage from './pages/LeaderInfoPage';
import LeaderDetailPage from './pages/LeaderDetailPage';
import AuthPage from './pages/AuthPage';
import TopicAnalysisPage from './pages/TopicAnalysisPage';
import EventsTimelinePage from './pages/EventsTimelinePage';
import TopTweetsPage from './pages/TopTweetsPage';
import PublicSentimentPage from './pages/PublicSentimentPage';
import SettingsPage from './pages/SettingsPage';
import SupportPage from './pages/SupportPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminRoute from './components/AdminRoute';
import AdminLayout from './layouts/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import PollManagement from './pages/admin/PollManagement';
import PartyManagement from './pages/admin/PartyManagement';
import LeaderManagement from './pages/admin/LeaderManagement';
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
          <Route path="trending" element={<TrendingPage />} />
          <Route path="topics" element={<TopicAnalysisPage />} />
          <Route path="public-sentiment" element={<PublicSentimentPage />} />
          <Route path="events" element={<EventsTimelinePage />} />
          <Route path="top-tweets" element={<TopTweetsPage />} />
          <Route path="party-info" element={<PartyInfoPage />} />
          <Route path="party-information" element={<PartyInfoPage />} />
          <Route path="party-information/:partyId" element={<PartyDetailPage />} />
          <Route path="leader-info" element={<LeaderInfoPage />} />
          <Route path="leader-info/:leaderId" element={<LeaderDetailPage />} />

          {/* Election Data */}
          <Route path="election-results" element={<ElectionResultsPage />} />
          <Route path="ebook" element={<EBookPage />} />
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
          <Route path="leaders" element={<LeaderManagement />} />
          <Route path="system" element={<SystemControl />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
