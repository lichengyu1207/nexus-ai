import React from 'react';
import { Box, Card, CardContent, Typography, Alert } from '@mui/material';
import { Assessment as AssessmentIcon } from '@mui/icons-material';

const LearningMonitorPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <AssessmentIcon sx={{ mr: 1, fontSize: 28, color: 'primary.main' }} />
            <Typography variant="h5" component="h1">
              学习监控面板
            </Typography>
          </Box>
          <Alert severity="info" sx={{ mt: 2 }}>
            此功能正在开发中，敬请期待...
          </Alert>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            学习监控面板将提供智能体学习状态、训练任务、反思记录和模型版本管理等功能。
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default LearningMonitorPage;
