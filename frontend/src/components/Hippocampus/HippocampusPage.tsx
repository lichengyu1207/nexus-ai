import React, { useState, useEffect, useCallback } from 'react';
import './HippocampusPage.css';

interface Memory {
  id: string;
  user_id: string;
  type: string;
  content: string;
  summary: string;
  importance: number;
  timestamp: string;
  source: string;
  agents: string[];
  entities: string[];
  context: Record<string, any>;
  access_count: number;
  last_access: string | null;
  created_at: string;
}

interface SearchResult {
  memory: Memory;
  score: number;
  match_type: string;
}

interface MemoryStats {
  total_memories: number;
  by_type: Record<string, number>;
  average_importance: number;
  health_score: number;
  type_distribution: Record<string, number>;
}

interface RelatedMemory {
  memory: Memory;
  relation_type: string;
  strength: number;
}

const MEMORY_TYPE_LABELS: Record<string, string> = {
  episodic: '情景记忆',
  semantic: '语义记忆',
  procedural: '程序性记忆',
};

const MEMORY_TYPE_COLORS: Record<string, string> = {
  episodic: '#3b82f6',
  semantic: '#10b981',
  procedural: '#f59e0b',
};

const HippocampusPage: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [relatedMemories, setRelatedMemories] = useState<RelatedMemory[]>([]);
  const [activeTab, setActiveTab] = useState<'timeline' | 'search' | 'stats'>('timeline');
  const [filterType, setFilterType] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newMemoryContent, setNewMemoryContent] = useState('');
  const [newMemoryType, setNewMemoryType] = useState('episodic');

  const fetchMemories = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      params.append('limit', '50');
      if (filterType) params.append('memory_type', filterType);

      const response = await fetch(`/api/hippocampus/memories?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setMemories(data);
      }
    } catch (error) {
      console.error('Failed to fetch memories:', error);
    }
  }, [filterType]);

  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/hippocampus/stats', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchMemories(), fetchStats()]);
      setLoading(false);
    };
    loadData();
  }, [fetchMemories, fetchStats]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/hippocampus/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: searchQuery,
          limit: 20,
          min_importance: 0.3,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
    setIsSearching(false);
  };

  const handleMemoryClick = async (memory: Memory) => {
    setSelectedMemory(memory);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/hippocampus/memories/${memory.id}/related`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setRelatedMemories(data);
      }
    } catch (error) {
      console.error('Failed to fetch related memories:', error);
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    if (!window.confirm('确定要删除这条记忆吗？')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/hippocampus/memories/${memoryId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setMemories(memories.filter((m) => m.id !== memoryId));
        if (selectedMemory?.id === memoryId) {
          setSelectedMemory(null);
        }
      }
    } catch (error) {
      console.error('Failed to delete memory:', error);
    }
  };

  const handleCreateMemory = async () => {
    if (!newMemoryContent.trim()) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/hippocampus/memories', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: newMemoryContent,
          memory_type: newMemoryType,
          source: 'manual',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMemories([data, ...memories]);
        setShowCreateModal(false);
        setNewMemoryContent('');
        fetchStats();
      }
    } catch (error) {
      console.error('Failed to create memory:', error);
    }
  };

  const handleConsolidate = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/hippocampus/consolidate', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        alert(`记忆整理完成！处理: ${data.result.memories_processed}, 合并: ${data.result.memories_merged}, 遗忘: ${data.result.memories_forgotten}`);
        fetchMemories();
        fetchStats();
      }
    } catch (error) {
      console.error('Consolidation failed:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getImportanceColor = (importance: number) => {
    if (importance >= 0.7) return '#ef4444';
    if (importance >= 0.5) return '#f59e0b';
    return '#10b981';
  };

  if (loading) {
    return (
      <div className="hippocampus-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>正在加载记忆中枢...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="hippocampus-page">
      <header className="hippocampus-header">
        <div className="header-content">
          <h1>🧠 海马体记忆中枢</h1>
          <p className="subtitle">存储、检索、联想您的数字记忆</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={handleConsolidate}>
            🔄 整理记忆
          </button>
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            ➕ 新建记忆
          </button>
        </div>
      </header>

      {stats && (
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-value">{stats.total_memories}</span>
            <span className="stat-label">总记忆数</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{(stats.average_importance * 100).toFixed(0)}%</span>
            <span className="stat-label">平均重要性</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{(stats.health_score * 100).toFixed(0)}%</span>
            <span className="stat-label">健康度</span>
          </div>
          {Object.entries(stats.by_type).map(([type, count]) => (
            <div key={type} className="stat-item">
              <span className="stat-value">{count}</span>
              <span className="stat-label">{MEMORY_TYPE_LABELS[type] || type}</span>
            </div>
          ))}
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'timeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          📅 时间线
        </button>
        <button
          className={`tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          🔍 搜索
        </button>
        <button
          className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          📊 统计
        </button>
      </div>

      <div className="main-content">
        {activeTab === 'timeline' && (
          <div className="timeline-view">
            <div className="filter-bar">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="filter-select"
              >
                <option value="">全部类型</option>
                <option value="episodic">情景记忆</option>
                <option value="semantic">语义记忆</option>
                <option value="procedural">程序性记忆</option>
              </select>
            </div>

            <div className="timeline">
              {memories.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-icon">🧠</span>
                  <p>暂无记忆数据</p>
                  <p className="empty-hint">点击"新建记忆"开始记录</p>
                </div>
              ) : (
                memories.map((memory) => (
                  <div
                    key={memory.id}
                    className={`memory-card ${selectedMemory?.id === memory.id ? 'selected' : ''}`}
                    onClick={() => handleMemoryClick(memory)}
                  >
                    <div className="memory-header">
                      <span
                        className="memory-type"
                        style={{
                          backgroundColor: MEMORY_TYPE_COLORS[memory.type] || '#6b7280',
                        }}
                      >
                        {MEMORY_TYPE_LABELS[memory.type] || memory.type}
                      </span>
                      <span
                        className="importance-badge"
                        style={{ color: getImportanceColor(memory.importance) }}
                      >
                        重要度: {(memory.importance * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="memory-content">
                      {memory.summary || memory.content.substring(0, 150)}
                    </div>
                    <div className="memory-footer">
                      <span className="memory-time">{formatDate(memory.timestamp)}</span>
                      <span className="memory-source">来源: {memory.source}</span>
                      <span className="memory-access">访问: {memory.access_count}次</span>
                    </div>
                    {memory.entities.length > 0 && (
                      <div className="memory-entities">
                        {memory.entities.slice(0, 5).map((entity, i) => (
                          <span key={i} className="entity-tag">
                            {entity}
                          </span>
                        ))}
                      </div>
                    )}
                    <button
                      className="delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteMemory(memory.id);
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'search' && (
          <div className="search-view">
            <div className="search-bar">
              <input
                type="text"
                placeholder="搜索记忆内容、实体、关键词..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button onClick={handleSearch} disabled={isSearching}>
                {isSearching ? '搜索中...' : '搜索'}
              </button>
            </div>

            <div className="search-results">
              {searchResults.length === 0 && searchQuery && !isSearching && (
                <div className="empty-state">
                  <span className="empty-icon">🔍</span>
                  <p>未找到相关记忆</p>
                </div>
              )}
              {searchResults.map((result, index) => (
                <div
                  key={result.memory.id}
                  className="search-result-card"
                  onClick={() => handleMemoryClick(result.memory)}
                >
                  <div className="result-header">
                    <span className="result-rank">#{index + 1}</span>
                    <span className="result-score">
                      相关度: {(result.score * 100).toFixed(0)}%
                    </span>
                    <span className="result-type">{result.match_type}</span>
                  </div>
                  <div className="result-content">
                    {result.memory.summary || result.memory.content.substring(0, 200)}
                  </div>
                  <div className="result-meta">
                    <span>{formatDate(result.memory.timestamp)}</span>
                    <span>{MEMORY_TYPE_LABELS[result.memory.type]}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'stats' && stats && (
          <div className="stats-view">
            <div className="stats-grid">
              <div className="stats-card">
                <h3>记忆类型分布</h3>
                <div className="type-distribution">
                  {Object.entries(stats.by_type).map(([type, count]) => (
                    <div key={type} className="type-bar-container">
                      <div className="type-label">{MEMORY_TYPE_LABELS[type] || type}</div>
                      <div className="type-bar">
                        <div
                          className="type-bar-fill"
                          style={{
                            width: `${(count / stats.total_memories) * 100}%`,
                            backgroundColor: MEMORY_TYPE_COLORS[type] || '#6b7280',
                          }}
                        ></div>
                      </div>
                      <div className="type-count">{count}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="stats-card">
                <h3>记忆健康度</h3>
                <div className="health-gauge">
                  <div className="gauge-value">
                    {(stats.health_score * 100).toFixed(0)}%
                  </div>
                  <div className="gauge-bar">
                    <div
                      className="gauge-fill"
                      style={{ width: `${stats.health_score * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div className="health-metrics">
                  <div className="metric">
                    <span className="metric-label">平均重要性</span>
                    <span className="metric-value">
                      {(stats.average_importance * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedMemory && (
          <div className="memory-detail-panel">
            <div className="panel-header">
              <h3>记忆详情</h3>
              <button className="close-btn" onClick={() => setSelectedMemory(null)}>
                ✕
              </button>
            </div>
            <div className="panel-content">
              <div className="detail-section">
                <label>类型</label>
                <span
                  className="type-badge"
                  style={{
                    backgroundColor: MEMORY_TYPE_COLORS[selectedMemory.type] || '#6b7280',
                  }}
                >
                  {MEMORY_TYPE_LABELS[selectedMemory.type]}
                </span>
              </div>
              <div className="detail-section">
                <label>内容</label>
                <p className="content-text">{selectedMemory.content}</p>
              </div>
              {selectedMemory.summary && (
                <div className="detail-section">
                  <label>摘要</label>
                  <p>{selectedMemory.summary}</p>
                </div>
              )}
              <div className="detail-section">
                <label>实体</label>
                <div className="entity-list">
                  {selectedMemory.entities.map((entity, i) => (
                    <span key={i} className="entity-tag">
                      {entity}
                    </span>
                  ))}
                </div>
              </div>
              <div className="detail-section">
                <label>元信息</label>
                <div className="meta-info">
                  <div>创建时间: {formatDate(selectedMemory.created_at)}</div>
                  <div>来源: {selectedMemory.source}</div>
                  <div>访问次数: {selectedMemory.access_count}</div>
                  <div>重要性: {(selectedMemory.importance * 100).toFixed(0)}%</div>
                </div>
              </div>
              {relatedMemories.length > 0 && (
                <div className="detail-section">
                  <label>相关记忆</label>
                  <div className="related-memories">
                    {relatedMemories.map((rel) => (
                      <div
                        key={rel.memory.id}
                        className="related-item"
                        onClick={() => handleMemoryClick(rel.memory)}
                      >
                        <span className="relation-type">{rel.relation_type}</span>
                        <span className="relation-strength">
                          {(rel.strength * 100).toFixed(0)}%
                        </span>
                        <p className="related-summary">
                          {rel.memory.summary || rel.memory.content.substring(0, 50)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>新建记忆</h3>
            <div className="form-group">
              <label>记忆类型</label>
              <select
                value={newMemoryType}
                onChange={(e) => setNewMemoryType(e.target.value)}
              >
                <option value="episodic">情景记忆</option>
                <option value="semantic">语义记忆</option>
                <option value="procedural">程序性记忆</option>
              </select>
            </div>
            <div className="form-group">
              <label>记忆内容</label>
              <textarea
                value={newMemoryContent}
                onChange={(e) => setNewMemoryContent(e.target.value)}
                placeholder="输入记忆内容..."
                rows={5}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                取消
              </button>
              <button className="btn-primary" onClick={handleCreateMemory}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HippocampusPage;
