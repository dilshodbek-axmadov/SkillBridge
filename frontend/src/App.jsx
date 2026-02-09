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

// Pages rendered without Navbar/Footer (full-screen)
const STANDALONE_ROUTES = ['/login', '/register', '/forgot-password', '/profile-setup', '/profile-manual', '/profile-cv', '/assessment', '/recommendations', '/dashboard'];

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
