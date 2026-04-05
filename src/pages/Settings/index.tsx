import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SettingsSidebar } from './components/SettingsSidebar';
import { PersonalSettings } from './components/PersonalSettings';
import { AgentPermissions } from './components/AgentPermissions';
import { AuditLogs } from './components/AuditLogs';
import { MCPToolManagement } from './components/MCPToolManagement';
import { GlobalConfig } from './components/GlobalConfig';
import type { SettingsTab } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const isAdmin = true;

function SettingsContent() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('theme');

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
      case 'theme':
      case 'language':
      case 'notifications':
      case 'voice':
        return <PersonalSettings />;
      case 'agent-permissions':
        return <AgentPermissions />;
      case 'audit-logs':
        return <AuditLogs />;
      case 'mcp-tools':
        return <MCPToolManagement />;
      case 'global-config':
        return <GlobalConfig />;
      default:
        return <PersonalSettings />;
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <SettingsSidebar
        activeKey={activeTab}
        onSelect={setActiveTab}
        isAdmin={isAdmin}
      />

      <main className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="max-w-4xl mx-auto"
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

export default function Settings() {
  return (
    <QueryClientProvider client={queryClient}>
      <SettingsContent />
    </QueryClientProvider>
  );
}
