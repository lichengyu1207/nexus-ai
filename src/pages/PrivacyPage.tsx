import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

interface PrivacyPolicy {
  id: string;
  version: string;
  title: string;
  content: string;
  effective_date: string;
  created_at?: string;
}

interface VersionSummary {
  id: string;
  version: string;
  title: string;
  effective_date: string;
  is_current: number;
}

export default function PrivacyPage() {
  const { version: urlVersion } = useParams<{ version?: string }>();
  const [policy, setPolicy] = useState<PrivacyPolicy | null>(null);
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVersions();
  }, []);

  useEffect(() => {
    if (versions.length > 0) {
      const versionToFetch = urlVersion || selectedVersion || 'current';
      fetchPolicy(versionToFetch);
    }
  }, [urlVersion, versions, selectedVersion]);

  const fetchVersions = async () => {
    try {
      const response = await api.get('/api/privacy/versions');
      setVersions(response.data);
      if (response.data.length > 0 && !selectedVersion) {
        const currentVersion = response.data.find((v: VersionSummary) => v.is_current === 1);
        if (currentVersion) {
          setSelectedVersion(currentVersion.version);
        }
      }
    } catch (err) {
      console.error('Failed to fetch versions:', err);
    }
  };

  const fetchPolicy = async (version: string) => {
    setLoading(true);
    setError(null);
    try {
      let response;
      if (version === 'current' || !version) {
        response = await api.get('/api/privacy/current');
      } else {
        response = await api.get(`/api/privacy/versions/${version}`);
      }
      setPolicy(response.data);
      setSelectedVersion(response.data.version);
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载隐私政策失败');
    } finally {
      setLoading(false);
    }
  };

  const handleVersionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedVersion(e.target.value);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-sm p-8">
          <div className="flex items-center justify-between mb-6 pb-4 border-b">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{policy?.title}</h1>
              <p className="text-sm text-gray-500 mt-1">
                版本 {policy?.version} · 生效日期 {policy?.effective_date}
              </p>
            </div>
            
            {versions.length > 1 && (
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">历史版本:</label>
                <select
                  value={selectedVersion}
                  onChange={handleVersionChange}
                  className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.version}>
                      {v.version} ({v.effective_date})
                      {v.is_current === 1 ? ' - 当前版本' : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <h1 className="text-2xl font-bold text-gray-900 mb-4 mt-6">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-xl font-semibold text-gray-800 mb-3 mt-5">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-lg font-medium text-gray-800 mb-2 mt-4">{children}</h3>
                ),
                p: ({ children }) => (
                  <p className="text-gray-600 mb-3 leading-relaxed">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside text-gray-600 mb-3 space-y-1">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside text-gray-600 mb-3 space-y-1">{children}</ol>
                ),
                li: ({ children }) => (
                  <li className="text-gray-600">{children}</li>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-gray-800">{children}</strong>
                ),
                a: ({ href, children }) => (
                  <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {policy?.content || ''}
            </ReactMarkdown>
          </div>

          <div className="mt-8 pt-4 border-t text-center text-sm text-gray-500">
            <p>
              如有疑问，请联系我们：
              <a href="mailto:privacy@example.com" className="text-blue-600 hover:underline ml-1">
                privacy@example.com
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
