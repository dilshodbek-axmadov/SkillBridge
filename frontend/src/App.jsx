import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
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
import ProjectIdeasPage from './pages/ProjectIdeasPage';
import BackgroundTasksPage from './pages/BackgroundTasksPage';
import ActivityPage from './pages/ActivityPage';
import MessagesPage from './pages/MessagesPage';
import RecruiterDashboardPage from './pages/RecruiterDashboardPage';
import RecruiterCandidatesPage from './pages/RecruiterCandidatesPage';
import RecruiterCandidateDetailPage from './pages/RecruiterCandidateDetailPage';
import RecruiterSavedCandidatesPage from './pages/RecruiterSavedCandidatesPage';
import RecruiterAnalyticsPage from './pages/RecruiterAnalyticsPage';
import RecruiterJobsPage from './pages/RecruiterJobsPage';
import RecruiterJobEditorPage from './pages/RecruiterJobEditorPage';
import AdminOverviewPage from './pages/AdminOverviewPage';
import AdminUsersPage from './pages/AdminUsersPage';
import AdminSettingsPage from './pages/AdminSettingsPage';
import CVPaymentSuccessPage from './pages/CVPaymentSuccessPage';
import CVPaymentFailurePage from './pages/CVPaymentFailurePage';
import SubscriptionSuccessPage from './pages/SubscriptionSuccessPage';
import SubscriptionFailurePage from './pages/SubscriptionFailurePage';

function MarketingLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route element={<MarketingLayout />}>
        <Route path="/" element={<LandingPage />} />
      </Route>

      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/profile-setup" element={<ProfileChoicePage />} />
      <Route path="/profile-manual" element={<ManualProfilePage />} />
      <Route path="/profile-cv" element={<CVUploadPage />} />
      <Route path="/assessment" element={<AssessmentPage />} />
      <Route path="/recommendations" element={<RecommendationsPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/recruiter/candidates/:candidateId" element={<RecruiterCandidateDetailPage />} />
      <Route path="/recruiter/candidates" element={<RecruiterCandidatesPage />} />
      <Route path="/recruiter/saved-candidates" element={<RecruiterSavedCandidatesPage />} />
      <Route path="/recruiter/analytics" element={<RecruiterAnalyticsPage />} />
      <Route path="/recruiter/jobs/new" element={<RecruiterJobEditorPage />} />
      <Route path="/recruiter/jobs/:jobId/edit" element={<RecruiterJobEditorPage />} />
      <Route path="/recruiter/jobs" element={<RecruiterJobsPage />} />
      <Route path="/recruiter/dashboard" element={<RecruiterDashboardPage />} />
      <Route path="/market-analytics" element={<MarketAnalyticsPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/jobs" element={<JobsPage />} />
      <Route path="/skills-gap" element={<SkillGapPage />} />
      <Route path="/manage-skills" element={<ManageSkillsPage />} />
      <Route path="/roadmap" element={<LearningRoadmapPage />} />
      <Route path="/cv-builder" element={<CVBuilderPage />} />
      <Route path="/payment/cv/success" element={<CVPaymentSuccessPage />} />
      <Route path="/payment/cv/failure" element={<CVPaymentFailurePage />} />
      <Route path="/payment/subscription/success" element={<SubscriptionSuccessPage />} />
      <Route path="/payment/subscription/failure" element={<SubscriptionFailurePage />} />
      <Route path="/chat" element={<ChatbotPage />} />
      <Route path="/messages" element={<MessagesPage />} />
      <Route path="/project-ideas" element={<ProjectIdeasPage />} />
      <Route path="/admin-panel/users" element={<AdminUsersPage />} />
      <Route path="/admin-panel/tasks" element={<BackgroundTasksPage variant="admin" />} />
      <Route path="/admin-panel/settings" element={<AdminSettingsPage />} />
      <Route path="/admin-panel" element={<AdminOverviewPage />} />
      <Route path="/background-tasks" element={<BackgroundTasksPage />} />
      <Route path="/activity" element={<ActivityPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
