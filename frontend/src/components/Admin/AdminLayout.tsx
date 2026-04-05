import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';

interface AdminInfo {
  id: string;
  email: string;
  username: string;
  role: string;
}

const menuItems = [
  { text: '仪表盘', icon: '📊', path: '/admin' },
  { text: '用户管理', icon: '👥', path: '/admin/users' },
  { text: '管理员管理', icon: '🔐', path: '/admin/admins' },
  { text: '文章管理', icon: '📝', path: '/admin/articles' },
  { text: '数据分析', icon: '📈', path: '/admin/analytics' },
  { text: 'IP管理', icon: '🎫', path: '/admin/ip' },
  { text: '积分管理', icon: '💰', path: '/admin/integral' },
  { text: '反馈管理', icon: '💬', path: '/admin/feedback' },
  { text: '举报管理', icon: '🚨', path: '/admin/reports' },
  { text: '来源统计', icon: '📍', path: '/admin/source' },
  { text: '知识库管理', icon: '📚', path: '/admin/knowledge' },
  { text: '用户地图', icon: '🗺️', path: '/admin/map' },
  { text: '数据采集', icon: '🔄', path: '/admin/data-collection' },
  { text: '学习监控', icon: '🧠', path: '/admin/learning' },
  { text: '吉祥物管理', icon: '🐕', path: '/admin/mascot' },
  { text: '合规管理', icon: '📋', path: '/admin/compliance' },
  { text: '审计日志', icon: '📜', path: '/admin/audit-logs' },
  { text: '系统设置', icon: '⚙️', path: '/admin/settings' },
];

const AdminLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [admin, setAdmin] = useState<AdminInfo | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const fetchAdmin = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const userData = await response.json();
          if (userData.role !== 'admin' && userData.role !== 'super_admin') {
            navigate('/dashboard');
            return;
          }
          setAdmin(userData);
        } else {
          localStorage.removeItem('token');
          navigate('/login');
        }
      } catch (error) {
        console.error('Failed to fetch admin:', error);
      }
    };

    fetchAdmin();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (!admin) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Desktop Sidebar */}
      <aside 
        className={`hidden md:flex flex-col fixed left-0 top-0 h-full bg-slate-800 z-40 transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-700">
          {sidebarOpen && (
            <Link to="/" className="text-lg font-bold text-white">
              房都督AI
            </Link>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded hover:bg-slate-700 text-slate-400"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>
        
        <div className="px-4 py-2">
          <span className="text-xs text-slate-500 uppercase tracking-wider">
            {sidebarOpen ? '管理后台' : 'Admin'}
          </span>
        </div>

        <nav className="flex-1 py-2 overflow-y-auto">
          {menuItems.map((item) => (
            <Link
              key={item.text}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
              title={!sidebarOpen ? item.text : undefined}
            >
              <span className="text-lg">{item.icon}</span>
              {sidebarOpen && <span>{item.text}</span>}
            </Link>
          ))}
        </nav>

        <div className="border-t border-slate-700 p-4">
          {sidebarOpen ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-medium">
                  {admin.username && admin.username.charAt(0).toUpperCase() || 'A'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{admin.username}</p>
                  <p className="text-xs text-slate-400 truncate">{admin.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Link
                  to="/dashboard"
                  className="flex-1 text-center text-sm bg-slate-700 text-slate-300 py-2 rounded hover:bg-slate-600"
                >
                  返回前台
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-2 rounded bg-red-600/20 text-red-400 hover:bg-red-600/30"
                  title="退出登录"
                >
                  🚪
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-medium">
                {admin.username?.charAt(0).toUpperCase() || 'A'}
              </div>
              <Link
                to="/dashboard"
                className="p-2 rounded hover:bg-slate-700 text-slate-400"
                title="返回前台"
              >
                🏠
              </Link>
              <button
                onClick={handleLogout}
                className="p-2 rounded hover:bg-red-600/30 text-red-400"
                title="退出登录"
              >
                🚪
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-slate-800 z-30 flex items-center justify-between px-4">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded hover:bg-slate-700 text-slate-400"
        >
          ☰
        </button>
        <span className="text-lg font-bold text-white">管理后台</span>
        <div className="w-10" />
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside 
        className={`md:hidden fixed left-0 top-0 h-full bg-slate-800 z-50 w-64 transform transition-transform duration-300 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-16 flex items-center px-4 border-b border-slate-700">
          <span className="text-lg font-bold text-white">房都督AI</span>
        </div>
        
        <div className="px-4 py-2">
          <span className="text-xs text-slate-500 uppercase tracking-wider">管理后台</span>
        </div>

        <nav className="py-2">
          {menuItems.map((item) => (
            <Link
              key={item.text}
              to={item.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary text-white'
                  : 'text-slate-300 hover:bg-slate-700'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.text}</span>
            </Link>
          ))}
        </nav>

        <div className="border-t border-slate-700 p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-medium">
              {admin.username?.charAt(0).toUpperCase() || 'A'}
            </div>
            <div>
              <p className="text-sm font-medium text-white">{admin.username}</p>
              <p className="text-xs text-slate-400">{admin.email}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              to="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="flex-1 text-center text-sm bg-slate-700 text-slate-300 py-2 rounded hover:bg-slate-600"
            >
              返回前台
            </Link>
            <button
              onClick={() => {
                handleLogout();
                setMobileMenuOpen(false);
              }}
              className="p-2 rounded bg-red-600/20 text-red-400 hover:bg-red-600/30"
            >
              🚪
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main 
        className={`flex-1 transition-all duration-300 pt-16 md:pt-0 ${
          sidebarOpen ? 'md:ml-64' : 'md:ml-20'
        }`}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;
