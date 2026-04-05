import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  MegaphoneIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';

interface Announcement {
  id: string;
  title: string;
  content: string;
  type: string;
  is_pinned: boolean;
  published_at: string;
  is_read: boolean;
}

const AnnouncementBanner: React.FC = () => {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);
  const [dismissed, setDismissed] = useState<string[]>([]);

  useEffect(() => {
    loadUnreadAnnouncements();
  }, []);

  const loadUnreadAnnouncements = async () => {
    try {
      const response = await api.get('announcements/unread');
      const unread = response.data.filter((a: Announcement) => !dismissed.includes(a.id));
      setAnnouncements(unread);
    } catch (error) {
      console.error('Failed to load announcements:', error);
    }
  };

  const handleDismiss = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const current = announcements[currentIndex];
    if (current) {
      setDismissed([...dismissed, current.id]);
      await api.post(`/api/announcements/${current.id}/read`).catch(() => {});
      
      if (currentIndex < announcements.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        setIsVisible(false);
      }
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'feature':
        return <SparklesIcon className="w-5 h-5 text-purple-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      default:
        return <InformationCircleIcon className="w-5 h-5 text-blue-500" />;
    }
  };

  const getTypeBg = (type: string) => {
    switch (type) {
      case 'feature':
        return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
      case 'success':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      default:
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
    }
  };

  if (!isVisible || announcements.length === 0) {
    return null;
  }

  const current = announcements[currentIndex];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`border-b ${getTypeBg(current.type)}`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {getTypeIcon(current.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {current.title}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 truncate hidden sm:block">
                  {current.content.substring(0, 100)}...
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2 ml-4">
              <a
                href="/announcements"
                className="flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium whitespace-nowrap"
              >
                查看详情
                <ChevronRightIcon className="w-4 h-4" />
              </a>
              
              <button
                onClick={handleDismiss}
                className="p-1 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
          </div>
          
          {announcements.length > 1 && (
            <div className="flex justify-center gap-1 pb-2">
              {announcements.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === currentIndex
                      ? 'bg-primary-500'
                      : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                />
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default AnnouncementBanner;
