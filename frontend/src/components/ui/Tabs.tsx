import React, { useState, createContext, useContext, ReactNode } from 'react';

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

const useTabsContext = () => {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tabs components must be used within a Tabs provider');
  }
  return context;
};

interface TabsProps {
  defaultTab?: string;
  value?: string;
  onChange?: (tab: string) => void;
  children: ReactNode;
  className?: string;
}

const Tabs: React.FC<TabsProps> = ({
  defaultTab,
  value,
  onChange,
  children,
  className = '',
}) => {
  const [internalTab, setInternalTab] = useState(defaultTab || '');
  
  const activeTab = value !== undefined ? value : internalTab;
  const setActiveTab = (tab: string) => {
    if (value === undefined) {
      setInternalTab(tab);
    }
    onChange?.(tab);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
};

interface TabListProps {
  children: ReactNode;
  className?: string;
}

const TabList: React.FC<TabListProps> = ({ children, className = '' }) => {
  return (
    <div
      className={`flex border-b border-gray-200 ${className}`}
      role="tablist"
    >
      {children}
    </div>
  );
};

interface TabProps {
  value: string;
  children: ReactNode;
  className?: string;
  disabled?: boolean;
}

const Tab: React.FC<TabProps> = ({
  value,
  children,
  className = '',
  disabled = false,
}) => {
  const { activeTab, setActiveTab } = useTabsContext();
  const isActive = activeTab === value;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-disabled={disabled}
      disabled={disabled}
      onClick={() => !disabled && setActiveTab(value)}
      className={`
        px-4 py-2 text-sm font-medium transition-colors relative
        ${isActive
          ? 'text-primary border-b-2 border-primary'
          : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${className}
      `}
    >
      {children}
      {isActive && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
      )}
    </button>
  );
};

interface TabPanelProps {
  value: string;
  children: ReactNode;
  className?: string;
  keepMounted?: boolean;
}

const TabPanel: React.FC<TabPanelProps> = ({
  value,
  children,
  className = '',
  keepMounted = false,
}) => {
  const { activeTab } = useTabsContext();
  const isActive = activeTab === value;

  if (!isActive && !keepMounted) {
    return null;
  }

  return (
    <div
      role="tabpanel"
      hidden={!isActive}
      className={`py-4 ${className}`}
    >
      {children}
    </div>
  );
};

interface TabPanelsProps {
  children: ReactNode;
  className?: string;
}

const TabPanels: React.FC<TabPanelsProps> = ({ children, className = '' }) => {
  return <div className={className}>{children}</div>;
};

export { Tabs, TabList, Tab, TabPanel, TabPanels };
export default Tabs;
