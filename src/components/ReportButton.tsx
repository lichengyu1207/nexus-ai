import React, { useState, useEffect } from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';
import ReportModal from './ReportModal';
import { ReportType, checkHasReported } from '@/api/reports';

interface ReportButtonProps {
  type: ReportType;
  id: string;
  title?: string;
  variant?: 'icon' | 'text' | 'button';
  className?: string;
}

const ReportButton: React.FC<ReportButtonProps> = ({
  type,
  id,
  title,
  variant = 'icon',
  className = '',
}) => {
  const { user } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [hasReported, setHasReported] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const check = async () => {
      if (!user) {
        setChecking(false);
        return;
      }
      const reported = await checkHasReported(type, id);
      setHasReported(reported);
      setChecking(false);
    };
    check();
  }, [type, id, user]);

  if (!user) {
    return null;
  }

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowModal(true);
  };

  if (hasReported) {
    if (variant === 'icon') {
      return (
        <span
          className={`text-gray-400 cursor-not-allowed ${className}`}
          title="您已举报过此内容"
        >
          <ExclamationTriangleIcon className="w-4 h-4" />
        </span>
      );
    }
    return (
      <span
        className={`text-xs text-gray-400 ${className}`}
      >
        已举报
      </span>
    );
  }

  if (variant === 'icon') {
    return (
      <>
        <button
          onClick={handleClick}
          className={`text-gray-400 hover:text-red-500 transition-colors ${className}`}
          title="举报"
        >
          <ExclamationTriangleIcon className="w-4 h-4" />
        </button>
        {showModal && (
          <ReportModal
            reportedType={type}
            reportedId={id}
            reportedTitle={title}
            onClose={() => setShowModal(false)}
            onSubmitted={() => setHasReported(true)}
          />
        )}
      </>
    );
  }

  if (variant === 'text') {
    return (
      <>
        <button
          onClick={handleClick}
          className={`text-xs text-gray-500 hover:text-red-500 transition-colors ${className}`}
        >
          举报
        </button>
        {showModal && (
          <ReportModal
            reportedType={type}
            reportedId={id}
            reportedTitle={title}
            onClose={() => setShowModal(false)}
            onSubmitted={() => setHasReported(true)}
          />
        )}
      </>
    );
  }

  return (
    <>
      <button
        onClick={handleClick}
        className={`flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-red-50 hover:border-red-300 hover:text-red-600 transition-colors ${className}`}
      >
        <ExclamationTriangleIcon className="w-4 h-4" />
        举报
      </button>
      {showModal && (
        <ReportModal
          reportedType={type}
          reportedId={id}
          reportedTitle={title}
          onClose={() => setShowModal(false)}
          onSubmitted={() => setHasReported(true)}
        />
      )}
    </>
  );
};

export default ReportButton;
