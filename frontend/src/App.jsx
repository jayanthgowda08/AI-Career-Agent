import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import RecommendedJobsPage from './pages/RecommendedJobsPage';
import AgentChatPage from './pages/AgentChatPage';
import JobSearchPage from './pages/JobSearchPage';
import JobDetailsPage from './pages/JobDetailsPage';
import ResumeUploadPage from './pages/ResumeUploadPage';
import SkillGapPage from './pages/SkillGapPage';
import SavedJobsPage from './pages/SavedJobsPage';
import ProfilePage from './pages/ProfilePage';
import EvaluationDashboard from './pages/EvaluationDashboard';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />

          {/* Protected Dashboard Routes */}
          <Route path="/dashboard" element={<ProtectedRoute />}>
            <Route index element={<Navigate to="/dashboard/recommendations" replace />} />
            <Route path="recommendations" element={<RecommendedJobsPage />} />
            <Route path="chat" element={<AgentChatPage />} />
            <Route path="jobs" element={<JobSearchPage />} />
            <Route path="jobs/:jobId" element={<JobDetailsPage />} />
            <Route path="resume" element={<ResumeUploadPage />} />
            <Route path="skill-gap" element={<SkillGapPage />} />
            <Route path="saved" element={<SavedJobsPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="evaluations" element={<EvaluationDashboard />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
