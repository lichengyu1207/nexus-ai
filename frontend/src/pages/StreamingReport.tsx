import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui';
import { StatusBadge } from '../components/ui/Badge';

interface ReportMessage {
  type: string;
  content?: string;
  chartType?: string;
  title?: string;
  xAxis?: string;
  yAxis?: string;
  yRange?: [number, number];
  legend?: string[];
  partial?: boolean;
  data?: any;
  index?: number;
  timestamp?: number;
  style?: string;
  step?: string;
  confidence?: string;
}

const StreamingReport: React.FC = () => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<ReportMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('深圳南山区房价');
  const navigate = useNavigate();
  const chartRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  useEffect(() => {
    // 建立WebSocket连接
    const ws = new WebSocket('ws://localhost:8000/api/consult/ws/report');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as ReportMessage;
        setMessages(prev => [...prev, message]);
        
        // 处理图表数据
        if (message.type === 'chart' && message.data) {
          handleChartData(message);
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket连接失败');
    };
    
    setSocket(ws);
    
    return () => {
      ws.close();
    };
  }, []);

  const handleChartData = (message: ReportMessage) => {
    // 这里可以实现图表的逐步绘制逻辑
    // 暂时只打印数据，实际项目中可以使用Chart.js等库来绘制
    console.log('Chart data:', message);
  };

  const startReportGeneration = () => {
    if (!socket || !isConnected) {
      setError('WebSocket未连接');
      return;
    }
    
    setMessages([]);
    setError(null);
    setIsGenerating(true);
    
    const reportRequest = {
      report_request: {
        query: query,
        report_type: '房产分析',
        data_sources: ['房价数据', '政策信息', '周边配套'],
        models: ['估值模型', '趋势预测模型']
      }
    };
    
    socket.send(JSON.stringify(reportRequest));
  };

  const sendControlCommand = (command: string) => {
    if (!socket || !isConnected) {
      setError('WebSocket未连接');
      return;
    }
    
    socket.send(JSON.stringify({ command }));
  };

  const renderMessage = (message: ReportMessage, index: number) => {
    switch (message.type) {
      case 'text':
        return (
          <div key={index} className={`p-4 mb-2 rounded-lg ${message.style === 'title' ? 'bg-primary text-white' : message.style === 'summary' ? 'bg-blue-50' : message.style === 'conclusion' ? 'bg-green-50' : 'bg-gray-50'}`}>
            <p>{message.content}</p>
          </div>
        );
      case 'status':
        return (
          <div key={index} className="p-2 mb-2 rounded-lg bg-yellow-50 flex items-center">
            <StatusBadge status={message.content === '完成' ? 'completed' : 'processing'} />
            <span className="ml-2 text-gray-600">{message.content}</span>
          </div>
        );
      case 'chart':
        return (
          <div key={index} className="p-4 mb-4 rounded-lg bg-white border">
            <h4 className="font-medium mb-2">{message.title}</h4>
            <div 
              ref={el => chartRefs.current[`chart-${index}`] = el}
              className="h-64 bg-gray-50 rounded"
            >
              {/* 图表将在这里渲染 */}
              <div className="flex items-center justify-center h-full text-gray-400">
                {message.partial ? '绘制中...' : '图表加载中...'}
              </div>
            </div>
          </div>
        );
      case 'reasoning':
        return (
          <div key={index} className="p-4 mb-2 rounded-lg bg-purple-50 border-l-4 border-purple-400">
            <h4 className="font-medium text-purple-700">{message.step}</h4>
            <p className="mt-1 text-gray-700">{message.content}</p>
            {message.confidence && <p className="mt-1 text-sm text-gray-500">{message.confidence}</p>}
          </div>
        );
      case 'error':
        return (
          <div key={index} className="p-4 mb-2 rounded-lg bg-red-50 text-red-600">
            <p>错误: {message.content}</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📊 流式报告生成</h1>
              <p className="text-gray-500 mt-1">实时生成房产分析报告</p>
            </div>
            <Button variant="outline" onClick={() => navigate('/dashboard')}>
              返回仪表盘
            </Button>
          </div>

          {/* Connection Status */}
          <div className="mt-4 flex items-center gap-2">
            <StatusBadge status={isConnected ? 'completed' : 'processing'} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'WebSocket已连接' : 'WebSocket连接中...'}
            </span>
          </div>
        </div>

        {/* Query Input */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-lg font-medium mb-4">生成报告</h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入查询内容，例如：深圳南山区房价"
              className="flex-1 p-2 border rounded-lg"
            />
            <Button 
              onClick={startReportGeneration}
              disabled={!isConnected || isGenerating}
            >
              开始生成
            </Button>
          </div>
        </div>

        {/* Control Buttons */}
        {isGenerating && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6 flex gap-3">
            <Button variant="outline" onClick={() => sendControlCommand('pause')}>
              暂停
            </Button>
            <Button variant="outline" onClick={() => sendControlCommand('resume')}>
              继续
            </Button>
            <Button variant="outline" onClick={() => sendControlCommand('skip')}>
              跳过
            </Button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 rounded-lg p-4 mb-6 text-red-600">
            {error}
          </div>
        )}

        {/* Report Output */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6 max-h-[600px] overflow-y-auto">
          <h2 className="text-lg font-medium mb-4">报告内容</h2>
          {messages.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>点击"开始生成"按钮开始生成报告</p>
            </div>
          ) : (
            messages.map((message, index) => renderMessage(message, index))
          )}
        </div>

        {/* Footer */}
        <div className="bg-white rounded-lg shadow-lg p-4 text-center text-sm text-gray-500">
          <p>流式报告生成功能 - 实时展示分析过程</p>
        </div>
      </div>
    </div>
  );
};

export default StreamingReport;