import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfileChoicePage from './pages/ProfileChoicePage';
import AssessmentPage from './pages/AssessmentPage';
import RecommendationsPage from './pages/RecommendationsPage';
import ManualProfilePage from './pages/ManualProfilePage';
import CVUploadPage from './pages/CVUploadPage';
import DashboardPage from './pages/DashboardPage';
import MarketAnalyticsPage from './pages/MarketAnalyticsPage';
import SettingsPage from './pages/SettingsPage';
import JobsPage from './pages/JobsPage';
import SkillGapPage from './pages/SkillGapPage';
import ManageSkillsPage from './pages/ManageSkillsPage';
import LearningRoadmapPage from './pages/LearningRoadmapPage';
import CVBuilderPage from './pages/CVBuilderPage';
import ChatbotPage from './pages/ChatbotPage';

// Pages rendered without Navbar/Footer (full-screen)
const STANDALONE_ROUTES = ['/login', '/register', '/forgot-password', '/profile-setup', '/profile-manual', '/profile-cv', '/assessment', '/recommendations', '/dashboard', '/market-analytics', '/settings', '/jobs', '/skills-gap', '/manage-skills', '/roadmap', '/cv-builder', '/chat'];

function AppLayout() {
  const location = useLocation();
  const isStandalone = STANDALONE_ROUTES.includes(location.pathname);

  if (isStandalone) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/profile-setup" element={<ProfileChoicePage />} />
        <Route path="/profile-manual" element={<ManualProfilePage />} />
        <Route path="/profile-cv" element={<CVUploadPage />} />
        <Route path="/assessment" element={<AssessmentPage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/market-analytics" element={<MarketAnalyticsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/skills-gap" element={<SkillGapPage />} />
        <Route path="/manage-skills" element={<ManageSkillsPage />} />
        <Route path="/roadmap" element={<LearningRoadmapPage />} />
        <Route path="/cv-builder" element={<CVBuilderPage />} />
        <Route path="/chat" element={<ChatbotPage />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
