import React, { useState, useEffect } from 'react';
import {
  Shield, AlertTriangle, CheckCircle, XCircle, RefreshCw,
  FileCode, Package, Server, Lock, Eye,
} from 'lucide-react';
import api from '@/services/api';

interface ScanResult {
  scan_type: string;
  status: string;
  findings: Array<{
    type: string;
    package?: string;
    severity?: string;
    message?: string;
    file?: string;
    line?: number;
  }>;
  scanned_at: string;
  total_packages?: number;
}

interface SecurityHeader {
  value: string;
  description: string;
  implemented: boolean;
  note?: string;
}

interface ChecklistCategory {
  category: string;
  items: Array<{
    item: string;
    status: boolean;
    note?: string;
  }>;
}

const MonitorPage: React.FC = () => {
  const [pythonScan, setPythonScan] = useState<ScanResult | null>(null);
  const [codeScan, setCodeScan] = useState<ScanResult | null>(null);
  const [frontendScan, setFrontendScan] = useState<ScanResult | null>(null);
  const [headers, setHeaders] = useState<Record<string, SecurityHeader> | null>(null);
  const [checklist, setChecklist] = useState<ChecklistCategory[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'scan' | 'headers' | 'checklist'>('overview');

  useEffect(() => {
    fetchSecurityData();
  }, []);

  const fetchSecurityData = async () => {
    setLoading(true);
    try {
      const [headersRes, checklistRes] = await Promise.all([
        api.get('/admin/security/headers'),
        api.get('/admin/security/checklist'),
      ]);

      setHeaders(headersRes.data?.recommended_headers || []);
      setChecklist(checklistRes.data?.checklist || []);
    } catch (error) {
      console.error('Failed to fetch security data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runScan = async (type: 'python' | 'code' | 'frontend') => {
    setLoading(true);
    try {
      const response = await api.get(`/admin/security/scan/${type}`);
      
      if (type === 'python') setPythonScan(response.data);
      else if (type === 'code') setCodeScan(response.data);
      else if (type === 'frontend') setFrontendScan(response.data);
    } catch (error) {
      console.error(`Failed to run ${type} scan:`, error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Shield className="w-7 h-7 text-blue-600" />
          安全中心
        </h1>
        <button
          onClick={fetchSecurityData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      <div className="flex gap-4 border-b">
        {[
          { key: 'overview', label: '概览' },
          { key: 'scan', label: '安全扫描' },
          { key: 'headers', label: '安全头' },
          { key: 'checklist', label: '检查清单' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 font-medium ${
              activeTab === tab.key
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-gray-500">Python依赖</span>
            </div>
            <p className="text-2xl font-bold mt-1">
              {pythonScan?.total_packages || '-'}
            </p>
            <p className="text-sm text-gray-500">已安装包</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <FileCode className="w-5 h-5 text-green-600" />
              <span className="text-sm text-gray-500">代码问题</span>
            </div>
            <p className="text-2xl font-bold mt-1">
              {codeScan?.findings?.length || '-'}
            </p>
            <p className="text-sm text-gray-500">发现的问题</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <span className="text-sm text-gray-500">漏洞数量</span>
            </div>
            <p className="text-2xl font-bold mt-1">
              {(pythonScan?.findings?.filter(f => f.type === 'vulnerability').length || 0) +
               (frontendScan?.findings?.filter(f => f.type === 'vulnerability').length || 0)}
            </p>
            <p className="text-sm text-gray-500">已知漏洞</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-purple-600" />
              <span className="text-sm text-gray-500">安全头</span>
            </div>
            <p className="text-2xl font-bold mt-1">
              {headers ? Object.values(headers).filter(h => h.implemented).length : '-'}/
              {headers ? Object.keys(headers).length : '-'}
            </p>
            <p className="text-sm text-gray-500">已配置</p>
          </div>
        </div>
      )}

      {activeTab === 'scan' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => runScan('python')}
              disabled={loading}
              className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left"
            >
              <Package className="w-8 h-8 text-blue-600 mb-2" />
              <h3 className="font-semibold">Python依赖扫描</h3>
              <p className="text-sm text-gray-500">检查Python包的已知漏洞</p>
            </button>
            
            <button
              onClick={() => runScan('code')}
              disabled={loading}
              className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left"
            >
              <FileCode className="w-8 h-8 text-green-600 mb-2" />
              <h3 className="font-semibold">代码安全扫描</h3>
              <p className="text-sm text-gray-500">使用Bandit扫描代码安全问题</p>
            </button>
            
            <button
              onClick={() => runScan('frontend')}
              disabled={loading}
              className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left"
            >
              <Server className="w-8 h-8 text-purple-600 mb-2" />
              <h3 className="font-semibold">前端依赖扫描</h3>
              <p className="text-sm text-gray-500">检查npm包的已知漏洞</p>
            </button>
          </div>

          {[pythonScan, codeScan, frontendScan].map((scan, index) => (
            scan && (
              <div key={index} className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                  <h3 className="font-semibold">{scan.scan_type}</h3>
                  <p className="text-sm text-gray-500">
                    扫描时间: {new Date(scan.scanned_at).toLocaleString()}
                  </p>
                </div>
                <div className="divide-y max-h-64 overflow-y-auto">
                  {scan.findings.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      <CheckCircle className="w-8 h-8 mx-auto text-green-500 mb-2" />
                      未发现问题
                    </div>
                  ) : (
                    scan.findings.map((finding, i) => (
                      <div key={i} className="p-4">
                        <div className="flex items-center gap-2">
                          {finding.severity && (
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(finding.severity)}`}>
                              {finding.severity}
                            </span>
                          )}
                          <span className="font-medium">{finding.package || finding.file || finding.type}</span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{finding.message}</p>
                        {finding.line && (
                          <p className="text-xs text-gray-400 mt-1">Line: {finding.line}</p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )
          ))}
        </div>
      )}

      {activeTab === 'headers' && headers && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h3 className="font-semibold">HTTP安全头配置</h3>
          </div>
          <div className="divide-y">
            {Object.entries(headers).map(([name, info]) => (
              <div key={name} className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium">{name}</p>
                  <p className="text-sm text-gray-500">{info.description}</p>
                  {info.note && (
                    <p className="text-xs text-yellow-600 mt-1">{info.note}</p>
                  )}
                </div>
                {info.implemented ? (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-500" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'checklist' && checklist && (
        <div className="space-y-4">
          {checklist.map((category, index) => (
            <div key={index} className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h3 className="font-semibold">{category.category}</h3>
              </div>
              <div className="divide-y">
                {category.items.map((item, i) => (
                  <div key={i} className="p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium">{item.item}</p>
                      {item.note && (
                        <p className="text-xs text-yellow-600 mt-1">{item.note}</p>
                      )}
                    </div>
                    {item.status ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MonitorPage;
