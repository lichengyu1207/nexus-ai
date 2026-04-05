import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

interface IPInfo {
  valid: boolean;
  ip_id?: string;
  ip_name?: string;
}

const ReferralDetector: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [ipInfo, setIPInfo] = useState<IPInfo | null>(null);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const ref = searchParams.get('ref');
    
    if (ref) {
      const storedRef = localStorage.getItem('referral_code');
      
      if (!storedRef || storedRef !== ref) {
        localStorage.setItem('referral_code', ref);
        checkReferralCode(ref);
      }
    }
  }, [searchParams]);

  const checkReferralCode = async (ref: string) => {
    try {
      const response = await fetch(`/api/ip/check?ref=${ref}`);
      const data = await response.json();
      
      if (data.valid) {
        setIPInfo(data);
        setShowBanner(true);
      }
    } catch (error) {
      console.error('Failed to check referral code:', error);
    }
  };

  const handleClose = () => {
    setShowBanner(false);
  };

  if (!showBanner || !ipInfo?.valid) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex justify-center p-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg shadow-lg p-4 max-w-md flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🎉</span>
          <span className="text-sm text-blue-800">
            您是通过 <strong>{ipInfo.ip_name}</strong> 的推荐链接访问的
          </span>
        </div>
        <button
          onClick={handleClose}
          className="text-blue-500 hover:text-blue-700 text-xl font-bold"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default ReferralDetector;
