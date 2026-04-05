import React from 'react';

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  defaultValue?: string;
  children: React.ReactNode;
  className?: string;
}

interface SelectContextValue {
  value: string;
  onChange: (value: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

const SelectContext = React.createContext<SelectContextValue>({
  value: '',
  onChange: () => {},
  isOpen: false,
  setIsOpen: () => {},
});

const Select: React.FC<SelectProps> = ({ value, onValueChange, defaultValue, children, className = '' }) => {
  const [internalValue, setInternalValue] = React.useState(defaultValue || '');
  const [isOpen, setIsOpen] = React.useState(false);
  const currentValue = value ?? internalValue;
  
  const handleChange = (newValue: string) => {
    setInternalValue(newValue);
    onValueChange?.(newValue);
    setIsOpen(false);
  };

  return (
    <SelectContext.Provider value={{ value: currentValue, onChange: handleChange, isOpen, setIsOpen }}>
      <div className={`relative inline-block ${className}`}>
        {children}
      </div>
    </SelectContext.Provider>
  );
};

const SelectTrigger: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => {
  const context = React.useContext(SelectContext);
  
  return (
    <button
      type="button"
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 ${className}`}
      onClick={() => context.setIsOpen(!context.isOpen)}
    >
      {children}
      <svg className="h-4 w-4 opacity-50 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

const SelectValue: React.FC<{ placeholder?: string }> = ({ placeholder }) => {
  const context = React.useContext(SelectContext);
  
  return (
    <span className={context.value ? 'text-gray-900' : 'text-gray-400'}>
      {context.value || placeholder}
    </span>
  );
};

const SelectContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => {
  const context = React.useContext(SelectContext);
  
  if (!context.isOpen) return null;
  
  return (
    <>
      <div className="fixed inset-0 z-40" onClick={() => context.setIsOpen(false)} />
      <div
        className={`absolute top-full left-0 z-50 mt-1 min-w-full bg-white border border-gray-200 rounded-md shadow-lg ${className}`}
      >
        <div className="py-1 max-h-60 overflow-auto">
          {children}
        </div>
      </div>
    </>
  );
};

const SelectItem: React.FC<{ value: string; children: React.ReactNode }> = ({ value, children }) => {
  const context = React.useContext(SelectContext);
  const isSelected = context.value === value;
  
  return (
    <div
      className={`px-3 py-2 text-sm cursor-pointer hover:bg-gray-100 flex items-center justify-between ${isSelected ? 'bg-primary-50 text-primary-600' : ''}`}
      onClick={() => context.onChange(value)}
    >
      {children}
      {isSelected && (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )}
    </div>
  );
};

export default Select;
export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
