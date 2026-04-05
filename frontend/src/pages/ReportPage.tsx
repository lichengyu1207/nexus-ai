import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, TabList, Tab, TabPanel, TabPanels } from '../components/ui/Tabs';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui';
import { DataSourceTooltip } from '../components/ui/Tooltip';
import FeedbackButton from '../components/common/FeedbackButton';

interface ReportData {
  task_id: string;
  query: string;
  report: {
    property_reports?: any[];
    summary_report?: {
      summary?: string;
      total_properties?: number;
      average_price?: number;
      price_range?: [number, number];
      investment_score?: number;
      risk_level?: string;
    };
    report_stats?: {
      total_properties: number;
      generated_reports: number;
      failed_reports: number;
    };
    core_findings?: {
      strengths: string[];
      weaknesses: string[];
      opportunities: string[];
      threats: string[];
    };
    detailed_analysis?: {
      location: {
        score: number;
        description: string;
        nearby_facilities: string[];
      };
      price_analysis: {
        current_price: number;
        market_average: number;
        price_trend: string;
        price_per_sqm: number;
      };
      rental_yield: {
        estimated_rent: number;
        yield_rate: number;
        occupancy_rate: number;
      };
    };
    investment_advice?: {
      recommendation: string;
      target_price: number;
      expected_appreciation: number;
      holding_period: string;
    };
    risks?: {
      level: string;
      items: string[];
      mitigation: string[];
    };
  };
  created_at: string;
  status: string;
  confidence?: number;
  data_sources?: string[];
}

const ReportPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    if (!taskId) return;
    fetchReport();
  }, [taskId]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        const data = await response.json();
        setReport(data);
      } else {
        setError('报告未找到');
      }
    } catch (err) {
      setError('加载报告失败');
      console.error('Error fetching report:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!report) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/reports/${taskId}/pdf`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `房产分析报告_${taskId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('PDF download failed:', err);
    }
  };

  const handleCopyReport = () => {
    if (!report) return;
    
    const text = generateTextReport(report);
    navigator.clipboard.writeText(text);
  };

  const generateTextReport = (reportData: ReportData): string => {
    return `
房产分析报告
报告编号: ${taskId}
生成时间: ${reportData.created_at}
查询内容: ${reportData.query}

摘要:
${reportData.report?.summary_report?.summary || '暂无摘要'}

分析状态: ${reportData.status}
置信度: ${((reportData.confidence || 0.85) * 100).toFixed(0)}%
    `.trim();
  };

  const handleDownloadHTML = () => {
    if (!report) return;
    
    const htmlContent = generateHTMLReport(report);
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `房产分析报告-${taskId}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadMD = async () => {
    if (!taskId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/reports/${taskId}/download?format=md`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `房产分析报告_${taskId}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('MD download failed:', err);
    }
  };

  const handleDownloadZIP = async () => {
    if (!taskId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/reports/${taskId}/download?format=zip`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `房产分析报告_${taskId}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('ZIP download failed:', err);
    }
  };

  const generateHTMLReport = (reportData: ReportData): string => {
    const reportInfo = reportData.report || {};
    const summaryReport = reportInfo.summary_report || {};
    const propertyReports = reportInfo.property_reports || [];
    const reportStats = reportInfo.report_stats || {};

    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>房产分析报告 - ${taskId}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 0 20px rgba(0,0,0,0.1); border-radius: 10px; }
        .header { text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 3px solid #667eea; }
        .header h1 { font-size: 32px; color: #333; margin-bottom: 10px; }
        .meta { color: #666; font-size: 14px; }
        .section { margin-bottom: 30px; }
        .section h2 { font-size: 24px; color: #333; margin-bottom: 15px; padding-left: 15px; border-left: 4px solid #667eea; }
        .info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }
        .info-item { background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .info-item .label { font-weight: bold; color: #666; margin-bottom: 5px; }
        .info-item .value { font-size: 18px; color: #333; }
        .highlight-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .disclaimer { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin-top: 30px; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 房产分析报告</h1>
            <div class="meta">
                <p>报告编号：${taskId}</p>
                <p>生成时间：${reportData.created_at || new Date().toLocaleString()}</p>
                <p>查询内容：${reportData.query || '未指定'}</p>
            </div>
        </div>
        <div class="section">
            <h2>📊 分析摘要</h2>
            <div class="highlight-box">
                <h3>分析结果</h3>
                <p>${summaryReport.summary || '分析已完成'}</p>
            </div>
            <div class="info-grid">
                <div class="info-item"><div class="label">分析状态</div><div class="value">${reportData.status === 'SUCCESS' ? '✅ 成功' : reportData.status}</div></div>
                <div class="info-item"><div class="label">生成报告数</div><div class="value">${reportStats.generated_reports || 0}</div></div>
                ${summaryReport.average_price ? `<div class="info-item"><div class="label">平均价格</div><div class="value">${summaryReport.average_price.toLocaleString()} 元/㎡</div></div>` : ''}
            </div>
        </div>
        <div class="disclaimer">
            <h3>⚠️ 免责声明</h3>
            <p>本报告仅基于公开数据模拟生成，仅供参考，不可用于正式抵押、交易、诉讼等法律用途。</p>
        </div>
    </div>
</body>
</html>
    `;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
          <p className="mt-4 text-gray-600">正在加载报告...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">❌ {error}</h2>
          <Button onClick={() => navigate('/dashboard')}>返回仪表盘</Button>
        </div>
      </div>
    );
  }

  const summaryReport = report?.report?.summary_report || {};
  const coreFindings = report?.report?.core_findings || { strengths: [], weaknesses: [], opportunities: [], threats: [] };
  const detailedAnalysis = report?.report?.detailed_analysis;
  const investmentAdvice = report?.report?.investment_advice;
  const risks = report?.report?.risks;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📄 房产分析报告</h1>
              <p className="text-gray-500 mt-1">报告编号: {taskId}</p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => navigate('/dashboard')}>
                返回
              </Button>
              <Button variant="outline" onClick={handleCopyReport}>
                📋 复制
              </Button>
              <Button variant="outline" onClick={handleDownloadMD}>
                📝 MD
              </Button>
              <Button variant="outline" onClick={handleDownloadZIP}>
                📦 全套
              </Button>
              <Button onClick={handleDownloadHTML}>
                📥 下载
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-500">查询内容</p>
              <p className="font-medium truncate">{report?.query || '未指定'}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-500">生成时间</p>
              <p className="font-medium">{report?.created_at ? new Date(report.created_at).toLocaleDateString('zh-CN') : '-'}</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-500">分析状态</p>
              <StatusBadge status={report?.status === 'SUCCESS' ? 'completed' : 'processing'} />
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-500">置信度</p>
              <p className="font-medium text-green-600">
                {((report?.confidence || 0.85) * 100).toFixed(0)}%
                <DataSourceTooltip
                  source="多数据源交叉验证"
                  confidence={report?.confidence || 0.85}
                />
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onChange={setActiveTab}>
          <TabList className="bg-white rounded-t-lg border-b">
            <Tab value="summary">📊 执行摘要</Tab>
            <Tab value="findings">🔍 核心发现</Tab>
            <Tab value="analysis">📈 详细分析</Tab>
            <Tab value="investment">💰 投资建议</Tab>
            <Tab value="risks">⚠️ 风险提示</Tab>
          </TabList>

          <TabPanels>
            {/* Summary Tab */}
            <TabPanel value="summary" className="bg-white rounded-b-lg p-6">
              <div className="bg-gradient-to-r from-primary to-purple-600 text-white p-6 rounded-lg mb-6">
                <h3 className="text-xl font-bold mb-2">分析摘要</h3>
                <p className="text-white/90">
                  {summaryReport.summary || '分析已完成，详细信息请查看各分项报告。'}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <p className="text-3xl font-bold text-blue-600">
                    {summaryReport.total_properties || 0}
                  </p>
                  <p className="text-sm text-gray-600">分析房产数</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <p className="text-3xl font-bold text-green-600">
                    {summaryReport.average_price?.toLocaleString() || '-'}
                  </p>
                  <p className="text-sm text-gray-600">平均价格 (元/㎡)</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <p className="text-3xl font-bold text-purple-600">
                    {summaryReport.investment_score || '-'}/10
                  </p>
                  <p className="text-sm text-gray-600">投资评分</p>
                </div>
              </div>

              {summaryReport.price_range && (
                <div className="mt-6">
                  <h4 className="font-medium mb-3">价格区间</h4>
                  <div className="relative h-4 bg-gray-200 rounded-full">
                    <div
                      className="absolute h-full bg-primary rounded-full"
                      style={{
                        left: `${(summaryReport.price_range[0] / 100000) * 100}%`,
                        right: `${100 - (summaryReport.price_range[1] / 100000) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-sm text-gray-500 mt-1">
                    <span>¥{summaryReport.price_range[0]?.toLocaleString()}</span>
                    <span>¥{summaryReport.price_range[1]?.toLocaleString()}</span>
                  </div>
                </div>
              )}
            </TabPanel>

            {/* Findings Tab */}
            <TabPanel value="findings" className="bg-white rounded-b-lg p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="font-medium text-green-700 mb-3 flex items-center gap-2">
                    <span className="text-xl">💪</span> 优势
                  </h4>
                  <ul className="space-y-2">
                    {coreFindings.strengths.length > 0 ? (
                      coreFindings.strengths.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-green-500 mt-0.5">✓</span>
                          {item}
                        </li>
                      ))
                    ) : (
                      <li className="text-sm text-gray-500">暂无数据</li>
                    )}
                  </ul>
                </div>

                <div className="bg-red-50 rounded-lg p-4">
                  <h4 className="font-medium text-red-700 mb-3 flex items-center gap-2">
                    <span className="text-xl">⚠️</span> 劣势
                  </h4>
                  <ul className="space-y-2">
                    {coreFindings.weaknesses.length > 0 ? (
                      coreFindings.weaknesses.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-red-500 mt-0.5">✗</span>
                          {item}
                        </li>
                      ))
                    ) : (
                      <li className="text-sm text-gray-500">暂无数据</li>
                    )}
                  </ul>
                </div>

                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-700 mb-3 flex items-center gap-2">
                    <span className="text-xl">🎯</span> 机会
                  </h4>
                  <ul className="space-y-2">
                    {coreFindings.opportunities.length > 0 ? (
                      coreFindings.opportunities.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-blue-500 mt-0.5">→</span>
                          {item}
                        </li>
                      ))
                    ) : (
                      <li className="text-sm text-gray-500">暂无数据</li>
                    )}
                  </ul>
                </div>

                <div className="bg-yellow-50 rounded-lg p-4">
                  <h4 className="font-medium text-yellow-700 mb-3 flex items-center gap-2">
                    <span className="text-xl">⚡</span> 威胁
                  </h4>
                  <ul className="space-y-2">
                    {coreFindings.threats.length > 0 ? (
                      coreFindings.threats.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-yellow-500 mt-0.5">!</span>
                          {item}
                        </li>
                      ))
                    ) : (
                      <li className="text-sm text-gray-500">暂无数据</li>
                    )}
                  </ul>
                </div>
              </div>
            </TabPanel>

            {/* Analysis Tab */}
            <TabPanel value="analysis" className="bg-white rounded-b-lg p-6">
              {detailedAnalysis ? (
                <div className="space-y-6">
                  {/* Location Analysis */}
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-4 flex items-center gap-2">
                      <span className="text-xl">📍</span> 地段分析
                    </h4>
                    <div className="flex items-center gap-4 mb-4">
                      <div className="flex-1">
                        <div className="h-2 bg-gray-200 rounded-full">
                          <div
                            className="h-full bg-primary rounded-full"
                            style={{ width: `${(detailedAnalysis.location.score || 0) * 10}%` }}
                          />
                        </div>
                      </div>
                      <span className="font-bold text-primary">
                        {detailedAnalysis.location.score || 0}/10
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm mb-3">
                      {detailedAnalysis.location.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {detailedAnalysis.location.nearby_facilities?.map((facility, i) => (
                        <Badge key={i} variant="info" size="sm">{facility}</Badge>
                      ))}
                    </div>
                  </div>

                  {/* Price Analysis */}
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-4 flex items-center gap-2">
                      <span className="text-xl">💵</span> 价格分析
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">当前价格</p>
                        <p className="text-lg font-bold">
                          ¥{detailedAnalysis.price_analysis?.current_price?.toLocaleString() || '-'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">市场均价</p>
                        <p className="text-lg font-bold">
                          ¥{detailedAnalysis.price_analysis?.market_average?.toLocaleString() || '-'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">单价</p>
                        <p className="text-lg font-bold">
                          ¥{detailedAnalysis.price_analysis?.price_per_sqm?.toLocaleString() || '-'}/㎡
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">价格趋势</p>
                        <Badge variant={detailedAnalysis.price_analysis?.price_trend === '上涨' ? 'success' : 'warning'}>
                          {detailedAnalysis.price_analysis?.price_trend || '稳定'}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {/* Rental Yield */}
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-4 flex items-center gap-2">
                      <span className="text-xl">🏠</span> 租金收益
                    </h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                          {detailedAnalysis.rental_yield?.yield_rate?.toFixed(1) || '-'}%
                        </p>
                        <p className="text-sm text-gray-500">年化收益率</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">
                          ¥{detailedAnalysis.rental_yield?.estimated_rent?.toLocaleString() || '-'}
                        </p>
                        <p className="text-sm text-gray-500">预估月租</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">
                          {detailedAnalysis.rental_yield?.occupancy_rate?.toFixed(0) || '-'}%
                        </p>
                        <p className="text-sm text-gray-500">出租率</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>暂无详细分析数据</p>
                </div>
              )}
            </TabPanel>

            {/* Investment Tab */}
            <TabPanel value="investment" className="bg-white rounded-b-lg p-6">
              {investmentAdvice ? (
                <div className="space-y-6">
                  <div className={`p-6 rounded-lg ${
                    investmentAdvice.recommendation === '强烈推荐' ? 'bg-green-50' :
                    investmentAdvice.recommendation === '推荐' ? 'bg-blue-50' :
                    investmentAdvice.recommendation === '谨慎' ? 'bg-yellow-50' :
                    'bg-red-50'
                  }`}>
                    <h4 className="text-xl font-bold mb-2">{investmentAdvice.recommendation}</h4>
                    <p className="text-gray-600">
                      基于多维度分析，我们对该房产的投资价值评估如下：
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="border rounded-lg p-4 text-center">
                      <p className="text-sm text-gray-500">建议入手价</p>
                      <p className="text-2xl font-bold text-primary">
                        ¥{investmentAdvice.target_price?.toLocaleString() || '-'}
                      </p>
                    </div>
                    <div className="border rounded-lg p-4 text-center">
                      <p className="text-sm text-gray-500">预期增值</p>
                      <p className="text-2xl font-bold text-green-600">
                        +{investmentAdvice.expected_appreciation?.toFixed(1) || '-'}%
                      </p>
                    </div>
                    <div className="border rounded-lg p-4 text-center">
                      <p className="text-sm text-gray-500">建议持有期</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {investmentAdvice.holding_period || '-'}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>暂无投资建议</p>
                </div>
              )}
            </TabPanel>

            {/* Risks Tab */}
            <TabPanel value="risks" className="bg-white rounded-b-lg p-6">
              {risks ? (
                <div className="space-y-6">
                  <div className={`p-4 rounded-lg ${
                    risks.level === '低' ? 'bg-green-50' :
                    risks.level === '中' ? 'bg-yellow-50' :
                    'bg-red-50'
                  }`}>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {risks.level === '低' ? '✅' : risks.level === '中' ? '⚠️' : '🚨'}
                      </span>
                      <div>
                        <h4 className="font-medium">风险等级: {risks.level}</h4>
                        <p className="text-sm text-gray-600">
                          {risks.level === '低' ? '该房产投资风险较低，适合稳健型投资者' :
                           risks.level === '中' ? '该房产存在一定风险，建议谨慎评估' :
                           '该房产风险较高，建议充分了解后再做决策'}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-3">主要风险点</h4>
                    <ul className="space-y-2">
                      {risks.items?.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
                          <span className="text-yellow-500">⚠️</span>
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-medium mb-3">风险缓解建议</h4>
                    <ul className="space-y-2">
                      {risks.mitigation?.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
                          <span className="text-blue-500">💡</span>
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>暂无风险提示</p>
                </div>
              )}

              {/* Disclaimer */}
              <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                <h4 className="font-medium text-yellow-800 mb-2">⚠️ 免责声明</h4>
                <p className="text-sm text-yellow-700">
                  本报告仅基于公开数据生成，仅供参考，不可用于正式抵押、交易、诉讼等法律用途。
                  实际房产价值受多种因素影响，请以专业评估机构出具的正式报告为准。
                </p>
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>

        {/* Feedback */}
        <div className="mt-6 bg-white rounded-lg shadow p-4">
          <FeedbackButton taskId={taskId || ''} />
        </div>
      </div>
    </div>
  );
};

export default ReportPage;
