import { useState, useEffect, useCallback } from 'react';
import { useUserStore } from '../stores/userStore';
import { authApi } from '../api/auth';

export const useAuth = () => {
  const { user, token, isAuthenticated, login, logout, setUser } = useUserStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkAuth = useCallback(async () => {
    if (!token) return false;
    
    setLoading(true);
    try {
      const userData = await authApi.me();
      setUser(userData);
      return true;
    } catch (err) {
      logout();
      return false;
    } finally {
      setLoading(false);
    }
  }, [token, setUser, logout]);

  const signIn = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const { user, token } = await authApi.login(email, password);
      login(user, token);
      localStorage.setItem('token', token);
      return { success: true };
    } catch (err: any) {
      const message = err?.detail || '登录失败';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (data: {
    email: string;
    password: string;
    username?: string;
    source?: string;
    ref?: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const { user, token } = await authApi.register(data);
      login(user, token);
      localStorage.setItem('token', token);
      return { success: true };
    } catch (err: any) {
      const message = err?.detail || '注册失败';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const signOut = () => {
    logout();
    localStorage.removeItem('token');
  };

  return {
    user,
    token,
    isAuthenticated,
    loading,
    error,
    checkAuth,
    signIn,
    signUp,
    signOut,
  };
};

export default useAuth;
