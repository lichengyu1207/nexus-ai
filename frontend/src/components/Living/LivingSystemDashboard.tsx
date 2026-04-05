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
  FormControlLabel
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
  AutoGraph as EvolutionIcon
} from '@mui/icons-material';

interface AgentInfo {
  agent_id: string;
  generation: number;
  fitness_score: number;
  energy: number;
  total_earned: number;
  created_at: string;
}

interface TaskInfo {
  task_id: string;
  task_type: string;
  description: string;
  status: string;
  reward: number;
  assigned_agents: string[];
  created_at: string;
}

interface EmergencePattern {
  pattern_id: string;
  pattern_type: string;
  occurrence_count: number;
  first_detected: string;
  last_detected: string;
}

interface SafetyStatus {
  emergency_stop_active: boolean;
  emergency_stop_reason: string | null;
  constraints_count: number;
  parliament_members: number;
  stats: {
    total_checks: number;
    total_violations: number;
    actions_blocked: number;
  };
}

interface SystemStatus {
  blackboard: any;
  task_bidding: any;
  reward_field: any;
  emergence_analyzer: any;
  reproduction: any;
  safety_fence: SafetyStatus;
}

const LivingSystemDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [patterns, setPatterns] = useState<EmergencePattern[]>([]);
  const [safetyStatus, setSafetyStatus] = useState<SafetyStatus | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [topPerformers, setTopPerformers] = useState<any[]>([]);
  const [interactionGraph, setInteractionGraph] = useState<any>(null);
  
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'warning' }>({
    open: false,
    message: '',
    severity: 'success'
  });
  
  const [publishTaskDialog, setPublishTaskDialog] = useState(false);
  const [newTask, setNewTask] = useState({
    task_type: 'defense',
    description: '',
    reward: 10,
    max_team_size: 5
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, tasksRes, patternsRes, performersRes, graphRes] = await Promise.all([
        fetch('/api/living/status'),
        fetch('/api/living/tasks?limit=20'),
        fetch('/api/living/emergence/patterns'),
        fetch('/api/living/rewards/top-performers?limit=10'),
        fetch('/api/living/emergence/graph')
      ]);

      if (statusRes.ok) setSystemStatus(await statusRes.json());
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        setTasks(tasksData.tasks || []);
      }
      if (patternsRes.ok) {
        const patternsData = await patternsRes.json();
        setPatterns(patternsData.patterns || []);
      }
      if (performersRes.ok) {
        const performersData = await performersRes.json();
        setTopPerformers(performersData.performers || []);
      }
      if (graphRes.ok) setInteractionGraph(await graphRes.json());
      
      if (systemStatus?.safety_fence) {
        setSafetyStatus(systemStatus.safety_fence);
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
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleEmergencyStop = async () => {
    try {
      const response = await fetch('/api/living/safety/emergency-stop?reason=manual_trigger', {
        method: 'POST'
      });
      
      if (response.ok) {
        setSnackbar({ open: true, message: '紧急停止已触发', severity: 'warning' });
        fetchData();
      }
    } catch (error) {
      setSnackbar({ open: true, message: '操作失败', severity: 'error' });
    }
  };

  const handleClearEmergencyStop = async () => {
    try {
      const response = await fetch('/api/living/safety/emergency-stop/clear?authorized_by=admin', {
        method: 'POST'
      });
      
      if (response.ok) {
        setSnackbar({ open: true, message: '紧急停止已解除', severity: 'success' });
        fetchData();
      }
    } catch (error) {
      setSnackbar({ open: true, message: '操作失败', severity: 'error' });
    }
  };

  const handlePublishTask = async () => {
    try {
      const response = await fetch('/api/living/tasks/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newTask,
          required_skills: [],
          priority: 2,
          created_by: 'admin'
        })
      });
      
      if (response.ok) {
        setSnackbar({ open: true, message: '任务已发布', severity: 'success' });
        setPublishTaskDialog(false);
        fetchData();
      }
    } catch (error) {
      setSnackbar({ open: true, message: '发布失败', severity: 'error' });
    }
  };

  const renderOverview = () => (
    <Grid container spacing={3}>
      {safetyStatus?.emergency_stop_active && (
        <Grid item xs={12}>
          <Alert severity="error" icon={<WarningIcon />}>
            紧急停止已激活: {safetyStatus.emergency_stop_reason}
            <Button
              size="small"
              color="inherit"
              onClick={handleClearEmergencyStop}
              sx={{ ml: 2 }}
            >
              解除紧急停止
            </Button>
          </Alert>
        </Grid>
      )}
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              活跃智能体
            </Typography>
            <Typography variant="h4">
              {systemStatus?.reproduction?.total_agents || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              平均能量: {systemStatus?.reproduction?.avg_energy?.toFixed(2) || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              活跃任务
            </Typography>
            <Typography variant="h4">
              {systemStatus?.task_bidding?.active_tasks || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              待处理: {systemStatus?.task_bidding?.pending_tasks || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              涌现模式
            </Typography>
            <Typography variant="h4">
              {systemStatus?.emergence_analyzer?.detected_patterns || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              唯一智能体: {systemStatus?.emergence_analyzer?.unique_agents || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              安全状态
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="h4">
                {safetyStatus?.emergency_stop_active ? (
                  <ErrorIcon color="error" fontSize="large" />
                ) : (
                  <CheckIcon color="success" fontSize="large" />
                )}
              </Typography>
              <Box>
                <Typography variant="body2">
                  违规: {safetyStatus?.stats?.total_violations || 0}
                </Typography>
                <Typography variant="body2">
                  阻止: {safetyStatus?.stats?.actions_blocked || 0}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <EnergyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              能量排行榜
            </Typography>
            <List dense>
              {topPerformers.slice(0, 5).map((performer, index) => (
                <ListItem key={performer.agent_id}>
                  <ListItemIcon>
                    <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>
                      {index + 1}
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={performer.agent_id}
                    secondary={`能量: ${performer.reward.toFixed(2)}`}
                  />
                  <Chip
                    size="small"
                    label={performer.reward.toFixed(1)}
                    color={index === 0 ? 'primary' : 'default'}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <ScienceIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              涌现模式
            </Typography>
            <List dense>
              {patterns.slice(0, 5).map((pattern) => (
                <ListItem key={pattern.pattern_id}>
                  <ListItemIcon>
                    <TimelineIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={pattern.pattern_type}
                    secondary={`出现 ${pattern.occurrence_count} 次`}
                  />
                  <Chip
                    size="small"
                    label={pattern.pattern_type}
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

  const renderTasks = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">任务列表</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setPublishTaskDialog(true)}
        >
          发布任务
        </Button>
      </Box>
      
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>任务ID</TableCell>
              <TableCell>类型</TableCell>
              <TableCell>描述</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>奖励</TableCell>
              <TableCell>分配智能体</TableCell>
              <TableCell>创建时间</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.task_id}>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: 12 }}>
                  {task.task_id.substring(0, 16)}...
                </TableCell>
                <TableCell>
                  <Chip size="small" label={task.task_type} />
                </TableCell>
                <TableCell>{task.description?.substring(0, 30)}...</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={task.status}
                    color={
                      task.status === 'completed' ? 'success' :
                      task.status === 'failed' ? 'error' :
                      task.status === 'in_progress' ? 'primary' : 'default'
                    }
                  />
                </TableCell>
                <TableCell>{task.reward.toFixed(2)}</TableCell>
                <TableCell>
                  {task.assigned_agents?.length > 0 ? (
                    <Badge badgeContent={task.assigned_agents.length} color="primary">
                      <TeamIcon />
                    </Badge>
                  ) : '-'}
                </TableCell>
                <TableCell>
                  {new Date(task.created_at).toLocaleString('zh-CN')}
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
              进化统计
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">总繁殖次数</Typography>
                <Typography variant="h5">
                  {systemStatus?.reproduction?.reproduction_stats?.total_reproductions || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">无性繁殖</Typography>
                <Typography variant="h5">
                  {systemStatus?.reproduction?.reproduction_stats?.asexual_reproductions || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">有性繁殖</Typography>
                <Typography variant="h5">
                  {systemStatus?.reproduction?.reproduction_stats?.sexual_reproductions || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">失败次数</Typography>
                <Typography variant="h5">
                  {systemStatus?.reproduction?.reproduction_stats?.failed_reproductions || 0}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <NetworkIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              交互网络
            </Typography>
            {interactionGraph ? (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  节点: {interactionGraph.nodes?.length || 0} | 边: {interactionGraph.edges?.length || 0}
                </Typography>
                <Grid container spacing={1}>
                  {interactionGraph.nodes?.slice(0, 20).map((node: string) => (
                    <Grid item key={node}>
                      <Chip
                        icon={<AgentIcon />}
                        label={node}
                        size="small"
                        variant="outlined"
                      />
                    </Grid>
                  ))}
                </Grid>
              </Box>
            ) : (
              <Typography color="text.secondary">暂无交互数据</Typography>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderSafety = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">
                <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                安全围栏控制
              </Typography>
              {safetyStatus?.emergency_stop_active ? (
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleClearEmergencyStop}
                >
                  解除紧急停止
                </Button>
              ) : (
                <Button
                  variant="contained"
                  color="error"
                  onClick={handleEmergencyStop}
                >
                  触发紧急停止
                </Button>
              )}
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">总检查次数</Typography>
                <Typography variant="h5">
                  {safetyStatus?.stats?.total_checks || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">违规次数</Typography>
                <Typography variant="h5" color={safetyStatus?.stats?.total_violations > 0 ? 'error' : 'text.primary'}>
                  {safetyStatus?.stats?.total_violations || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">阻止操作</Typography>
                <Typography variant="h5">
                  {safetyStatus?.stats?.actions_blocked || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography color="text.secondary">议会成员</Typography>
                <Typography variant="h5">
                  {safetyStatus?.parliament_members || 0}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <GavelIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              约束列表
            </Typography>
            <Typography color="text.secondary">
              已启用约束: {safetyStatus?.constraints_count || 0}
            </Typography>
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
          活体智能体系统
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
          <Tab label="任务管理" />
          <Tab label="进化系统" />
          <Tab label="安全控制" />
        </Tabs>
      </Box>

      <Box sx={{ mt: 2 }}>
        {activeTab === 0 && renderOverview()}
        {activeTab === 1 && renderTasks()}
        {activeTab === 2 && renderEvolution()}
        {activeTab === 3 && renderSafety()}
      </Box>

      <Dialog open={publishTaskDialog} onClose={() => setPublishTaskDialog(false)}>
        <DialogTitle>发布新任务</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>任务类型</InputLabel>
            <Select
              value={newTask.task_type}
              onChange={(e) => setNewTask({ ...newTask, task_type: e.target.value })}
            >
              <MenuItem value="defense">防御任务</MenuItem>
              <MenuItem value="analysis">分析任务</MenuItem>
              <MenuItem value="coordination">协调任务</MenuItem>
              <MenuItem value="monitoring">监控任务</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="任务描述"
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            sx={{ mt: 2 }}
          />
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="奖励"
                value={newTask.reward}
                onChange={(e) => setNewTask({ ...newTask, reward: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="最大团队规模"
                value={newTask.max_team_size}
                onChange={(e) => setNewTask({ ...newTask, max_team_size: parseInt(e.target.value) })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPublishTaskDialog(false)}>取消</Button>
          <Button variant="contained" onClick={handlePublishTask}>发布</Button>
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

export default LivingSystemDashboard;
