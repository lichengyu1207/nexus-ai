import React, { useState, useRef, useCallback } from 'react';
import { UserCircleIcon, CameraIcon, ArrowUpTrayIcon, XMarkIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface AvatarUploaderProps {
  currentAvatar?: string | null;
  onAvatarChange?: (avatarUrl: string) => void;
  size?: 'sm' | 'md' | 'lg';
}

const AvatarUploader: React.FC<AvatarUploaderProps> = ({
  currentAvatar,
  onAvatarChange,
  size = 'md',
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
  };

  const iconSizes = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  const handleFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      showToast.error('请选择图片文件');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      showToast.error('图片大小不能超过5MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const avatarUrl = response.data.avatar_url;
      setPreview(null);
      onAvatarChange?.(avatarUrl);
      showToast.success('头像已更新');
    } catch {
      showToast.error('上传失败');
      setPreview(null);
    } finally {
      setIsUploading(false);
    }
  }, [onAvatarChange]);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const displayAvatar = preview || currentAvatar;

  return (
    <div className="relative inline-block">
      <div
        className={`
          ${sizeClasses[size]}
          rounded-full overflow-hidden cursor-pointer
          border-2 border-gray-200 dark:border-gray-700
          bg-gray-100 dark:bg-gray-800
          transition-all duration-200
          hover:border-primary-400
          ${dragActive ? 'border-primary-500 ring-2 ring-primary-200' : ''}
        `}
        onClick={handleClick}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {displayAvatar ? (
          <img
            src={displayAvatar}
            alt="Avatar"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-primary-100 dark:bg-primary-900">
            <UserCircleIcon className={`${iconSizes[size]} text-primary-400`} />
          </div>
        )}

        {isUploading && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={handleClick}
        className="absolute bottom-0 right-0 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white shadow-lg hover:bg-primary-700 transition-colors"
      >
        <CameraIcon className="w-4 h-4" />
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="hidden"
      />

      {preview && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setPreview(null);
          }}
          className="absolute top-0 right-0 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-lg hover:bg-red-600"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default AvatarUploader;
