import React, { Suspense, lazy, useEffect, useState } from 'react';
import { HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { MascotProvider } from '@/contexts/MascotContext';
import PrivateRoute from '@/components/PrivateRoute';
import PrivateAdminRoute from '@/components/PrivateAdminRoute';
import PublicRoute from '@/components/PublicRoute';
import Layout from '@/components/Layout';
import ProgressBar from '@/components/ProgressBar';
import PageLoader from '@/components/PageLoader';
import ErrorBoundary from '@/components/ErrorBoundary';
import { ToastContainer } from '@/utils/toast';
import { QueryProvider } from '@/lib/queryClient';
import { initGA, pageview } from '@/analytics';
import { MascotToastProvider, OnboardingManager, ActiveReminderManager, InteractiveMascot } from '@/components/mascot';
import DebugPanel from '@/components/DebugPanel';
import { initSourceTracking } from '@/utils/sourceTracker';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2, ease: 'easeIn' } },
};

const AnimatedPage: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <motion.div
    variants={pageVariants}
    initial="initial"
    animate="animate"
    exit="exit"
    className="w-full h-full"
  >
    {children}
  </motion.div>
);

initSourceTracking();

const RouteTracker: React.FC = () => {
  const location = useLocation();

  useEffect(() => {
    pageview(location.pathname + location.search);
  }, [location]);

  return null;
};

