import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import DashboardLayout from './components/Layout/DashboardLayout'
import VirtualOffice from './components/VirtualOffice/VirtualOffice'
import PropertyAnalysis from './pages/PropertyAnalysis'
import Report from './pages/Report'
import ReportPage from './pages/ReportPage'
import StreamingReport from './pages/StreamingReport'
import About from './pages/About'
import NotFound from './pages/NotFound'
import AdminLayout from './components/Admin/AdminLayout'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage'
import AdminIPManagement from './pages/admin/AdminIPManagement'
import AdminAuditLogs from './pages/admin/AdminAuditLogs'
import AdminIntegralPage from './pages/admin/AdminIntegralPage'
import AdminFeedbackPage from './pages/admin/AdminFeedbackPage'
import AdminSettingsPage from './pages/admin/AdminSettingsPage'
import AdminSourcePage from './pages/admin/AdminSourcePage'
import AdminKnowledgePage from './pages/admin/AdminKnowledgePage'
import AdminCompliancePage from './pages/admin/AdminCompliancePage'
import AdminReportsPage from './pages/admin/AdminReportsPage'
import AdminMapPage from './pages/admin/AdminMapPage'
import AdminMascotPage from './pages/admin/AdminMascotPage'
import DataCollectionPage from './pages/admin/DataCollectionPage'
import AdminAdminsPage from './pages/admin/AdminAdminsPage'
import AdminArticlesPage from './pages/admin/AdminArticlesPage'
import AdminLoginPage from './pages/admin/AdminLoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ReportConversionGuide from './pages/help/ReportConversionGuide'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'
import ArticleListPage from './pages/articles/ArticleListPage'
import ArticleDetailPage from './pages/articles/ArticleDetailPage'
import IPApplyPage from './pages/ip/IPApplyPage'
import IPDashboardPage from './pages/ip/IPDashboardPage'
import ReferralDetector from './components/common/ReferralDetector'
import ErrorBoundary from './components/common/ErrorBoundary'
import { UserProvider } from './context/UserContext'
import HomePage from './pages/HomePage'
import Login from './components/Auth/Login'
import DashboardPage from './pages/DashboardPage'
import SettingsPage from './pages/SettingsPage'
import MyReportsPage from './pages/MyReportsPage'
import IntegralPage from './pages/IntegralPage'
import PointsCenterPage from './pages/PointsCenterPage'
import RechargePage from './pages/RechargePage'
import HelpPage from './pages/HelpPage'
import TasksPage from './pages/TasksPage'
import TaskDetailPage from './pages/tasks/TaskDetailPage'
import UnifiedAssistant from './pages/UnifiedAssistant'
import ProfilePage from './pages/ProfilePage'
import ForbiddenPage from './pages/ForbiddenPage'
import Pricing from './components/Pricing/Pricing'
import PrivateRoute from './components/common/PrivateRoute'
import AdminRoute from './components/common/AdminRoute'
import BatchAnalysisPage from './pages/analysis/BatchAnalysisPage'
import ComparePage from './pages/analysis/ComparePage'
import NotificationPage from './pages/NotificationPage'
import PrivacyPage from './pages/legal/PrivacyPage'
import TermsPage from './pages/legal/TermsPage'
import CityPage from './pages/seo/CityPage'
import CommunityPage from './pages/seo/CommunityPage'
import KnowledgePage from './pages/seo/KnowledgePage'
import LearningMonitorPage from './pages/LearningMonitorPage'
import TrilogyShowcasePage from './pages/TrilogyShowcasePage'
import ValuationReport from './pages/ValuationReport'

function App() {
  return (
    <ErrorBoundary>
      <UserProvider>
        <Router>
          <ReferralDetector />
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<HomePage />} />
              <Route path="about" element={<About />} />
              <Route path="help" element={<HelpPage />} />
              <Route path="help/report-conversion" element={<ReportConversionGuide />} />
              <Route path="pricing" element={<Pricing />} />
              <Route path="privacy" element={<PrivacyPage />} />
              <Route path="terms" element={<TermsPage />} />
            </Route>

            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/forbidden" element={<ForbiddenPage />} />
            <Route path="/admin/login" element={<AdminLoginPage />} />

            <Route path="/dashboard" element={<PrivateRoute><DashboardLayout /></PrivateRoute>}>
              <Route index element={<DashboardPage />} />
              <Route path="property-analysis" element={<PropertyAnalysis />} />
              <Route path="tasks" element={<TasksPage />} />
              <Route path="tasks/:taskId" element={<TaskDetailPage />} />
              <Route path="my-reports" element={<MyReportsPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="integral" element={<IntegralPage />} />
              <Route path="points" element={<PointsCenterPage />} />
              <Route path="recharge" element={<RechargePage />} />
              <Route path="ip" element={<IPDashboardPage />} />
              <Route path="ip-apply" element={<IPApplyPage />} />
              <Route path="virtual-office/:taskId" element={<VirtualOffice />} />
              <Route path="report/:reportId" element={<Report />} />
              <Route path="report-page/:taskId" element={<ReportPage />} />
              <Route path="valuation-report/:reportId" element={<ValuationReport />} />
              <Route path="batch-analysis" element={<BatchAnalysisPage />} />
              <Route path="compare" element={<ComparePage />} />
              <Route path="notifications" element={<NotificationPage />} />
              <Route path="unified-assistant" element={<UnifiedAssistant />} />
              <Route path="streaming-report" element={<StreamingReport />} />
            </Route>

            <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
              <Route index element={<AdminDashboard />} />
              <Route path="login" element={<AdminLoginPage />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="admins" element={<AdminAdminsPage />} />
              <Route path="analytics" element={<AdminAnalyticsPage />} />
              <Route path="ip" element={<AdminIPManagement />} />
              <Route path="audit-logs" element={<AdminAuditLogs />} />
              <Route path="integral" element={<AdminIntegralPage />} />
              <Route path="feedback" element={<AdminFeedbackPage />} />
              <Route path="settings" element={<AdminSettingsPage />} />
              <Route path="source" element={<AdminSourcePage />} />
              <Route path="knowledge" element={<AdminKnowledgePage />} />
              <Route path="compliance" element={<AdminCompliancePage />} />
              <Route path="reports" element={<AdminReportsPage />} />
              <Route path="map" element={<AdminMapPage />} />
              <Route path="mascot" element={<AdminMascotPage />} />
              <Route path="data-collection" element={<DataCollectionPage />} />
              <Route path="articles" element={<AdminArticlesPage />} />
              <Route path="learning" element={<LearningMonitorPage />} />
            </Route>

            <Route path="/articles" element={<Layout />}>
              <Route index element={<ArticleListPage />} />
              <Route path=":slug" element={<ArticleDetailPage />} />
            </Route>

            <Route path="/property-analysis" element={<PropertyAnalysis />} />
            <Route path="/trilogy-showcase" element={<TrilogyShowcasePage />} />
            <Route path="/report/:reportId" element={<Report />} />
            <Route path="/report" element={<Report />} />
            <Route path="/report-page/:taskId" element={<ReportPage />} />
            <Route path="/virtual-office/:taskId" element={<VirtualOffice />} />
            <Route path="/ip-apply" element={<IPApplyPage />} />
            <Route path="/ip" element={<IPDashboardPage />} />

            <Route path="/city/:cityId" element={<CityPage />} />
            <Route path="/community/:cityId/:communityName" element={<CommunityPage />} />
            <Route path="/knowledge/:slug" element={<KnowledgePage />} />
            <Route path="/guide/:slug" element={<KnowledgePage />} />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
      </UserProvider>
    </ErrorBoundary>
  )
}

export default App
