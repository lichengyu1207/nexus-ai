import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import CharacterAvatar from '../components/CharacterAvatar';
import Dudu from '../components/Dudu';
import ProgressCamp from '../components/ProgressCamp';
import { api } from '../services/api';

interface Progress {
  status: string;
  current_step: string;
  steps: Array<{
    step_name: string;
    status: string;
    comment: string;
  }>;
  step_comment: string;
}

const PERSONA_CONFIGS = {
  zhouyu: {
    name: '周瑜大都督',
    welcomeText: '主公请讲，瑜已备好羽扇，只待一声令下。',
    thinkingText: '正在推演...',
    buttonText: '调兵遣将',
  },
  luxun: {
    name: '陆逊大都督',
    welcomeText: '主公请讲，逊已布好阵势，随时可探。',
    thinkingText: '正在探查...',
    buttonText: '布阵发令',
  },
};

export const TaskAnalysisPage: React.FC = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [persona, setPersona] = useState<'zhouyu' | 'luxun'>('zhouyu');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchPersona();
  }, []);

  useEffect(() => {
    if (!taskId) return;
    
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/tasks/${taskId}/progress`);
        setProgress(response.data);
        
        if (response.data.status === 'completed') {
          clearInterval(interval);
          navigate(`/reports/${taskId}`);
        }
      } catch (error) {
        console.error('Failed to fetch progress:', error);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [taskId, navigate]);

  const fetchPersona = async () => {
    try {
      const response = await api.get('/consult/persona');
      setPersona(response.data.persona);
    } catch (error) {
      console.error('Failed to fetch persona:', error);
    }
  };

  const handleSubmit = async () => {
    if (!query.trim() || isLoading) return;
    
    setIsLoading(true);
    try {
      const response = await api.post('/tasks', {
        query: query.trim(),
      });
      setTaskId(response.data.task_id);
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const config = PERSONA_CONFIGS[persona];

  return (
    <div className="max-w-4xl mx-auto p-6">
      {!taskId ? (
        <motion.div
          className="bg-white rounded-2xl shadow-xl p-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-6 mb-8">
            <CharacterAvatar persona={persona} emotion="default" size="lg" />
            <div>
              <h2 className="text-3xl font-bold mb-2">{config.name}</h2>
              <p className="text-gray-600">{config.welcomeText}</p>
            </div>
          </div>
          
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="例如：深圳南山区1000万学区房"
            className="w-full p-4 border border-gray-300 rounded-lg mb-4 h-32 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          
          <motion.button
            onClick={handleSubmit}
            disabled={!query.trim() || isLoading}
            className="w-full bg-primary-600 text-white py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isLoading ? '正在启动...' : config.buttonText}
          </motion.button>
        </motion.div>
      ) : (
        <motion.div
          className="bg-white rounded-2xl shadow-xl p-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="flex items-center gap-6 mb-8">
            <CharacterAvatar persona={persona} emotion="thinking" size="lg" />
            <div>
              <h2 className="text-3xl font-bold mb-2">
                {config.thinkingText}
              </h2>
              <p className="text-gray-600">
                {progress?.step_comment || '正在准备...'}
              </p>
            </div>
          </div>
          
          <ProgressCamp progress={progress} persona={persona} />
          
          <div className="mt-8">
            <Dudu action="think" position="bottom-left" size="md" />
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default TaskAnalysisPage;
