import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { ShieldExclamationIcon } from '@heroicons/react/24/outline';

interface PrivateAdminRouteProps {
  children: React.ReactNode;
  requireSuperAdmin?: boolean;
}

const PrivateAdminRoute: React.FC<PrivateAdminRouteProps> = ({ 
  children, 
  requireSuperAdmin = false 
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">验证权限中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const isAdmin = user?.is_admin || user?.role === 'admin' || user?.role === 'super_admin';
  const isSuperAdmin = user?.role === 'super_admin';

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <ShieldExclamationIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            访问被拒绝
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            您没有管理员权限访问此页面。如需帮助，请联系系统管理员。
          </p>
          <a
            href="/dashboard"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            返回首页
          </a>
        </div>
      </div>
    );
  }

  if (requireSuperAdmin && !isSuperAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <ShieldExclamationIcon className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            权限不足
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            此操作需要超级管理员权限。当前您是普通管理员。
          </p>
          <a
            href="/admin"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            返回管理后台
          </a>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default PrivateAdminRoute;
