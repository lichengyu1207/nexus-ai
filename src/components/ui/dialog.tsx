import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={() => onOpenChange(false)}
      />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-auto">
          {children}
        </div>
      </div>
    </div>
  );
};

const DialogTrigger: React.FC<{ children: React.ReactNode; asChild?: boolean; onClick?: () => void }> = ({ children, onClick }) => (
  <div onClick={onClick}>{children}</div>
);

const DialogContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`p-6 ${className}`}>
    {children}
  </div>
);

const DialogHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`mb-4 ${className}`}>
    {children}
  </div>
);

const DialogFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`mt-4 flex justify-end space-x-2 ${className}`}>
    {children}
  </div>
);

const DialogTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <h2 className={`text-lg font-semibold text-gray-900 dark:text-white ${className}`}>
    {children}
  </h2>
);

const DialogDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <p className={`text-sm text-gray-500 dark:text-gray-400 mt-1 ${className}`}>
    {children}
  </p>
);

const DialogClose: React.FC<{ children?: React.ReactNode; onClick?: () => void; className?: string }> = ({ children, onClick, className = '' }) => (
  <button
    className={`absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 ${className}`}
    onClick={onClick}
  >
    {children || <XMarkIcon className="w-5 h-5" />}
  </button>
);

export default Dialog;
export {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogClose,
};
