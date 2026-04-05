import React, { useState, useEffect } from 'react';

interface IP {
  id: string;
  user_id: string;
  user_email: string;
  name: string;
  contact: string;
  platform: string;
  platform_id: string;
  followers: number;
  status: string;
  commission_rate: number;
  referral_code: string;
  available_commission: number;
  total_commission: number;
  created_at: string;
}

interface Withdrawal {
  id: string;
  ip_id: string;
  ip_name: string;
  ip_contact: string;
  amount: number;
  account_type: string;
  account_info: string;
  status: string;
  admin_notes: string;
  created_at: string;
  processed_at: string;
}

const AdminIPManagement: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [ips, setIPs] = useState<IP[]>([]);
  const [withdrawals, setWithdrawals] = useState<Withdrawal[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  
  const [editDialog, setEditDialog] = useState(false);
  const [selectedIP, setSelectedIP] = useState<IP | null>(null);
  const [editForm, setEditForm] = useState({
    status: '',
    commission_rate: 20,
    notes: '',
  });
  
  const [withdrawalDialog, setWithdrawalDialog] = useState(false);
  const [selectedWithdrawal, setSelectedWithdrawal] = useState<Withdrawal | null>(null);
  const [withdrawalForm, setWithdrawalForm] = useState({
    status: '',
    admin_notes: '',
  });

  useEffect(() => {
    if (tabValue === 0) {
      fetchIPs();
    } else {
      fetchWithdrawals();
    }
  }, [tabValue, page, rowsPerPage, statusFilter]);

  const fetchIPs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: (page + 1).toString(),
        page_size: rowsPerPage.toString(),
      });
      if (statusFilter) params.append('status', statusFilter);
      
      const res = await fetch(`http://localhost:8000/api/ip/admin/list?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setIPs(data.ips || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Failed to fetch IPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWithdrawals = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: (page + 1).toString(),
        page_size: rowsPerPage.toString(),
      });
      if (statusFilter) params.append('status', statusFilter);
      
      const res = await fetch(`http://localhost:8000/api/ip/admin/withdrawals/list?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setWithdrawals(data.withdrawals || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Failed to fetch withdrawals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditIP = async () => {
    if (!selectedIP) return;
    
    try {
      const token = localStorage.getItem('token');
      await fetch(`http://localhost:8000/api/ip/admin/${selectedIP.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(editForm)
      });
      setEditDialog(false);
      fetchIPs();
    } catch (error) {
      console.error('Failed to update IP:', error);
    }
  };

  const handleProcessWithdrawal = async () => {
    if (!selectedWithdrawal) return;
    
    try {
      const token = localStorage.getItem('token');
      await fetch(`http://localhost:8000/api/ip/admin/withdrawals/${selectedWithdrawal.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(withdrawalForm)
      });
      setWithdrawalDialog(false);
      fetchWithdrawals();
    } catch (error) {
      console.error('Failed to process withdrawal:', error);
    }
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-700',
      pending: 'bg-yellow-100 text-yellow-700',
      suspended: 'bg-red-100 text-red-700',
      approved: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700',
      completed: 'bg-blue-100 text-blue-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getStatusName = (status: string): string => {
    const names: Record<string, string> = {
      active: '活跃',
      pending: '待审核',
      suspended: '已暂停',
      approved: '已通过',
      rejected: '已拒绝',
      completed: '已完成',
    };
    return names[status] || status;
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">IP合作伙伴管理</h1>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => { setTabValue(0); setPage(0); }}
          className={`px-4 py-2 rounded ${tabValue === 0 ? 'bg-primary text-white' : 'bg-gray-100'}`}
        >
          IP列表
        </button>
        <button
          onClick={() => { setTabValue(1); setPage(0); }}
          className={`px-4 py-2 rounded ${tabValue === 1 ? 'bg-primary text-white' : 'bg-gray-100'}`}
        >
          提现管理
        </button>
      </div>

      <div className="mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded px-3 py-2"
        >
          <option value="">全部状态</option>
          {tabValue === 0 ? (
            <>
              <option value="pending">待审核</option>
              <option value="active">活跃</option>
              <option value="suspended">已暂停</option>
            </>
          ) : (
            <>
              <option value="pending">待处理</option>
              <option value="approved">已通过</option>
              <option value="rejected">已拒绝</option>
              <option value="completed">已完成</option>
            </>
          )}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b">
                  {tabValue === 0 ? (
                    <>
                      <th className="text-left py-3 px-4">姓名</th>
                      <th className="text-left py-3 px-4">联系方式</th>
                      <th className="text-left py-3 px-4">平台</th>
                      <th className="text-left py-3 px-4">粉丝数</th>
                      <th className="text-left py-3 px-4">状态</th>
                      <th className="text-left py-3 px-4">佣金比例</th>
                      <th className="text-left py-3 px-4">累计佣金</th>
                      <th className="text-left py-3 px-4">推广码</th>
                      <th className="text-left py-3 px-4">操作</th>
                    </>
                  ) : (
                    <>
                      <th className="text-left py-3 px-4">IP名称</th>
                      <th className="text-left py-3 px-4">联系方式</th>
                      <th className="text-left py-3 px-4">金额</th>
                      <th className="text-left py-3 px-4">账户类型</th>
                      <th className="text-left py-3 px-4">状态</th>
                      <th className="text-left py-3 px-4">操作</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {tabValue === 0 ? (
                  ips.map((ip) => (
                    <tr key={ip.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">{ip.name}</td>
                      <td className="py-3 px-4">{ip.contact}</td>
                      <td className="py-3 px-4">{ip.platform}</td>
                      <td className="py-3 px-4">{ip.followers?.toLocaleString()}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(ip.status)}`}>
                          {getStatusName(ip.status)}
                        </span>
                      </td>
                      <td className="py-3 px-4">{ip.commission_rate}%</td>
                      <td className="py-3 px-4">{(ip.total_commission / 100).toFixed(2)}元</td>
                      <td className="py-3 px-4 font-mono text-xs">{ip.referral_code}</td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => {
                            setSelectedIP(ip);
                            setEditForm({
                              status: ip.status,
                              commission_rate: ip.commission_rate,
                              notes: '',
                            });
                            setEditDialog(true);
                          }}
                          className="text-primary hover:underline text-sm"
                        >
                          编辑
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  withdrawals.map((w) => (
                    <tr key={w.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">{w.ip_name}</td>
                      <td className="py-3 px-4">{w.ip_contact}</td>
                      <td className="py-3 px-4">{(w.amount / 100).toFixed(2)}元</td>
                      <td className="py-3 px-4">{w.account_type}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(w.status)}`}>
                          {getStatusName(w.status)}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {w.status === 'pending' && (
                          <button
                            onClick={() => {
                              setSelectedWithdrawal(w);
                              setWithdrawalForm({ status: 'approved', admin_notes: '' });
                              setWithdrawalDialog(true);
                            }}
                            className="text-primary hover:underline text-sm"
                          >
                            处理
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4">
            <span className="text-sm text-gray-600">
              共 {total} 条记录
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                上一页
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={(page + 1) * rowsPerPage >= total}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          </div>
        </>
      )}

      {/* Edit Dialog */}
      {editDialog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-medium mb-4">编辑IP</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">状态</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="pending">待审核</option>
                  <option value="active">活跃</option>
                  <option value="suspended">已暂停</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">佣金比例(%)</label>
                <input
                  type="number"
                  value={editForm.commission_rate}
                  onChange={(e) => setEditForm({ ...editForm, commission_rate: parseInt(e.target.value) || 0 })}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">备注</label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setEditDialog(false)} className="px-4 py-2 text-gray-600">取消</button>
              <button onClick={handleEditIP} className="px-4 py-2 bg-primary text-white rounded">保存</button>
            </div>
          </div>
        </div>
      )}

      {/* Withdrawal Dialog */}
      {withdrawalDialog && selectedWithdrawal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-medium mb-4">处理提现申请</h3>
            <div className="text-sm text-gray-600 mb-4">
              <p>金额: {(selectedWithdrawal.amount / 100).toFixed(2)}元</p>
              <p>账户: {selectedWithdrawal.account_type} - {selectedWithdrawal.account_info}</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">处理结果</label>
                <select
                  value={withdrawalForm.status}
                  onChange={(e) => setWithdrawalForm({ ...withdrawalForm, status: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="approved">通过</option>
                  <option value="rejected">拒绝</option>
                  <option value="completed">已完成打款</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">备注</label>
                <textarea
                  value={withdrawalForm.admin_notes}
                  onChange={(e) => setWithdrawalForm({ ...withdrawalForm, admin_notes: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setWithdrawalDialog(false)} className="px-4 py-2 text-gray-600">取消</button>
              <button onClick={handleProcessWithdrawal} className="px-4 py-2 bg-primary text-white rounded">确认</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminIPManagement;
