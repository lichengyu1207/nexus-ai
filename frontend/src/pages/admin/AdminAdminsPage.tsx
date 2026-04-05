import React, { useState, useEffect } from 'react';

interface Admin {
  id: string;
  email: string;
  username: string;
  role: 'admin' | 'super_admin';
  permissions: Record<string, boolean>;
  last_login: string;
  created_at: string;
  created_by: string;
}

const AdminAdminsPage: React.FC = () => {
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState<Admin | null>(null);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    role: 'admin' as 'admin' | 'super_admin',
    permissions: {
      can_manage_users: true,
      can_manage_content: true,
      can_view_analytics: true,
      can_manage_settings: false,
    },
  });

  useEffect(() => {
    fetchAdmins();
  }, []);

  const fetchAdmins = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/admin/admins', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setAdmins(data.admins || []);
      }
    } catch (error) {
      console.error('Failed to fetch admins:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const token = localStorage.getItem('token');
      const url = editingAdmin
        ? `http://localhost:8000/api/admin/admins/${editingAdmin.id}`
        : 'http://localhost:8000/api/admin/admins';
      const method = editingAdmin ? 'PUT' : 'POST';

      const body = editingAdmin
        ? { role: formData.role, permissions: formData.permissions }
        : formData;

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        setShowModal(false);
        setEditingAdmin(null);
        setFormData({
          email: '',
          username: '',
          password: '',
          role: 'admin',
          permissions: {
            can_manage_users: true,
            can_manage_content: true,
            can_view_analytics: true,
            can_manage_settings: false,
          },
        });
        fetchAdmins();
      } else {
        const error = await response.json();
        alert(error.detail || '操作失败');
      }
    } catch (error) {
      console.error('Failed to save admin:', error);
      alert('操作失败');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除此管理员吗？')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/admins/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        fetchAdmins();
      } else {
        alert('删除失败');
      }
    } catch (error) {
      console.error('Failed to delete admin:', error);
      alert('删除失败');
    }
  };

  const openEditModal = (admin: Admin) => {
    setEditingAdmin(admin);
    setFormData({
      email: admin.email,
      username: admin.username,
      password: '',
      role: admin.role,
      permissions: admin.permissions || {
        can_manage_users: true,
        can_manage_content: true,
        can_view_analytics: true,
        can_manage_settings: false,
      },
    });
    setShowModal(true);
  };

  const getRoleColor = (role: string) => {
    return role === 'super_admin'
      ? 'bg-purple-100 text-purple-700'
      : 'bg-blue-100 text-blue-700';
  };

  const getRoleName = (role: string) => {
    return role === 'super_admin' ? '超级管理员' : '管理员';
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">管理员管理</h1>
        <button
          onClick={() => {
            setEditingAdmin(null);
            setFormData({
              email: '',
              username: '',
              password: '',
              role: 'admin',
              permissions: {
                can_manage_users: true,
                can_manage_content: true,
                can_view_analytics: true,
                can_manage_settings: false,
              },
            });
            setShowModal(true);
          }}
          className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
        >
          添加管理员
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="text-center py-10">加载中...</div>
        ) : admins.length === 0 ? (
          <div className="text-center py-10 text-gray-500">暂无管理员</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">邮箱</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户名</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">最后登录</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {admins.map((admin) => (
                <tr key={admin.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{admin.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{admin.username}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${getRoleColor(admin.role)}`}>
                      {getRoleName(admin.role)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {admin.last_login ? new Date(admin.last_login).toLocaleString('zh-CN') : '从未登录'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(admin.created_at).toLocaleDateString('zh-CN')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => openEditModal(admin)}
                      className="text-primary hover:underline mr-3"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => handleDelete(admin.id)}
                      className="text-red-600 hover:underline"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">
              {editingAdmin ? '编辑管理员' : '添加管理员'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!editingAdmin && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required={!editingAdmin}
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'super_admin' })}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="admin">管理员</option>
                  <option value="super_admin">超级管理员</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">权限</label>
                <div className="space-y-2">
                  {Object.entries(formData.permissions).map(([key, value]) => (
                    <label key={key} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={(e) => setFormData({
                          ...formData,
                          permissions: { ...formData.permissions, [key]: e.target.checked },
                        })}
                        className="mr-2"
                      />
                      <span className="text-sm">
                        {key === 'can_manage_users' && '用户管理'}
                        {key === 'can_manage_content' && '内容管理'}
                        {key === 'can_view_analytics' && '查看统计'}
                        {key === 'can_manage_settings' && '系统设置'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark disabled:opacity-50"
                >
                  {saving ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAdminsPage;
