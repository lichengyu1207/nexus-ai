import React, { useEffect, useState } from 'react';

const BackendStatusChecker: React.FC = () => {
  const [offline, setOffline] = useState(false);
  const [checking, setChecking] = useState(false);

  const checkBackend = async () => {
    setChecking(true);
    try {
      const res = await fetch('http://localhost:8000/api/health');
      if (res.ok) {
        setOffline(false);
        localStorage.setItem('backend_status', 'online');
      } else {
        throw new Error('Backend not healthy');
      }
    } catch (error) {
      setOffline(true);
      localStorage.setItem('backend_status', 'offline');
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!offline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex justify-center p-4">
      <div className="bg-red-50 border border-red-200 rounded-lg shadow-lg p-4 max-w-md flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-red-500 text-xl">⚠️</span>
          <span className="text-sm text-red-700">
            后端服务不可用，请检查后端是否启动
          </span>
        </div>
        <button
          onClick={checkBackend}
          disabled={checking}
          className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
        >
          {checking ? '检测中...' : '重试'}
        </button>
      </div>
    </div>
  );
};

export default BackendStatusChecker;
