import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { getStoredSource } from '@/utils/sourceTracker';
import SliderCaptcha from '@/components/SliderCaptcha';

const RegisterPage: React.FC = () => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [referredBy, setReferredBy] = useState('');
  const [referredByOther, setReferredByOther] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCaptchaVerified, setIsCaptchaVerified] = useState(false);
  
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!isCaptchaVerified) {
      setError(t('auth.captchaRequired'));
      return;
    }

    if (password !== confirmPassword) {
      setError(t('auth.passwordMismatch'));
      return;
    }

    if (password.length < 6) {
      setError(t('auth.passwordMinLength'));
      return;
    }

    setIsLoading(true);

    try {
      const source = getStoredSource();
      
      await register({ 
        email, 
        password, 
        full_name: fullName || undefined,
        source,
        referred_by: referredBy || undefined,
        referred_by_other: referredBy === 'other' ? referredByOther : undefined
      });
      navigate('/login', { state: { message: t('auth.registerSuccessMessage') } });
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.registerFailedMessage'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">F</span>
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            {t('auth.createAccount')}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {t('auth.registerSubtitle')}
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                {t('auth.email')}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                placeholder={t('auth.emailPlaceholder')}
              />
            </div>

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-gray-700">
                {t('auth.fullNameOptional')}
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                placeholder={t('auth.fullNamePlaceholder')}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                {t('auth.password')}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                placeholder={t('auth.passwordHint')}
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                {t('auth.confirmPassword')}
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                placeholder={t('auth.confirmPasswordPlaceholder')}
              />
            </div>

            <div>
              <label htmlFor="referredBy" className="block text-sm font-medium text-gray-700">
                {t('auth.referralSource')}
              </label>
              <select
                id="referredBy"
                name="referredBy"
                value={referredBy}
                onChange={(e) => setReferredBy(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm bg-white"
              >
                <option value="">{t('auth.referralPlaceholder')}</option>
                <option value="laohai">{t('auth.referralFounder')}</option>
                <option value="friend">{t('auth.referralFriend')}</option>
                <option value="search">{t('auth.referralSearch')}</option>
                <option value="social">{t('auth.referralSocial')}</option>
                <option value="ad">{t('auth.referralAd')}</option>
                <option value="other">{t('auth.referralOther')}</option>
              </select>
            </div>

            {referredBy === 'other' && (
              <div>
                <label htmlFor="referredByOther" className="block text-sm font-medium text-gray-700">
                  {t('auth.referralOtherLabel')}
                </label>
                <input
                  id="referredByOther"
                  name="referredByOther"
                  type="text"
                  value={referredByOther}
                  onChange={(e) => setReferredByOther(e.target.value)}
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                  placeholder={t('auth.referralOtherPlaceholder')}
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('auth.captchaLabel')} <span className="text-red-500">*</span>
              </label>
              <SliderCaptcha 
                onSuccess={() => setIsCaptchaVerified(true)}
                onFail={() => setIsCaptchaVerified(false)}
              />
              {isCaptchaVerified && (
                <p className="mt-1 text-sm text-green-600">{t('auth.captchaVerified')}</p>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? t('auth.registering') : t('nav.register')}
          </button>

          <div className="text-center">
            <span className="text-sm text-gray-600">{t('auth.hasAccount')}</span>
            <Link to="/login" className="ml-1 text-sm font-medium text-primary-600 hover:text-primary-500">
              {t('auth.loginNow')}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterPage;
