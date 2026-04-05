import React, { useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import axios from 'axios';

interface MonitoringData {
  agents: Record<string, { cpu: number; memory: number }>;
  task_stats: {
    total: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
  tool_calls: {
    http: number;
    local: number;
    grpc: number;
  };
  errors: {
    timeout: number;
    permission: number;
    other: number;
  };
}

const MonitoringDashboard: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(false);
  const agentChartRef = useRef<HTMLDivElement>(null);
  const taskChartRef = useRef<HTMLDivElement>(null);
  const toolChartRef = useRef<HTMLDivElement>(null);
  const errorChartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMonitoringData();
    const interval = setInterval(loadMonitoringData, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (monitoringData && agentChartRef.current) {
      initCharts();
    }
  }, [monitoringData]);

  const loadMonitoringData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/monitoring/data');
      setMonitoringData(response.data);
    } catch (error) {
      console.error('加载监控数据失败', error);
    } finally {
      setLoading(false);
    }
  };

  const initCharts = () => {
    if (!monitoringData) return;

    if (agentChartRef.current) {
      const agentChart = echarts.init(agentChartRef.current);
      const agentOption = {
        title: {
          text: '智能体负载',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        legend: {
          data: ['CPU', '内存'],
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: Object.keys(monitoringData.agents)
        },
        yAxis: {
          type: 'value',
          max: 100
        },
        series: [
          {
            name: 'CPU',
            type: 'bar',
            data: Object.values(monitoringData.agents).map((agent) => agent.cpu),
            itemStyle: { color: '#ffd700' }
          },
          {
            name: '内存',
            type: 'bar',
            data: Object.values(monitoringData.agents).map((agent) => agent.memory),
            itemStyle: { color: '#2196f3' }
          }
        ]
      };
      agentChart.setOption(agentOption);
    }

    if (taskChartRef.current) {
      const taskChart = echarts.init(taskChartRef.current);
      const taskOption = {
        title: {
          text: '任务统计',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '任务状态',
            type: 'pie',
            radius: '60%',
            data: [
              {
                value: monitoringData.task_stats.completed,
                name: '成功',
                itemStyle: { color: '#4caf50' }
              },
              {
                value: monitoringData.task_stats.failed,
                name: '失败',
                itemStyle: { color: '#f44336' }
              }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };
      taskChart.setOption(taskOption);
    }

    if (toolChartRef.current) {
      const toolChart = echarts.init(toolChartRef.current);
      const toolOption = {
        title: {
          text: '工具调用频率',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'item'
        },
        series: [
          {
            name: '调用次数',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              {
                value: monitoringData.tool_calls.http,
                name: 'HTTP',
                itemStyle: { color: '#4caf50' }
              },
              {
                value: monitoringData.tool_calls.local,
                name: '本地',
                itemStyle: { color: '#ff9800' }
              },
              {
                value: monitoringData.tool_calls.grpc,
                name: 'gRPC',
                itemStyle: { color: '#2196f3' }
              }
            ]
          }
        ]
      };
      toolChart.setOption(toolOption);
    }

    if (errorChartRef.current) {
      const errorChart = echarts.init(errorChartRef.current);
      const errorOption = {
        title: {
          text: '错误分布',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'item'
        },
        series: [
          {
            name: '错误类型',
            type: 'pie',
            radius: '60%',
            data: [
              {
                value: monitoringData.errors.timeout,
                name: '超时',
                itemStyle: { color: '#ff9800' }
              },
              {
                value: monitoringData.errors.permission,
                name: '权限',
                itemStyle: { color: '#f44336' }
              },
              {
                value: monitoringData.errors.other,
                name: '其他',
                itemStyle: { color: '#9e9e9e' }
              }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };
      errorChart.setOption(errorOption);
    }

    const handleResize = () => {
      if (agentChartRef.current) {
        echarts.getInstanceByDom(agentChartRef.current)?.resize();
      }
      if (taskChartRef.current) {
        echarts.getInstanceByDom(taskChartRef.current)?.resize();
      }
      if (toolChartRef.current) {
        echarts.getInstanceByDom(toolChartRef.current)?.resize();
      }
      if (errorChartRef.current) {
        echarts.getInstanceByDom(errorChartRef.current)?.resize();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  };

  if (loading && !monitoringData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!monitoringData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center text-gray-500">
          <p>无监控数据</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div ref={agentChartRef} style={{ height: 300, width: '100%' }}></div>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div ref={taskChartRef} style={{ height: 300, width: '100%' }}></div>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div ref={toolChartRef} style={{ height: 300, width: '100%' }}></div>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div ref={errorChartRef} style={{ height: 300, width: '100%' }}></div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
