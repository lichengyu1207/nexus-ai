import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { HomeIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import { Mascot } from '@/components/mascot';

const NotFoundPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
      <motion.div 
        className="text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-center gap-6 mb-8">
          <motion.div
            animate={{ 
              y: [0, -8, 0],
              rotate: [-5, 5, -5],
            }}
            transition={{ 
              duration: 3, 
              repeat: Infinity, 
              ease: 'easeInOut' 
            }}
          >
            <Mascot emotion="confused" size="xl" animate />
          </motion.div>
          
          <div className="relative">
            <span className="text-9xl font-bold text-primary-600/20 dark:text-primary-400/20">404</span>
            <motion.div
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-gray-800 rounded-2xl px-4 py-2 shadow-lg border border-gray-200 dark:border-gray-700"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
            >
              <p className="text-sm text-gray-700 dark:text-gray-200 whitespace-nowrap">
                页面迷路了，回首页看看吧
              </p>
            </motion.div>
          </div>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          {t('errors.notFound')}
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          抱歉，您访问的页面不存在或已被移除。
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            <HomeIcon className="w-5 h-5" />
            {t('nav.home')}
          </Link>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600 transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            {t('common.back')}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default NotFoundPage;
