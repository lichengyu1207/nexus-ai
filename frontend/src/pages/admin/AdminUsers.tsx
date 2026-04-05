import React, { useState, useEffect } from 'react';

interface User {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_active: boolean;
  integral: number;
  membership_level: string;
  created_at: string;
}

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchUsers();
  }, [page, rowsPerPage]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/api/admin/users?page=${page + 1}&page_size=${rowsPerPage}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await res.json();
      setUsers(result.users || []);
      setTotal(result.total || 0);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(
    (user) =>
      user.email.toLowerCase().includes(search.toLowerCase()) ||
      user.full_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">用户管理</h1>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
            <input
              type="text"
              placeholder="搜索用户..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-4 font-medium">用户名</th>
                    <th className="text-left py-3 px-4 font-medium">邮箱</th>
                    <th className="text-left py-3 px-4 font-medium">积分</th>
                    <th className="text-left py-3 px-4 font-medium">会员等级</th>
                    <th className="text-left py-3 px-4 font-medium">状态</th>
                    <th className="text-left py-3 px-4 font-medium">注册时间</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {user.full_name}
                          {user.is_admin && (
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                              管理员
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">{user.email}</td>
                      <td className="py-3 px-4">{user.integral}</td>
                      <td className="py-3 px-4">{user.membership_level || '普通'}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs ${
                          user.is_active 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {user.is_active ? '活跃' : '禁用'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {new Date(user.created_at).toLocaleDateString('zh-CN')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-4 border-t flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">每页行数:</span>
                <select
                  value={rowsPerPage}
                  onChange={(e) => {
                    setRowsPerPage(parseInt(e.target.value, 10));
                    setPage(0);
                  }}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">
                  {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, total)} 共 {total} 条
                </span>
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                >
                  上一页
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={(page + 1) * rowsPerPage >= total}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                >
                  下一页
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AdminUsers;
