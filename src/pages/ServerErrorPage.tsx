import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { HomeIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const ServerErrorPage: React.FC = () => {
  const { t } = useTranslation();

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
      <div className="text-center">
        <div className="mb-8">
          <span className="text-9xl font-bold text-red-600 dark:text-red-400">500</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          {t('errors.serverError')}
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          抱歉，服务器发生错误。请稍后重试。
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
            onClick={handleRefresh}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600 transition-colors"
          >
            <ArrowPathIcon className="w-5 h-5" />
            {t('common.refresh')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServerErrorPage;
