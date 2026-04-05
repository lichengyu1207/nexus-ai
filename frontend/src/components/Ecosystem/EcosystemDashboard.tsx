import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Badge,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Switch,
  FormControlLabel,
  Slider,
  CircularProgress
} from '@mui/material';
import {
  Psychology as AgentIcon,
  Hub as NetworkIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Groups as TeamIcon,
  Gavel as GavelIcon,
  Security as SecurityIcon,
  Science as ScienceIcon,
  Bolt as EnergyIcon,
  AutoGraph as EvolutionIcon,
  FlashOn as AttackIcon,
  Shield as DefenseIcon,
  Storage as MemoryIcon,
  Biotech as ReproductionIcon,
  Insights as EmergenceIcon
} from '@mui/icons-material';

interface AgentInfo {
  agent_id: string;
  agent_type: string;
  species: string;
  generation: number;
  energy: number;
  age: number;
  status: string;
  tasks_completed: number;
  tasks_failed: number;
  is_alive: boolean;
}

interface EcosystemStatus {
  state: string;
  generation: number;
  total_births: number;
  total_deaths: number;
  metrics: {
    total_agents: number;
    attack_agents: number;
    defense_agents: number;
    memory_agents: number;
    avg_energy: number;
    attack_success_rate: number;
    defense_success_rate: number;
    diversity_index: number;
  };
  emergence_patterns: number;
}

interface EvolutionEvent {
  event_type: string;
  subject: string;
  category: string;
  generation: number;
  timestamp: string;
}

interface EmergencePattern {
  pattern_id: string;
  pattern: any;
  first_detected: string;
  occurrence_count: number;
}

const EcosystemDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<EcosystemStatus | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [evolutionHistory, setEvolutionHistory] = useState<EvolutionEvent[]>([]);
  const [emergencePatterns, setEmergencePatterns] = useState<EmergencePattern[]>([]);
  
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'warning' }>({
    open: false,
    message: '',
    severity: 'success'
  });
  
  const [spawnDialog, setSpawnDialog] = useState(false);
  const [newAgent, setNewAgent] = useState({
    agent_type: 'attack',
    species: 'default'
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, agentsRes, historyRes, patternsRes] = await Promise.all([
        fetch('/api/ecosystem/status'),
        fetch('/api/ecosystem/agents?limit=50'),
        fetch('/api/ecosystem/evolution/history?limit=50'),
        fetch('/api/ecosystem/emergence/patterns')
      ]);

      if (statusRes.ok) setStatus(await statusRes.json());
      if (agentsRes.ok) {
        const agentsData = await agentsRes.json();
        setAgents(agentsData.agents || []);
      }
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setEvolutionHistory(historyData.history || []);
      }
      if (patternsRes.ok) {
        const patternsData = await patternsRes.json();
        setEmergencePatterns(patternsData.patterns || []);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setSnackbar({ open: true, message: '获取数据失败', severity: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleSpawnAgent = async () => {
    try {
      const response = await fetch('/api/ecosystem/agents/spawn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newAgent)
      });
      
      if (response.ok) {
        setSnackbar({ open: true, message: '智能体已创建', severity: 'success' });
        setSpawnDialog(false);
        fetchData();
      }
    } catch (error) {
      setSnackbar({ open: true, message: '创建失败', severity: 'error' });
    }
  };

  const handleTriggerSelection = async () => {
    try {
      const response = await fetch('/api/ecosystem/selection/trigger', { method: 'POST' });
      if (response.ok) {
        setSnackbar({ open: true, message: '自然选择已触发', severity: 'success' });
        fetchData();
      }
    } catch (error) {
      setSnackbar({ open: true, message: '操作失败', severity: 'error' });
    }
  };

  const handleTriggerMutation = async () => {
    try {
      const response = await fetch('/api/ecosystem/mutation/trigger', { method: 'POST' });
      if (response.ok) {
        setSnackbar({ open: true, message: '变异已触发', severity: 'success' });
        fetchData();
      }
    } catch (error) {
      setSnackbar({ open: true, message: '操作失败', severity: 'error' });
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'stable': return 'success';
      case 'stressed': return 'warning';
      case 'under_attack': return 'error';
      case 'recovering': return 'info';
      case 'evolving': return 'primary';
      default: return 'default';
    }
  };

  const getAgentTypeIcon = (type: string) => {
    switch (type) {
      case 'attack': return <AttackIcon />;
      case 'defense': return <DefenseIcon />;
      case 'memory': return <MemoryIcon />;
      default: return <AgentIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'default';
      case 'working': return 'primary';
      case 'resting': return 'warning';
      case 'reproducing': return 'success';
      case 'dying':
      case 'dead': return 'error';
      default: return 'default';
    }
  };

  const renderOverview = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Alert 
          severity={getStateColor(status?.state || 'stable') as any}
          icon={status?.state === 'under_attack' ? <WarningIcon /> : undefined}
        >
          生态系统状态: {status?.state || 'unknown'} | 第 {status?.generation || 0} 代
        </Alert>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              <AttackIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'error.main' }} />
              攻击智能体
            </Typography>
            <Typography variant="h4">
              {status?.metrics?.attack_agents || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              成功率: {((status?.metrics?.attack_success_rate || 0) * 100).toFixed(1)}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              <DefenseIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'primary.main' }} />
              防御智能体
            </Typography>
            <Typography variant="h4">
              {status?.metrics?.defense_agents || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              成功率: {((status?.metrics?.defense_success_rate || 0) * 100).toFixed(1)}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              <MemoryIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'info.main' }} />
              记忆智能体
            </Typography>
            <Typography variant="h4">
              {status?.metrics?.memory_agents || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              记忆存储节点
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              <EnergyIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'warning.main' }} />
              平均能量
            </Typography>
            <Typography variant="h4">
              {(status?.metrics?.avg_energy || 0).toFixed(1)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              多样性指数: {(status?.metrics?.diversity_index || 0).toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <ReproductionIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              进化统计
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography color="text.secondary">总出生</Typography>
                <Typography variant="h5" color="success.main">
                  {status?.total_births || 0}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="text.secondary">总死亡</Typography>
                <Typography variant="h5" color="error.main">
                  {status?.total_deaths || 0}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="text.secondary">净增长</Typography>
                <Typography variant="h5">
                  {(status?.total_births || 0) - (status?.total_deaths || 0)}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography color="text.secondary">涌现模式</Typography>
                <Typography variant="h5" color="primary">
                  {status?.emergence_patterns || 0}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <EmergenceIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              涌现模式
            </Typography>
            <List dense>
              {emergencePatterns.slice(0, 5).map((pattern) => (
                <ListItem key={pattern.pattern_id}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={pattern.pattern?.type || 'Unknown Pattern'}
                    secondary={`出现 ${pattern.occurrence_count} 次`}
                  />
                  <Chip
                    size="small"
                    label={pattern.pattern?.type || 'pattern'}
                    color="info"
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderAgents = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">智能体列表</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<PlayIcon />}
            onClick={handleTriggerSelection}
            sx={{ mr: 1 }}
          >
            触发选择
          </Button>
          <Button
            variant="outlined"
            startIcon={<ScienceIcon />}
            onClick={handleTriggerMutation}
            sx={{ mr: 1 }}
          >
            触发变异
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setSpawnDialog(true)}
          >
            创建智能体
          </Button>
        </Box>
      </Box>
      
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>类型</TableCell>
              <TableCell>物种</TableCell>
              <TableCell>代数</TableCell>
              <TableCell>能量</TableCell>
              <TableCell>年龄</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>任务</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {agents.map((agent) => (
              <TableRow key={agent.agent_id}>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: 11 }}>
                  {agent.agent_id.substring(0, 20)}...
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    icon={getAgentTypeIcon(agent.agent_type)}
                    label={agent.agent_type}
                    color={agent.agent_type === 'attack' ? 'error' : agent.agent_type === 'defense' ? 'primary' : 'info'}
                  />
                </TableCell>
                <TableCell>{agent.species}</TableCell>
                <TableCell>Gen {agent.generation}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={Math.min(100, agent.energy / 3)} 
                        color={agent.energy > 150 ? 'success' : agent.energy > 50 ? 'warning' : 'error'}
                      />
                    </Box>
                    <Typography variant="body2">{agent.energy.toFixed(0)}</Typography>
                  </Box>
                </TableCell>
                <TableCell>{agent.age}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={agent.status}
                    color={getStatusColor(agent.status)}
                  />
                </TableCell>
                <TableCell>
                  {agent.tasks_completed}/{agent.tasks_failed}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderEvolution = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <EvolutionIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              进化事件历史
            </Typography>
            <List>
              {evolutionHistory.map((event, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {event.event_type === 'birth' && <AddIcon color="success" />}
                    {event.event_type === 'death' && <RemoveIcon color="error" />}
                    {event.event_type === 'reproduction' && <ReproductionIcon color="primary" />}
                    {event.event_type === 'emergence' && <EmergenceIcon color="info" />}
                    {event.event_type === 'generation' && <TimelineIcon />}
                  </ListItemIcon>
                  <ListItemText
                    primary={event.event_type}
                    secondary={`Subject: ${event.subject} | Category: ${event.category} | Gen: ${event.generation}`}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {new Date(event.timestamp).toLocaleString('zh-CN')}
                  </Typography>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          <AgentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          活体智能体生态系统
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchData}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="系统概览" />
          <Tab label="智能体管理" />
          <Tab label="进化历史" />
        </Tabs>
      </Box>

      <Box sx={{ mt: 2 }}>
        {activeTab === 0 && renderOverview()}
        {activeTab === 1 && renderAgents()}
        {activeTab === 2 && renderEvolution()}
      </Box>

      <Dialog open={spawnDialog} onClose={() => setSpawnDialog(false)}>
        <DialogTitle>创建新智能体</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>智能体类型</InputLabel>
            <Select
              value={newAgent.agent_type}
              onChange={(e) => setNewAgent({ ...newAgent, agent_type: e.target.value })}
            >
              <MenuItem value="attack">攻击智能体</MenuItem>
              <MenuItem value="defense">防御智能体</MenuItem>
              <MenuItem value="memory">记忆智能体</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="物种"
            value={newAgent.species}
            onChange={(e) => setNewAgent({ ...newAgent, species: e.target.value })}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSpawnDialog(false)}>取消</Button>
          <Button variant="contained" onClick={handleSpawnAgent}>创建</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EcosystemDashboard;
