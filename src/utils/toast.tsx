import React from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastOptions {
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration: number;
  action?: ToastOptions['action'];
}

const toasts: Toast[] = [];
let listeners: Array<() => void> = [];

const notify = () => {
  listeners.forEach(listener => listener());
};

const subscribe = (listener: () => void) => {
  listeners.push(listener);
  return () => {
    listeners = listeners.filter(l => l !== listener);
  };
};

const getToasts = () => toasts;

const removeToast = (id: string) => {
  const index = toasts.findIndex(t => t.id === id);
  if (index > -1) {
    toasts.splice(index, 1);
    notify();
  }
};

const addToast = (type: ToastType, message: string, options: ToastOptions = {}) => {
  const id = Math.random().toString(36).substring(2, 9);
  const duration = options.duration ?? 4000;
  
  const toast: Toast = {
    id,
    type,
    message,
    duration,
    action: options.action,
  };
  
  toasts.push(toast);
  notify();
  
  if (duration > 0) {
    setTimeout(() => removeToast(id), duration);
  }
  
  return id;
};

const toast = {
  success: (message: string, options?: ToastOptions) => addToast('success', message, options),
  error: (message: string, options?: ToastOptions) => addToast('error', message, options),
  warning: (message: string, options?: ToastOptions) => addToast('warning', message, options),
  info: (message: string, options?: ToastOptions) => addToast('info', message, options),
  dismiss: removeToast,
};

const getIcon = (type: ToastType) => {
  switch (type) {
    case 'success':
      return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
    case 'error':
      return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
    case 'warning':
      return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
    case 'info':
      return <InformationCircleIcon className="w-5 h-5 text-blue-500" />;
  }
};

const getBgColor = (type: ToastType) => {
  switch (type) {
    case 'success':
      return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
    case 'error':
      return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
    case 'warning':
      return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
    case 'info':
      return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
  }
};

const ToastContainer: React.FC = () => {
  const [, forceUpdate] = React.useReducer(x => x + 1, 0);
  
  React.useEffect(() => {
    return subscribe(() => forceUpdate());
  }, []);
  
  const currentToasts = getToasts();
  
  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm">
      {currentToasts.map(toast => (
        <div
          key={toast.id}
          className={`
            flex items-start gap-3 p-4 rounded-lg border shadow-lg
            animate-slide-up
            ${getBgColor(toast.type)}
          `}
        >
          <div className="flex-shrink-0">
            {getIcon(toast.type)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-900 dark:text-gray-100">
              {toast.message}
            </p>
            {toast.action && (
              <button
                onClick={toast.action.onClick}
                className="mt-1 text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700"
              >
                {toast.action.label}
              </button>
            )}
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
};

export { toast, ToastContainer };
export default toast;
