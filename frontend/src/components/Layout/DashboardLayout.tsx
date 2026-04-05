import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';

interface UserInfo {
  id: string;
  email: string;
  username: string;
  role: string;
  integral: number;
  source: string | null;
  source_name: string | null;
  bonus_label: string | null;
  membership_level: string;
}

const menuItems = [
  { text: '仪表盘', icon: '📊', path: '/dashboard' },
  { text: '房产分析', icon: '🏠', path: '/dashboard/property-analysis' },
  { text: '我的报告', icon: '📋', path: '/dashboard/my-reports' },
  { text: '账户设置', icon: '⚙️', path: '/dashboard/settings' },
];

const DashboardLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
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
          setUser(userData);
        } else {
          localStorage.removeItem('token');
          navigate('/login');
        }
      } catch (error) {
        console.error('Failed to fetch user:', error);
      }
    };

    fetchUser();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (!user) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <aside 
        className={`hidden md:flex flex-col fixed left-0 top-0 h-full bg-white border-r border-gray-200 z-40 transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
          {sidebarOpen && (
            <Link to="/" className="text-lg font-bold text-primary hover:text-primaryDark">
              房都督AI
            </Link>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded hover:bg-gray-100 text-gray-500"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>
        
        <nav className="flex-1 py-4 overflow-y-auto">
          {menuItems.map((item) => (
            <Link
              key={item.text}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary/10 text-primary border-r-2 border-primary'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              title={!sidebarOpen ? item.text : undefined}
            >
              <span className="text-lg">{item.icon}</span>
              {sidebarOpen && <span>{item.text}</span>}
            </Link>
          ))}
          
          {/* IP入口 */}
          {sidebarOpen && (
            <div className="mt-4 px-4">
              <div className="border-t border-gray-200 pt-4">
                <p className="text-xs text-gray-400 mb-2">IP合作计划</p>
                <Link
                  to="/ip"
                  className="flex items-center gap-2 text-sm text-primary hover:text-primaryDark"
                >
                  <span>🎫</span>
                  <span>IP工作台</span>
                </Link>
              </div>
            </div>
          )}
        </nav>

        <div className="border-t border-gray-200 p-4">
          {sidebarOpen ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-medium">
                  {user.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{user.username}</p>
                  <p className="text-xs text-gray-500 truncate">{user.email}</p>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-primary font-medium">{user.integral} 积分</span>
                {user.membership_level && (
                  <span className="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded">
                    {user.membership_level}
                  </span>
                )}
              </div>
              <button
                onClick={handleLogout}
                className="w-full text-left text-sm text-gray-600 hover:text-red-600 py-2 flex items-center gap-2"
              >
                <span>🚪</span>
                <span>退出登录</span>
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-medium">
                {user.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded hover:bg-gray-100 text-gray-500"
                title="退出登录"
              >
                🚪
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-30 flex items-center justify-between px-4">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded hover:bg-gray-100 text-gray-500"
        >
          ☰
        </button>
        <Link to="/" className="text-lg font-bold text-primary">房都督AI</Link>
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
        className={`md:hidden fixed left-0 top-0 h-full bg-white z-50 w-64 transform transition-transform duration-300 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-16 flex items-center px-4 border-b border-gray-200">
          <Link to="/" className="text-lg font-bold text-primary">房都督AI</Link>
        </div>
        
        <nav className="py-4">
          {menuItems.map((item) => (
            <Link
              key={item.text}
              to={item.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary/10 text-primary'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.text}</span>
            </Link>
          ))}
          
          <div className="mt-4 px-4 border-t border-gray-200 pt-4">
            <p className="text-xs text-gray-400 mb-2">IP合作计划</p>
            <Link
              to="/ip"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-2 text-sm text-primary hover:text-primaryDark py-2"
            >
              <span>🎫</span>
              <span>IP工作台</span>
            </Link>
          </div>
        </nav>

        <div className="border-t border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-medium">
              {user.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div>
              <p className="text-sm font-medium">{user.username}</p>
              <p className="text-xs text-gray-500">{user.integral} 积分</p>
            </div>
          </div>
          <button
            onClick={() => {
              handleLogout();
              setMobileMenuOpen(false);
            }}
            className="w-full text-left text-sm text-gray-600 hover:text-red-600 py-2 flex items-center gap-2"
          >
            <span>🚪</span>
            <span>退出登录</span>
          </button>
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

export default DashboardLayout;
