import React, { useState, useEffect } from 'react';
import { XMarkIcon, KeyIcon, TrashIcon } from '@heroicons/react/24/outline';
import { AdminUser, adminUsersApi } from '@/api/admin/users';
import showToast from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';

interface UserEditModalProps {
  user: AdminUser;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const UserEditModal: React.FC<UserEditModalProps> = ({ user, isOpen, onClose, onUpdate }) => {
  const { user: currentUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user.full_name || '',
    role: user.role,
    is_active: user.is_active,
  });
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [newPassword, setNewPassword] = useState<string | null>(null);

  useEffect(() => {
    setFormData({
      full_name: user.full_name || '',
      role: user.role,
      is_active: user.is_active,
    });
    setNewPassword(null);
  }, [user]);

  if (!isOpen) return null;

  const isCurrentUser = currentUser?.id === user.id;
  const isSuperAdmin = user.role === 'super_admin';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isCurrentUser) {
      showToast.error('不能修改自己的信息');
      return;
    }

    setIsLoading(true);
    try {
      await adminUsersApi.update(user.id, {
        full_name: formData.full_name || undefined,
        role: formData.role,
        is_active: formData.is_active,
      });
      showToast.success('用户信息已更新');
      onUpdate();
      onClose();
    } catch {
      showToast.error('更新失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (isCurrentUser) {
      showToast.error('不能重置自己的密码');
      return;
    }

    setIsLoading(true);
    try {
      const result = await adminUsersApi.resetPassword(user.id, false);
      setNewPassword(result.new_password || null);
      setShowResetConfirm(false);
      showToast.success('密码已重置');
    } catch {
      showToast.error('重置密码失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (isCurrentUser) {
      showToast.error('不能删除自己');
      return;
    }

    if (isSuperAdmin) {
      showToast.error('不能删除超级管理员');
      return;
    }

    if (!confirm(`确定要删除用户 ${user.email} 吗？此操作不可撤销。`)) return;

    setIsLoading(true);
    try {
      await adminUsersApi.delete(user.id);
      showToast.success('用户已删除');
      onUpdate();
      onClose();
    } catch {
      showToast.error('删除失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
        
        <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">编辑用户</h3>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            {/* User Info */}
            <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
                <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
                  {(user.full_name || user.email)[0].toUpperCase()}
                </span>
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  {user.full_name || user.username}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{user.email}</p>
              </div>
            </div>

            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                全名
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                placeholder="用户全名"
              />
            </div>

            {/* Role */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                角色
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                disabled={isCurrentUser || isSuperAdmin}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
              >
                <option value="user">普通用户</option>
                <option value="admin">管理员</option>
                <option value="super_admin">超级管理员</option>
              </select>
              {isSuperAdmin && (
                <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                  超级管理员角色不可修改
                </p>
              )}
            </div>

            {/* Status */}
            <div>
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.value })}
                  disabled={isCurrentUser || isSuperAdmin}
                  className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-primary-600"
                />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">账号激活</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    禁用后用户将无法登录
                  </p>
                </div>
              </label>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={() => setShowResetConfirm(true)}
                disabled={isCurrentUser}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-lg hover:bg-yellow-100 dark:hover:bg-yellow-900/50 disabled:opacity-50"
              >
                <KeyIcon className="w-4 h-4" />
                重置密码
              </button>
              
              <button
                type="button"
                onClick={handleDelete}
                disabled={isCurrentUser || isSuperAdmin}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 disabled:opacity-50"
              >
                <TrashIcon className="w-4 h-4" />
                删除用户
              </button>
            </div>

            {/* New Password Display */}
            {newPassword && (
              <div className="p-3 bg-green-50 dark:bg-green-900/30 rounded-lg">
                <p className="text-sm font-medium text-green-700 dark:text-green-400 mb-1">
                  新密码已生成：
                </p>
                <code className="text-sm bg-white dark:bg-gray-800 px-2 py-1 rounded border border-green-200 dark:border-green-800">
                  {newPassword}
                </code>
                <p className="text-xs text-green-600 dark:text-green-500 mt-1">
                  请将此密码发送给用户
                </p>
              </div>
            )}

            {/* Submit */}
            <div className="flex justify-end gap-2 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={isLoading || isCurrentUser}
                className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {isLoading ? '保存中...' : '保存'}
              </button>
            </div>
          </form>

          {/* Reset Password Confirm */}
          {showResetConfirm && (
            <div className="absolute inset-0 bg-white dark:bg-gray-800 rounded-xl p-4 flex flex-col items-center justify-center">
              <KeyIcon className="w-12 h-12 text-yellow-500 mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                确认重置密码？
              </h4>
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-4">
                将为用户 {user.email} 生成新的随机密码
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  取消
                </button>
                <button
                  onClick={handleResetPassword}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
                >
                  确认重置
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserEditModal;
