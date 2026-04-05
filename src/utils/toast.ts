import React from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastOptions {
  duration?: number;
}

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration: number;
}

const toasts: Toast[] = [];

const addToast = (toast: Omit<Toast, 'id'>) => {
  const id = Math.random().toString(36).substr(2, 9);
  toasts.push({ ...toast, id });
};

const dismissToast = (id: string) => {
  const index = toasts.findIndex((t) => t.id === id);
  if (index > -1) {
    toasts.splice(index, 1);
  }
};

const toast = {
  success: (message: string, options?: ToastOptions) => {
    console.log(`[Success] ${message}`);
    return message;
  },
  error: (message: string, options?: ToastOptions) => {
    console.error(`[Error] ${message}`);
    return message;
  },
  warning: (message: string, options?: ToastOptions) => {
    console.warn(`[Warning] ${message}`);
    return message;
  },
  info: (message: string, options?: ToastOptions) => {
    console.info(`[Info] ${message}`);
    return message;
  },
};

export const ToastContainer = () => {
  return null;
};

export default toast;
