import React from 'react';
import { Link } from 'react-router-dom';

const ForbiddenPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full text-center">
        <div className="text-9xl mb-4">🚫</div>
        <h1 className="text-6xl font-bold text-gray-300 mb-4">403</h1>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">访问被拒绝</h2>
        <p className="text-gray-600 mb-8">
          抱歉，您没有权限访问此页面。如果您认为这是一个错误，请联系管理员。
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primaryDark transition-colors"
          >
            返回首页
          </Link>
          <Link
            to="/dashboard"
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            进入仪表盘
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForbiddenPage;
