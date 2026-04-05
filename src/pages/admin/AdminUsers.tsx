import React, { useState, useEffect, useCallback } from 'react';
import {
  UsersIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
} from '@heroicons/react/24/outline';
import { adminUsersApi, AdminUser } from '@/api/admin/users';
import { UserEditModal, CreateUserModal } from '@/components/admin';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';
import { useAuth } from '@/contexts/AuthContext';

const ROLE_COLORS: Record<string, string> = {
  user: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
  admin: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  super_admin: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
};

const ROLE_LABELS: Record<string, string> = {
  user: '用户',
  admin: '管理员',
  super_admin: '超级管理员',
};

const AdminUsers: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    search: '',
    role: '',
    is_active: '',
  });
  const pageSize = 20;

  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
      };
      
      if (filters.search) params.search = filters.search;
      if (filters.role) params.role = filters.role;
      if (filters.is_active !== '') params.is_active = filters.is_active === 'true';

      const response = await adminUsersApi.list(params);
      setUsers(response.users);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch {
      showToast.error('加载用户失败');
    } finally {
      setIsLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadUsers();
  };

  const handleUserCreated = (user: AdminUser) => {
    setUsers([user, ...users]);
    setTotal(total + 1);
  };

  const handleUserUpdated = () => {
    loadUsers();
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">用户管理</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">共 {total} 个用户</p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <PlusIcon className="w-5 h-5" />
          新增用户
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="搜索邮箱、用户名..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
            />
          </div>
          
          <select
            value={filters.role}
            onChange={(e) => setFilters({ ...filters, role: e.target.value })}
            className="px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          >
            <option value="">全部角色</option>
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
            <option value="super_admin">超级管理员</option>
          </select>
          
          <select
            value={filters.is_active}
            onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
            className="px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          >
            <option value="">全部状态</option>
            <option value="true">活跃</option>
            <option value="false">禁用</option>
          </select>
          
          <button
            type="submit"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            搜索
          </button>
          
          <button
            type="button"
            onClick={() => {
              setFilters({ search: '', role: '', is_active: '' });
              setPage(1);
            }}
            className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            重置
          </button>
        </form>
      </div>

      {/* Users Table */}
      {isLoading ? (
        <LoadingCard message="加载用户..." />
      ) : users.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <UsersIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">暂无用户</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">没有找到符合条件的用户</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">用户</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">邮箱</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">角色</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">注册时间</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
                            {(user.full_name || user.email)[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {user.full_name || user.username}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">@{user.username}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{user.email}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded ${ROLE_COLORS[user.role]}`}>
                        {user.role === 'admin' || user.role === 'super_admin' ? (
                          <ShieldCheckIcon className="w-3 h-3" />
                        ) : null}
                        {ROLE_LABELS[user.role] || user.role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {user.is_active ? (
                        <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                          <CheckCircleIcon className="w-4 h-4" />
                          活跃
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-red-600 dark:text-red-400 text-sm">
                          <XCircleIcon className="w-4 h-4" />
                          禁用
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{formatDate(user.created_at)}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setEditingUser(user)}
                        disabled={user.id === currentUser?.id}
                        className="flex items-center gap-1 px-2 py-1 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded disabled:opacity-50"
                      >
                        <PencilIcon className="w-4 h-4" />
                        编辑
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                第 {page} 页，共 {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                >
                  <ChevronLeftIcon className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                >
                  <ChevronRightIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Edit Modal */}
      {editingUser && (
        <UserEditModal
          user={editingUser}
          isOpen={true}
          onClose={() => setEditingUser(null)}
          onUpdate={handleUserUpdated}
        />
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateUserModal
          isOpen={true}
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleUserCreated}
        />
      )}
    </div>
  );
};

export default AdminUsers;
