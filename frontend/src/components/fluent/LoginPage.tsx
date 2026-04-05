import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, Github, Chrome } from 'lucide-react';
import FluentButton from './FluentButton';
import AcrylicContainer from './AcrylicContainer';

interface LoginPageProps {
  onLogin?: (email: string, password: string) => void;
  onRegister?: (name: string, email: string, password: string) => void;
  onOAuthLogin?: (provider: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onRegister, onOAuthLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isLogin) {
      onLogin?.(formData.email, formData.password);
    } else {
      if (formData.password === formData.confirmPassword) {
        onRegister?.(formData.name, formData.email, formData.password);
      }
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="absolute inset-0 mica">
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%230A1A2F' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
      </div>

      <div className="absolute left-0 top-0 bottom-0 w-1/3 hidden lg:flex items-center justify-center">
        <motion.div
          className="relative"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div className="relative w-80 h-96">
            <motion.div
              className="absolute inset-0 rounded-2xl bg-gradient-to-br from-fluent-deepOcean-500/20 to-fluent-gold-500/20"
              animate={{
                boxShadow: [
                  '0 0 30px rgba(212, 175, 55, 0.2)',
                  '0 0 60px rgba(212, 175, 55, 0.3)',
                  '0 0 30px rgba(212, 175, 55, 0.2)',
                ],
              }}
              transition={{ duration: 3, repeat: Infinity }}
            />
            <div className="relative z-10 flex flex-col items-center justify-center h-full">
              <motion.div
                className="text-8xl mb-4"
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              >
                🏛️
              </motion.div>
              <motion.div
                className="text-6xl"
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              >
                🪭
              </motion.div>
              <div className="mt-8 text-center">
                <h2 className="text-2xl font-heading text-fluent-deepOcean-500">房都督</h2>
                <p className="text-gray-500 mt-2">智能房产决策平台</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="relative z-10 min-h-screen flex items-center justify-center lg:justify-end lg:pr-20 p-4">
        <motion.div
          className="w-full max-w-md"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <AcrylicContainer
            blur="lg"
            opacity={0.8}
            goldAccent
            className="p-8"
          >
            <motion.div variants={itemVariants} className="text-center mb-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-fluent-deepOcean-500 to-fluent-deepOcean-700 flex items-center justify-center">
                <span className="text-fluent-gold-400 font-bold text-2xl">督</span>
              </div>
              <h1 className="text-2xl font-bold text-fluent-deepOcean-500">
                {isLogin ? '欢迎回来' : '创建账户'}
              </h1>
              <p className="text-gray-500 mt-2">
                {isLogin ? '登录您的账户继续使用' : '注册成为房都督用户'}
              </p>
            </motion.div>

            <motion.form variants={itemVariants} onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="用户名"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/50 border border-white/30 focus:border-fluent-gold-500 focus:ring-2 focus:ring-fluent-gold-500/20 outline-none transition-all"
                    required={!isLogin}
                  />
                </div>
              )}

              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  placeholder="邮箱地址"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/50 border border-white/30 focus:border-fluent-gold-500 focus:ring-2 focus:ring-fluent-gold-500/20 outline-none transition-all"
                  required
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="密码"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full pl-10 pr-10 py-3 rounded-xl bg-white/50 border border-white/30 focus:border-fluent-gold-500 focus:ring-2 focus:ring-fluent-gold-500/20 outline-none transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>

              {!isLogin && (
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="确认密码"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/50 border border-white/30 focus:border-fluent-gold-500 focus:ring-2 focus:ring-fluent-gold-500/20 outline-none transition-all"
                    required={!isLogin}
                  />
                </div>
              )}

              {isLogin && (
                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded border-gray-300 text-fluent-gold-500 focus:ring-fluent-gold-500"
                    />
                    <span className="text-gray-600">记住我</span>
                  </label>
                  <a href="#" className="text-fluent-gold-500 hover:text-fluent-gold-600">
                    忘记密码？
                  </a>
                </div>
              )}

              <motion.div variants={itemVariants}>
                <FluentButton
                  variant="primary"
                  fullWidth
                  size="lg"
                  icon={<ArrowRight className="w-5 h-5" />}
                  iconPosition="right"
                >
                  {isLogin ? '登录' : '注册'}
                </FluentButton>
              </motion.div>
            </motion.form>

            <motion.div variants={itemVariants} className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white/70 text-gray-500">或使用以下方式</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4">
                <motion.button
                  type="button"
                  onClick={() => onOAuthLogin?.('google')}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white/50 border border-white/30 hover:bg-white/70 transition-all"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Chrome className="w-5 h-5 text-red-500" />
                  <span className="text-sm font-medium text-gray-700">Google</span>
                </motion.button>
                <motion.button
                  type="button"
                  onClick={() => onOAuthLogin?.('github')}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white/50 border border-white/30 hover:bg-white/70 transition-all"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Github className="w-5 h-5 text-gray-700" />
                  <span className="text-sm font-medium text-gray-700">GitHub</span>
                </motion.button>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="mt-6 text-center">
              <p className="text-gray-500">
                {isLogin ? '还没有账户？' : '已有账户？'}
                <motion.button
                  type="button"
                  onClick={() => setIsLogin(!isLogin)}
                  className="ml-2 text-fluent-gold-500 hover:text-fluent-gold-600 font-medium"
                  whileHover={{ scale: 1.05 }}
                >
                  {isLogin ? '立即注册' : '立即登录'}
                </motion.button>
              </p>
            </motion.div>
          </AcrylicContainer>

          <motion.p
            variants={itemVariants}
            className="mt-4 text-center text-xs text-gray-400"
          >
            登录即表示您同意我们的
            <a href="#" className="text-fluent-gold-500 hover:underline">服务条款</a>
            和
            <a href="#" className="text-fluent-gold-500 hover:underline">隐私政策</a>
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
