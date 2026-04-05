import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface CompareResult {
  id: string;
  address1: string;
  address2: string;
  status: string;
  created_at: string;
  report_summary?: string;
  price_estimate?: number;
  confidence?: number;
}

const ComparePage: React.FC = () => {
  const navigate = useNavigate();
  const [address1, setAddress1] = useState('');
  const [address2, setAddress2] = useState('');
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [results, setResults] = useState<CompareResult[]>([]);

  const handleCompare = async () => {
    if (!address1.trim() || !address2.trim()) {
      alert('请输入两个房产地址');
      return;
    }

    setComparing(true);
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/compare', {
        method: 'POST',
        headers: {
        'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ address1, address2 }),
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      } else {
        const error = await response.json();
        alert(error.detail || '对比分析失败');
      }
    } catch (error) {
      console.error('Failed to compare:', error);
      alert('对比分析失败');
    } finally {
      setLoading(false);
      setComparing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">房源对比分析</h1>
        <button
          onClick={() => navigate('/dashboard')}
          className="text-gray-500 hover:text-gray-700"
        >
          返回
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              房产地址 1
            </label>
            <input
              type="text"
              value={address1}
              onChange={(e) => setAddress1(e.target.value)}
              className="w-full border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="请输入第一个房产地址"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              房产地址 2
            </label>
            <input
              type="text"
              value={address2}
              onChange={(e) => setAddress2(e.target.value)}
              className="w-full border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="请输入第二个房产地址"
            />
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={comparing || !address1.trim() || !address2.trim()}
          className="w-full bg-primary text-white py-3 rounded-lg hover:bg-primaryDark disabled:opacity-50"
        >
          {comparing ? '对比中...' : '开始对比分析'}
        </button>

        <div className="mt-4 text-sm text-gray-500">
          <p>对比分析将消耗 2 积分</p>
        </div>
      </div>

      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">对比结果</h2>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={result.id || index} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-medium">{result.address}</h3>
                  <Link
                    to={`/virtual-office/${result.id}`}
                    className="text-primary hover:text-primaryDark text-sm"
                  >
                    查看详情
                  </Link>
                </div>
                {result.report_summary && (
                  <p className="text-sm text-gray-600 mt-2">{result.report_summary}</p>
                )}
                <div className="grid grid-cols-2 gap-4 mt-3">
                  {result.price_estimate && (
                    <div>
                      <span className="text-gray-500 text-sm">估值:</span>
                      <span className="font-medium">{result.price_estimate} 万</span>
                    </div>
                  )}
                  {result.confidence && (
                    <div>
                      <span className="text-gray-500 text-sm">置信度:</span>
                      <span className="font-medium">{result.confidence}%</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ComparePage;
