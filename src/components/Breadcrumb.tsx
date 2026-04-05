import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';

interface BreadcrumbItem {
  path: string;
  label: string;
}

const routeLabels: Record<string, string> = {
  '/': '首页',
  '/dashboard': '仪表盘',
  '/tasks': '任务列表',
  '/reports': '报告列表',
  '/integral': '积分中心',
  '/settings': '设置',
  '/admin': '管理后台',
  '/admin/users': '用户管理',
  '/admin/audit': '审计日志',
  '/admin/sources': '来源统计',
  '/admin/feedback': '反馈管理',
  '/admin/settings': '系统设置',
  '/compare': '房源对比',
  '/help': '帮助中心',
  '/privacy': '隐私政策',
};

const Breadcrumb: React.FC = () => {
  const location = useLocation();
  
  const getBreadcrumbs = (): BreadcrumbItem[] => {
    const paths = location.pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];
    
    let currentPath = '';
    
    if (location.pathname !== '/') {
      breadcrumbs.push({ path: '/', label: '首页' });
    }
    
    for (const path of paths) {
      currentPath += `/${path}`;
      const label = routeLabels[currentPath] || routeLabels[`/${path}`] || path;
      breadcrumbs.push({ path: currentPath, label });
    }
    
    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-4 px-4 py-2 bg-gray-50 rounded-lg">
      <HomeIcon className="w-4 h-4" />
      {breadcrumbs.map((item, index) => (
        <React.Fragment key={item.path}>
          <ChevronRightIcon className="w-4 h-4" />
          {index === breadcrumbs.length - 1 ? (
            <span className="text-gray-900 font-medium">{item.label}</span>
          ) : (
            <Link
              to={item.path}
              className="hover:text-primary-600 transition-colors"
            >
              {item.label}
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

export default Breadcrumb;
