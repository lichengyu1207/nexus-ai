<template>
  <div class="war-room">
    <div class="war-room-header">
      <h1>战时指挥中心</h1>
      <p class="war-room-subtitle">实时监控 · 智能体协同 · 攻防态势</p>
    </div>
    
    <div class="war-room-content">
      <div class="attack-monitor">
        <div class="monitor-header">
          <h3>攻击流量监控</h3>
          <div class="monitor-stats">
            <div class="stat-item" v-for="stat in attackStats" :key="stat.id">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
        
        <div class="chart-container" ref="attackChart"></div>
      </div>
      
      <div class="agent-status">
        <div class="status-header">
          <h3>智能体集群状态</h3>
          <div class="agent-grid">
            <div
              v-for="agent in agents" 
              :key="agent.id"
              class="agent-card"
              :class="{ active: agent.status === 'active' }"
            >
              <div class="agent-avatar">{{ agent.avatar }}</div>
              <div class="agent-info">
                <p class="agent-name">{{ agent.name }}</p>
                <p class="agent-type">{{ agent.type }}</p>
                <div class="agent-metrics">
                  <span>能量: {{ agent.energy }}%</span>
                  <span>任务: {{ agent.tasks }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="defense-status">
          <div class="status-header">
            <h3>防御态势</h3>
          <div class="defense-metrics">
            <div class="metric-card" v-for="metric in defenseMetrics" :key="metric.id">
              <div class="metric-icon">{{ metric.icon }}</div>
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-label">{{ metric.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

interface AttackStat {
  id: string
  label: string
  value: number
  trend: 'up' | 'down' | 'stable'
}

interface Agent {
  id: string
  name: string
  type: string
  status: 'active' | 'idle'
  energy: number
  tasks: number
  avatar: string
}

interface DefenseMetric {
  id: string
  label: string
  value: string
  trend: 'up' | 'down' | 'stable'
  icon: string
}

const attackStats = ref<AttackStat[]>([
  { id: 'total', label: '总攻击量', value: 156, trend: 'up' },
  { id: 'blocked', label: '已拦截', value: 142, trend: 'up' },
  { id: 'active', label: '活跃攻击源', value: 23, trend: 'stable' },
  { id: 'critical', label: '高危攻击', value: 5, trend: 'down' },
])

const agents = ref<Agent[]>([
  { id: '1', name: '监测智能体', type: 'monitoring', status: 'active', energy: 85, tasks: 12, avatar: '🛡️' },
  { id: '2', name: '预警智能体', type: 'warning', status: 'active', energy: 72, tasks: 8, avatar: '⚠️' },
  { id: '3', name: '防御智能体', type: 'defense', status: 'active', energy: 90, tasks: 5, avatar: '🛡️' },
  { id: '4', name: '分析智能体', type: 'analysis', status: 'idle', energy: 45, tasks: 0, avatar: '📊' },
  { id: '5', name: '响应智能体', type: 'response', status: 'active', energy: 76, tasks: 3, avatar: '⚡' },
])

const defenseMetrics = ref<DefenseMetric[]>([
  { id: 'intercept', label: '拦截率', value: '98.5%', trend: 'up', icon: '🛡️' },
  { id: 'response', label: '响应时间', value: '45ms', trend: 'down', icon: '⚡' },
  { id: 'accuracy', label: '识别准确率', value: '99.2%', trend: 'stable', icon: '🎯' },
  { id: 'coverage', label: '防护覆盖', value: '100%', trend: 'stable', icon: '🛡️' },
])

const attackChart = ref<echarts.ECharts | null>()
const defenseChart = ref<echarts.ECharts | null>()
const topologyChart = ref<echarts.ECharts | null>()

const updateCharts = () => {
  if (!attackChart.value) return
  
  attackChart.value = echarts.init(attackChart.value, 'dark')
  attackChart.value.setOption({
    title: { text: '攻击流量监控', left: '10%', right: '10%' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: attackStats.value.map(s => s.label) },
    yAxis: { type: 'value' },
    series: attackStats.value.map(stat => ({
      name: stat.label,
      type: 'line',
      data: [stat.value],
      smooth: true,
    })),
  })
}

  onMounted(() => {
    setInterval(() => {
      const now = Date.now()
      attackStats.value.forEach(stat => {
        const change = Math.random() * 10 - 5
        stat.value = Math.max(0, Math.min(1000, stat.value + change))
        stat.trend = change > 0 ? 'up' : change < 0 ? 'down' : 'stable'
      })
      
      agents.value.forEach(agent => {
        const energyChange = Math.random() * 10 - 5
        agent.energy = Math.max(0, Math.min(100, agent.energy + energyChange))
        agent.tasks = Math.max(0, Math.min(20, agent.tasks + Math.floor(Math.random() * 3) - 1))
      })
      
      defenseMetrics.value.forEach(metric => {
        const change = Math.random() * 2 - 1
        const numValue = parseFloat(metric.value)
        metric.value = Math.max(90, Math.min(100, numValue + change)).toFixed(1) + '%'
      })
    }, 3000)
  })
  
  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style scoped>
.war-room {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2a 0%, #0f02027 100%);
  color: #fff;
  font-family: 'Microsoft YaHei', sans-serif;
  overflow: hidden;
}

  
  .war-room-header {
    padding: 20px 30px;
    background: rgba(0, 0, 0, 0.8);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .war-room-title {
    font-size: 28px;
    font-weight: bold;
    color: #fff;
    margin: 0;
    letter-spacing: 2px;
  }
  
  .war-room-subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    margin-top: 5px;
  }
  
  .war-room-content {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    padding: 20px;
    height: calc(100% - 140px);
  }
  
  .attack-monitor,
  .agent-status,
  .defense-status {
    background: rgba(0, 20, 40, 0.6);
    border-radius: 8px;
    padding: 15px;
  }
  
  .monitor-header,
  .status-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .monitor-header h3,
  .status-header h3 {
    font-size: 16px;
    color: #fff;
    margin: 0;
  }
  
  .monitor-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
  }
  
  .stat-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    padding: 10px;
    text-align: center;
  }
  
  .stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #fff;
  }
  
  .stat-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .chart-container {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    height: 200px;
    margin-top: 15px;
  }
  
  .agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr);
    gap: 10px;
    max-height: 250px;
    overflow-y: auto;
  }
  
  .agent-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all 0.3s;
  }
  
  .agent-card:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: scale(1.02);
  }
  
  .agent-card.active {
    border-left: 3px solid #4caf50;
  }
  
  .agent-card.idle {
    border-left: 3px solid #ff6b6b;
  }
  
  .agent-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
  }
  
  .agent-info {
    flex: 1;
  }
  
  .agent-name {
    font-size: 14px;
    font-weight: bold;
    color: #fff;
  }
  
  .agent-type {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 2px;
  }
  
  .agent-metrics {
    display: flex;
    gap: 15px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .defense-metrics {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .metric-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .metric-icon {
    font-size: 24px;
  }
  
  .metric-value {
    font-size: 20px;
    font-weight: bold;
    color: #fff;
  }
  
  .metric-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
  }
</style>