const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const LandingPage = lazy(() => import('@/pages/LandingPage'));
const SEOLandingPage = lazy(() => import('@/pages/SEOLandingPage'));
const ComparePage = lazy(() => import('@/pages/ComparePage'));
const HelpPage = lazy(() => import('@/pages/HelpPage'));
const ContactPage = lazy(() => import('@/pages/ContactPage'));
const TutorialDetailPage = lazy(() => import('@/pages/TutorialDetailPage'));
const AboutPage = lazy(() => import('@/pages/AboutPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));
const AnnouncementsPage = lazy(() => import('@/pages/AnnouncementsPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const TasksPage = lazy(() => import('@/pages/TasksPage'));
const TaskDetailPage = lazy(() => import('@/pages/TaskDetailPageNew'));
const ProfilePage = lazy(() => import('@/pages/ProfilePage'));
const TeamsPage = lazy(() => import('@/pages/TeamsPage'));
const TeamDetailPage = lazy(() => import('@/pages/TeamDetailPage'));
const ReportPage = lazy(() => import('@/pages/ReportPage'));
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage'));
const ReportsPage = lazy(() => import('@/pages/ReportsPage'));
const PublicReportPage = lazy(() => import('@/pages/PublicReportPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const SearchResultsPage = lazy(() => import('@/pages/SearchResultsPage'));
const AuditLogsPage = lazy(() => import('@/pages/AuditLogsPage'));
const IntegralPage = lazy(() => import('@/pages/IntegralPage'));
const RechargePage = lazy(() => import('@/pages/RechargePage'));
const ConsultPage = lazy(() => import('@/pages/ConsultPageNew'));
const ConsumptionPage = lazy(() => import('@/pages/ConsumptionPage'));
const ComplaintsPage = lazy(() => import('@/pages/ComplaintsPage'));
const UploadPage = lazy(() => import('@/pages/UploadPage'));
const AdminUploadsPage = lazy(() => import('@/pages/AdminUploadsPage'));
const TaskCenterPage = lazy(() => import('@/pages/TaskCenterPage'));
const HabitsPage = lazy(() => import('@/pages/HabitsPage'));
const MemoryPage = lazy(() => import('@/pages/MemoryPage'));
const TalentMarketPage = lazy(() => import('@/pages/TalentMarketPage'));
const AgentDashboardPage = lazy(() => import('@/pages/AgentDashboardPage'));
const OpsDashboardPage = lazy(() => import('@/pages/admin/OpsDashboardPage'));
const CounterStrikePage = lazy(() => import('@/pages/CounterstrikePage'));
const EvolutionPage = lazy(() => import('@/pages/EvolutionPage'));
const SelfPlayPage = lazy(() => import('@/pages/SelfPlayPage'));
const DataEngineeringPage = lazy(() => import('@/pages/DataEngineeringPage'));
const AISafetyPage = lazy(() => import('@/pages/AISafetyPage'));
const FullChainPage = lazy(() => import('@/pages/FullChainPage'));
const AgentCognitionPanel = lazy(() => import('@/pages/AgentCognitionPanel'));
const RecruitPage = lazy(() => import('@/pages/RecruitPage'));
const AutoWorkPage = lazy(() => import('@/pages/AutoWorkPage'));
const EcosystemPage = lazy(() => import('@/pages/EcosystemPage'));
const FiveEndPage = lazy(() => import('@/pages/FiveEndPage'));
const GovernancePage = lazy(() => import('@/pages/GovernancePage'));
const LearningPage = lazy(() => import('@/pages/LearningPage'));

const AdminLayout = lazy(() => import('@/pages/admin/AdminLayout'));
const AdminOverview = lazy(() => import('@/pages/admin/AdminOverview'));
const AdminUsers = lazy(() => import('@/pages/admin/AdminUsers'));
const AdminSettings = lazy(() => import('@/pages/admin/AdminSettings'));
const AuditPage = lazy(() => import('@/pages/admin/AuditPage'));
const StatsPage = lazy(() => import('@/pages/admin/StatsPage'));
const MapPage = lazy(() => import('@/pages/admin/MapPage'));
const LocationsPage = lazy(() => import('@/pages/admin/LocationsPage'));
const AdminFeedbackPage = lazy(() => import('@/pages/admin/FeedbackPage'));
const ABTestPage = lazy(() => import('@/pages/admin/ABTestPage'));
const PrivacyPolicyPage = lazy(() => import('@/pages/PrivacyPolicyPage'));
const FeedbackPage = lazy(() => import('@/pages/FeedbackPage'));
const FeedbackDetailPage = lazy(() => import('@/pages/FeedbackDetailPage'));
const KnowledgeBasePage = lazy(() => import('@/pages/admin/KnowledgeBasePage'));
const UserCommunicationPage = lazy(() => import('@/pages/admin/UserCommunicationPage'));
const AdminReportsPage = lazy(() => import('@/pages/admin/ReportsPage'));
const AdminRechargeOrdersPage = lazy(() => import('@/pages/admin/AdminRechargeOrdersPage'));
const CompliancePage = lazy(() => import('@/pages/admin/CompliancePage'));
const MascotPage = lazy(() => import('@/pages/admin/MascotPage'));
const SourceStatsPage = lazy(() => import('@/pages/admin/SourceStatsPage'));
const PerformancePage = lazy(() => import('@/pages/admin/PerformancePage'));
const LogsPage = lazy(() => import('@/pages/admin/LogsPage'));
const MonitorPage = lazy(() => import('@/pages/admin/MonitorPage'));
const AdminIntegralPage = lazy(() => import('@/pages/admin/AdminIntegralPage'));
const AdminPlansPage = lazy(() => import('@/pages/admin/AdminPlansPage'));
const AdminRechargePage = lazy(() => import('@/pages/admin/AdminRechargePage'));
const DataCollectionPage = lazy(() => import('@/pages/admin/DataCollectionPage'));
const AdminGeoPage = lazy(() => import('@/pages/admin/AdminGeoPage'));
const TrainingPage = lazy(() => import('@/pages/admin/TrainingPage'));
const ClusterMonitorPage = lazy(() => import('@/pages/admin/ClusterMonitorPage'));
const MarketPage = lazy(() => import('@/pages/MarketPage'));
const SkillPage = lazy(() => import('@/pages/SkillPage'));
const IconShowcasePage = lazy(() => import('@/pages/IconShowcasePage'));

const IPApplyPage = lazy(() => import('@/pages/IPApplyPage'));
const IPDashboardPage = lazy(() => import('@/pages/IPDashboardPage'));
const IPLinksPage = lazy(() => import('@/pages/IPLinksPage'));
const AtmosphereValuationPage = lazy(() => import('@/pages/AtmosphereValuationPage'));
const IPCommissionsPage = lazy(() => import('@/pages/IPCommissionsPage'));
const IPWithdrawPage = lazy(() => import('@/pages/IPWithdrawPage'));
const AdminIPManagementPage = lazy(() => import('@/pages/admin/AdminIPManagementPage'));

const AuthenticatedReminders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  return (
    <ActiveReminderManager
      enableIdleReminder={isAuthenticated}
      enableDailyGreeting={isAuthenticated}
      idleTimeout={60000}
    >
      {children}
    </ActiveReminderManager>
  );
};

const InteractiveMascotWrapper: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [showMascot, setShowMascot] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      const timer = setTimeout(() => setShowMascot(true), 2000);
      return () => clearTimeout(timer);
    } else {
      setShowMascot(false);
    }
  }, [isAuthenticated]);

  if (!showMascot) return null;

  return (
    <InteractiveMascot
      size="lg"
      draggable
      showQuoteBubble
      initialPosition={{ x: window.innerWidth - 120, y: window.innerHeight - 150 }}
    />
  );
};

const AppRoutes: React.FC = () => {
  const location = useLocation();

  return (
    <>
      <ProgressBar />
      <AnimatePresence mode="wait">
        <Suspense fallback={<PageLoader />}>
          <Routes location={location} key={location.pathname}>
            {/* Public Routes */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <AnimatedPage>
                    <LoginPage />
                  </AnimatedPage>
                </PublicRoute>
              }
            />
            <Route
              path="/register"
              element={
                <PublicRoute>
                  <AnimatedPage>
                    <RegisterPage />
                  </AnimatedPage>
                </PublicRoute>
              }
            />
            <Route path="/public/:token" element={<AnimatedPage><PublicReportPage /></AnimatedPage>} />

          {/* Public IP Routes */}
          <Route path="/ip-apply" element={<AnimatedPage><IPApplyPage /></AnimatedPage>} />
          <Route path="/ip" element={<AnimatedPage><IPDashboardPage /></AnimatedPage>} />

          {/* Protected Routes */}
          <Route
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route path="/dashboard" element={<AnimatedPage><DashboardPage /></AnimatedPage>} />
            <Route path="/help" element={<AnimatedPage><HelpPage /></AnimatedPage>} />
            <Route path="/help/tutorials/:id" element={<AnimatedPage><TutorialDetailPage /></AnimatedPage>} />
            <Route path="/contact" element={<AnimatedPage><ContactPage /></AnimatedPage>} />
            <Route path="/about" element={<AnimatedPage><AboutPage /></AnimatedPage>} />
            <Route path="/announcements" element={<AnimatedPage><AnnouncementsPage /></AnimatedPage>} />
            <Route path="/tasks" element={<AnimatedPage><TasksPage /></AnimatedPage>} />
            <Route path="/tasks/:taskId" element={<AnimatedPage><TaskDetailPage /></AnimatedPage>} />
            <Route path="/tasks/:taskId/report" element={<AnimatedPage><ReportPage /></AnimatedPage>} />
            <Route path="/reports" element={<AnimatedPage><ReportsPage /></AnimatedPage>} />
            <Route path="/teams" element={<AnimatedPage><TeamsPage /></AnimatedPage>} />
            <Route path="/teams/:teamId" element={<AnimatedPage><TeamDetailPage /></AnimatedPage>} />
            <Route path="/notifications" element={<AnimatedPage><NotificationsPage /></AnimatedPage>} />
            <Route path="/search" element={<AnimatedPage><SearchResultsPage /></AnimatedPage>} />
            <Route path="/settings" element={<AnimatedPage><SettingsPage /></AnimatedPage>} />
            <Route path="/privacy" element={<AnimatedPage><PrivacyPolicyPage /></AnimatedPage>} />
            <Route path="/feedback" element={<AnimatedPage><FeedbackPage /></AnimatedPage>} />
            <Route path="/feedback/:id" element={<AnimatedPage><FeedbackDetailPage /></AnimatedPage>} />
            <Route path="/settings/audit-logs" element={<AnimatedPage><AuditLogsPage /></AnimatedPage>} />
            <Route path="/integral" element={<AnimatedPage><IntegralPage /></AnimatedPage>} />
            <Route path="/recharge" element={<AnimatedPage><RechargePage /></AnimatedPage>} />
            <Route path="/consumption" element={<AnimatedPage><ConsumptionPage /></AnimatedPage>} />
            <Route path="/complaints" element={<AnimatedPage><ComplaintsPage /></AnimatedPage>} />
            <Route path="/upload" element={<AnimatedPage><UploadPage /></AnimatedPage>} />
            <Route path="/consult" element={<AnimatedPage><ConsultPage /></AnimatedPage>} />
            <Route path="/compare" element={<AnimatedPage><ComparePage /></AnimatedPage>} />
            <Route path="/landing" element={<AnimatedPage><LandingPage /></AnimatedPage>} />
            <Route path="/icon-showcase" element={<AnimatedPage><IconShowcasePage /></AnimatedPage>} />
            <Route path="/profile" element={<AnimatedPage><ProfilePage /></AnimatedPage>} />
            <Route path="/ip" element={<AnimatedPage><IPDashboardPage /></AnimatedPage>} />
            <Route path="/ip/links" element={<AnimatedPage><IPLinksPage /></AnimatedPage>} />
            <Route path="/ip/commissions" element={<AnimatedPage><IPCommissionsPage /></AnimatedPage>} />
            <Route path="/ip/withdraw" element={<AnimatedPage><IPWithdrawPage /></AnimatedPage>} />
            <Route path="/ip-apply" element={<AnimatedPage><IPApplyPage /></AnimatedPage>} />
            <Route path="/task-center" element={<AnimatedPage><TaskCenterPage /></AnimatedPage>} />
            <Route path="/habits" element={<AnimatedPage><HabitsPage /></AnimatedPage>} />
            <Route path="/memory" element={<AnimatedPage><MemoryPage /></AnimatedPage>} />
            <Route path="/talent-market" element={<AnimatedPage><TalentMarketPage /></AnimatedPage>} />
            <Route path="/market" element={<AnimatedPage><MarketPage /></AnimatedPage>} />
            <Route path="/skills" element={<AnimatedPage><SkillPage /></AnimatedPage>} />
            <Route path="/agents" element={<AnimatedPage><AgentDashboardPage /></AnimatedPage>} />
            <Route path="/counterstrike" element={<AnimatedPage><CounterStrikePage /></AnimatedPage>} />
            <Route path="/evolution" element={<AnimatedPage><EvolutionPage /></AnimatedPage>} />
            <Route path="/selfplay" element={<AnimatedPage><SelfPlayPage /></AnimatedPage>} />
            <Route path="/data-engineering" element={<AnimatedPage><DataEngineeringPage /></AnimatedPage>} />
            <Route path="/ai-safety" element={<AnimatedPage><AISafetyPage /></AnimatedPage>} />
            <Route path="/fullchain" element={<AnimatedPage><FullChainPage /></AnimatedPage>} />
            <Route path="/cognition" element={<AnimatedPage><AgentCognitionPanel /></AnimatedPage>} />
            <Route path="/recruit" element={<AnimatedPage><RecruitPage /></AnimatedPage>} />
            <Route path="/auto-work" element={<AnimatedPage><AutoWorkPage /></AnimatedPage>} />
            <Route path="/ecosystem" element={<AnimatedPage><EcosystemPage /></AnimatedPage>} />
            <Route path="/five-end" element={<AnimatedPage><FiveEndPage /></AnimatedPage>} />
            <Route path="/governance" element={<AnimatedPage><GovernancePage /></AnimatedPage>} />
            <Route path="/learning" element={<AnimatedPage><LearningPage /></AnimatedPage>} />
            <Route path="/atmosphere" element={<AnimatedPage><AtmosphereValuationPage /></AnimatedPage>} />
          </Route>

          {/* Admin Routes */}
          <Route 
            path="/admin" 
            element={
              <PrivateAdminRoute>
                <AdminLayout />
              </PrivateAdminRoute>
            }
          >
            <Route index element={<AnimatedPage><AdminOverview /></AnimatedPage>} />
            <Route path="users" element={<AnimatedPage><AdminUsers /></AnimatedPage>} />
            <Route path="map" element={<AnimatedPage><MapPage /></AnimatedPage>} />
            <Route path="locations" element={<AnimatedPage><LocationsPage /></AnimatedPage>} />
            <Route path="feedback" element={<AnimatedPage><AdminFeedbackPage /></AnimatedPage>} />
            <Route path="uploads" element={<AnimatedPage><AdminUploadsPage /></AnimatedPage>} />
            <Route path="ab-tests" element={<AnimatedPage><ABTestPage /></AnimatedPage>} />
            <Route path="knowledge-base" element={<AnimatedPage><KnowledgeBasePage /></AnimatedPage>} />
            <Route path="user-communication" element={<AnimatedPage><UserCommunicationPage /></AnimatedPage>} />
            <Route path="reports" element={<AnimatedPage><AdminReportsPage /></AnimatedPage>} />
            <Route path="recharge-orders" element={<AnimatedPage><AdminRechargeOrdersPage /></AnimatedPage>} />
            <Route path="compliance" element={<AnimatedPage><CompliancePage /></AnimatedPage>} />
            <Route path="mascot" element={<AnimatedPage><MascotPage /></AnimatedPage>} />
            <Route path="performance" element={<AnimatedPage><PerformancePage /></AnimatedPage>} />
            <Route path="logs" element={<AnimatedPage><LogsPage /></AnimatedPage>} />
            <Route path="monitor" element={<AnimatedPage><MonitorPage /></AnimatedPage>} />
            <Route path="integral" element={<AnimatedPage><AdminIntegralPage /></AnimatedPage>} />
            <Route path="plans" element={<AnimatedPage><AdminPlansPage /></AnimatedPage>} />
            <Route path="recharge" element={<AnimatedPage><AdminRechargePage /></AnimatedPage>} />
            <Route path="source-stats" element={<AnimatedPage><SourceStatsPage /></AnimatedPage>} />
            <Route path="data-collection" element={<AnimatedPage><DataCollectionPage /></AnimatedPage>} />
            <Route path="geo" element={<AnimatedPage><AdminGeoPage /></AnimatedPage>} />
            <Route path="ip-management" element={<AnimatedPage><AdminIPManagementPage /></AnimatedPage>} />
            <Route path="settings" element={<AnimatedPage><AdminSettings /></AnimatedPage>} />
            <Route path="audit" element={<AnimatedPage><AuditPage /></AnimatedPage>} />
            <Route path="stats" element={<AnimatedPage><StatsPage /></AnimatedPage>} />
            <Route path="ops" element={<AnimatedPage><OpsDashboardPage /></AnimatedPage>} />
            <Route path="training" element={<AnimatedPage><TrainingPage /></AnimatedPage>} />
            <Route path="cluster" element={<AnimatedPage><ClusterMonitorPage /></AnimatedPage>} />
          </Route>

          {/* Default Route */}
          <Route path="/" element={<AnimatedPage><LandingPage /></AnimatedPage>} />
          <Route path="/search" element={<AnimatedPage><SEOLandingPage /></AnimatedPage>} />
          <Route path="*" element={<AnimatedPage><NotFoundPage /></AnimatedPage>} />
        </Routes>
      </Suspense>
    </AnimatePresence>
    </>
  );
};

const App: React.FC = () => {
  useEffect(() => {
    initGA();
  }, []);

  return (
    <ErrorBoundary>
      <HelmetProvider>
        <BrowserRouter>
          <RouteTracker />
          <ThemeProvider>
            <QueryProvider>
              <AuthProvider>
                <MascotProvider>
                  <MascotToastProvider position="top-center">
                    <AuthenticatedReminders>
                      <OnboardingManager>
                        <AppRoutes />
                      </OnboardingManager>
                    </AuthenticatedReminders>
                    <InteractiveMascotWrapper />
                    <DebugPanel />
                    <ToastContainer />
                  </MascotToastProvider>
                </MascotProvider>
              </AuthProvider>
            </QueryProvider>
          </ThemeProvider>
        </BrowserRouter>
      </HelmetProvider>
    </ErrorBoundary>
  );
};

export default App;
