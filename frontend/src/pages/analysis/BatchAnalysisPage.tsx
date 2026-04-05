import React, { useState } from 'react';
import { Link } from 'react-router-dom';

interface BatchResult {
  address: string;
  status: string;
  task_id?: string;
}

const BatchAnalysisPage: React.FC = () => {
  const [addresses, setAddresses] = useState<string[]>([]);
  const [results, setResults] = useState<BatchResult[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const handleRemoveAddress = (index: number) => {
    setAddresses(addresses.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/tasks/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ addresses }),
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      } else {
        alert('批量分析失败');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">批量分析</h1>
        <p className="text-gray-500 mb-4">输入多个房产地址，一次性进行分析</p>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            输入房产地址（每行一个）
          </label>
          <textarea
            value={addresses.join('\n')}
            onChange={(e) => setAddresses(e.target.value.split('\n').filter((a: string) => a.trim()))}
            className="w-full border rounded-lg px-4 py-3 h-40 focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="请输入房产地址，每行一个地址..."
          />
        </div>

        <div className="mb-4">
          <button
            onClick={() => setAddresses([''])}
            className="text-sm text-primary hover:text-primaryDark"
          >
            清空
          </button>
        </div>

        {addresses.length > 0 && (
          <div className="mb-4">
            <div className="text-sm text-gray-500 mb-2">已输入 {addresses.length} 个地址</div>
            <div className="max-h-60 overflow-y-auto border rounded-lg">
              {addresses.map((address, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm truncate flex-1">{address}</span>
                  <button
                    onClick={() => handleRemoveAddress(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    删除
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={submitting || addresses.length === 0}
          className="w-full bg-primary text-white py-3 rounded-lg hover:bg-primaryDark disabled:opacity-50"
        >
          {submitting ? '提交中...' : '开始批量分析'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-medium mb-4">分析结果</h2>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium truncate flex-1">{result.address}</span>
                  <span className={`px-2 py-1 rounded-full text-sm ${
                    result.status === 'completed' ? 'bg-green-100 text-green-700' :
                    result.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                    result.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {result.status}
                  </span>
                </div>
                {result.task_id && (
                  <Link
                    to={`/virtual-office/${result.task_id}`}
                    className="text-primary hover:text-primaryDark text-sm"
                  >
                    查看详情
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchAnalysisPage;
