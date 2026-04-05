import React from 'react';

interface TabsProps {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}

const TabsContext = React.createContext<{
  value: string;
  onChange: (value: string) => void;
}>({
  value: '',
  onChange: () => {},
});

const Tabs: React.FC<TabsProps> = ({ defaultValue, value, onValueChange, children, className = '' }) => {
  const [internalValue, setInternalValue] = React.useState(defaultValue || '');
  const currentValue = value ?? internalValue;
  
  const handleChange = (newValue: string) => {
    setInternalValue(newValue);
    onValueChange?.(newValue);
  };

  return (
    <TabsContext.Provider value={{ value: currentValue, onChange: handleChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
};

const TabsList: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 ${className}`}>
    {children}
  </div>
);

const TabsTrigger: React.FC<{ value: string; children: React.ReactNode; className?: string }> = ({ value, children, className = '' }) => {
  const context = React.useContext(TabsContext);
  const isActive = context.value === value;
  
  return (
    <button
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 ${
        isActive ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
      } ${className}`}
      onClick={() => context.onChange(value)}
    >
      {children}
    </button>
  );
};

const TabsContent: React.FC<{ value: string; children: React.ReactNode; className?: string }> = ({ value, children, className = '' }) => {
  const context = React.useContext(TabsContext);
  if (context.value !== value) return null;
  return <div className={className}>{children}</div>;
};

export default Tabs;
export { Tabs, TabsList, TabsTrigger, TabsContent };
