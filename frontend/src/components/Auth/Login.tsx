import React, { useState } from 'react';

const Login: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.detail || '登录失败，请检查邮箱和密码');
        return;
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError('网络错误，请稍后重试');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center mica py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-20 left-10 w-72 h-72 bg-fluent-gold-500/10 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-fluent-deepOcean-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />
      
      <div className="max-w-md w-full relative">
        <div className="acrylic rounded-3xl shadow-fluent-xl p-8 border border-white/30">
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 rounded-2xl flex items-center justify-center text-3xl shadow-gold-glow mb-4">
              🏠
            </div>
            <h2 className="text-3xl font-bold text-fluent-deepOcean-500">
              登录房都督AI
            </h2>
            <p className="mt-2 text-sm text-fluent-deepOcean-300">
              或{' '}
              <a
                href="/register"
                className="font-medium text-fluent-gold-500 hover:text-fluent-gold-600 transition-colors"
              >
                创建新账户
              </a>
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6" role="alert">
              <strong className="font-bold">错误：</strong>
              <span className="block sm:inline"> {error}</span>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-fluent-deepOcean-500 mb-2">
                  邮箱地址
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="appearance-none block w-full px-4 py-3 border-2 border-fluent-deepOcean-200 rounded-xl placeholder-fluent-deepOcean-300 text-fluent-deepOcean-500 focus:outline-none focus:border-fluent-gold-400 focus:ring-2 focus:ring-fluent-gold-400/20 bg-white/50 backdrop-blur-sm transition-all duration-300"
                  placeholder="请输入邮箱地址"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-fluent-deepOcean-500 mb-2">
                  密码
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className="appearance-none block w-full px-4 py-3 border-2 border-fluent-deepOcean-200 rounded-xl placeholder-fluent-deepOcean-300 text-fluent-deepOcean-500 focus:outline-none focus:border-fluent-gold-400 focus:ring-2 focus:ring-fluent-gold-400/20 bg-white/50 backdrop-blur-sm transition-all duration-300"
                  placeholder="请输入密码"
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-fluent-gold-500 focus:ring-fluent-gold-400 border-fluent-deepOcean-200 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-fluent-deepOcean-400">
                  记住我
                </label>
              </div>
              <a href="/forgot-password" className="text-sm text-fluent-gold-500 hover:text-fluent-gold-600 transition-colors">
                忘记密码？
              </a>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-fluent-deepOcean-500 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 hover:shadow-gold-glow focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-fluent-gold-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
              >
                {loading ? (
                  <span className="inline-block animate-spin rounded-full h-5 w-5 border-2 border-fluent-deepOcean-500 border-t-transparent mr-2"></span>
                ) : null}
                登录
              </button>
            </div>
          </form>

          <div className="mt-6 p-4 bg-fluent-deepOcean-50 rounded-xl border border-fluent-deepOcean-100">
            <p className="text-sm text-fluent-deepOcean-500 mb-2 font-medium">测试账号：</p>
            <div className="text-xs text-fluent-deepOcean-400 space-y-1">
              <p>laohai来源: xiaowang@test.com / test123456</p>
              <p>seo来源: laozhang@test.com / test123456</p>
              <p>urgent来源: chenjie@test.com / test123456</p>
              <p>direct来源: test_newuser@example.com / test123456</p>
            </div>
          </div>
        </div>
        
        <div className="absolute -bottom-4 -right-4 w-16 h-16 bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 rounded-full flex items-center justify-center text-2xl shadow-gold-glow animate-float cursor-pointer hover:scale-110 transition-transform">
          🐶
        </div>
      </div>
    </div>
  );
};

export default Login;
