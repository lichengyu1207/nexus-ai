import React, { useState, useEffect } from 'react';
import * as echarts from 'echarts';
import axios from 'axios';

const MonitoringDashboard: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMonitoringData();
    const interval = setInterval(loadMonitoringData, 5000); // 每5秒刷新一次
    return () => clearInterval(interval);
  }, []);

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

  useEffect(() => {
    if (monitoringData) {
      initCharts();
    }
  }, [monitoringData]);

  const initCharts = () => {
    // 智能体负载图表
    const agentChart = echarts.init(document.getElementById('agent-chart'));
    const agentOption = {
      title: {
        text: '智能体负载',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
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
          data: Object.values(monitoringData.agents).map((agent: any) => agent.cpu),
          itemStyle: {
            color: '#ffd700'
          }
        },
        {
          name: '内存',
          type: 'bar',
          data: Object.values(monitoringData.agents).map((agent: any) => agent.memory),
          itemStyle: {
            color: '#2196f3'
          }
        }
      ]
    };
    agentChart.setOption(agentOption);

    // 任务成功率图表
    const taskChart = echarts.init(document.getElementById('task-chart'));
    const taskOption = {
      title: {
        text: '任务统计',
        left: 'center'
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

    // 工具调用频率图表
    const toolChart = echarts.init(document.getElementById('tool-chart'));
    const toolOption = {
      title: {
        text: '工具调用频率',
        left: 'center'
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

    // 错误分布图表
    const errorChart = echarts.init(document.getElementById('error-chart'));
    const errorOption = {
      title: {
        text: '错误分布',
        left: 'center'
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

    // 响应窗口大小变化
    window.addEventListener('resize', () => {
      agentChart.resize();
      taskChart.resize();
      toolChart.resize();
      errorChart.resize();
    });
  };

  if (loading) {
    return <div className="text-center p-lg">加载中...</div>;
  }

  if (!monitoringData) {
    return <div className="text-center p-lg">无监控数据</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
      <div className="card">
        <div id="agent-chart" style={{ height: 300, width: '100%' }}></div>
      </div>
      <div className="card">
        <div id="task-chart" style={{ height: 300, width: '100%' }}></div>
      </div>
      <div className="card">
        <div id="tool-chart" style={{ height: 300, width: '100%' }}></div>
      </div>
      <div className="card">
        <div id="error-chart" style={{ height: 300, width: '100%' }}></div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
