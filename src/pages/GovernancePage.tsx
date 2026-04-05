import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import governanceApi, { Department } from '@/api/governance';

const departmentNames: Record<Department, string> = {
  li: '吏部', hu: '户部', li_guan: '礼部', bing: '兵部', xing: '刑部', gong: '工部',
};

const departmentColors: Record<Department, string> = {
  li: 'bg-purple-500', hu: 'bg-green-500', li_guan: 'bg-blue-500',
  bing: 'bg-red-500', xing: 'bg-orange-500', gong: 'bg-yellow-500',
};

const GovernancePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedDept, setSelectedDept] = useState<Department | null>(null);

  const { data: status } = useQuery({ queryKey: ['governanceStatus'], queryFn: governanceApi.getStatus });
  const { data: departments } = useQuery({ queryKey: ['governanceDepartments'], queryFn: governanceApi.getDepartments });
  const { data: tasks } = useQuery({ queryKey: ['governanceTasks'], queryFn: () => governanceApi.getTasks(undefined, 20) });

  const submitMutation = useMutation({
    mutationFn: (params: { department: Department; task_type: string; description: string }) =>
      governanceApi.submitRequest(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governanceTasks', 'governanceStatus'] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">三省六部治理系统</h2>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-green-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">待处理</p>
          <p className="text-2xl font-bold">{status?.pending_requests || 0}</p>
        </div>
        <div className="bg-blue-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">今日完成</p>
          <p className="text-2xl font-bold">{status?.completed_today || 0}</p>
        </div>
        <div className="bg-purple-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">平均处理时间</p>
          <p className="text-2xl font-bold">{status?.avg_processing_time?.toFixed(1) || 0}s</p>
        </div>
        <div className="bg-gray-700 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">系统状态</p>
          <p className="text-2xl font-bold">{status?.is_active ? '运行中' : '待机'}</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold mb-4">六部</h3>
        <div className="grid grid-cols-6 gap-4">
          {(Object.keys(departmentNames) as Department[]).map((dept) => (
            <motion.div
              key={dept}
              whileHover={{ scale: 1.02 }}
              onClick={() => setSelectedDept(dept)}
              className={`p-4 rounded-lg cursor-pointer text-center text-white ${
                selectedDept === dept ? 'ring-2 ring-primary-500' : ''
              } ${departmentColors[dept]}`}
            >
              <p className="font-medium">{departmentNames[dept]}</p>
              <p className="text-xs opacity-80 mt-1">
                {departments?.departments?.find(d => d.code === dept)?.agent_count || 0} 智能体
              </p>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold mb-4">任务列表</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {tasks?.tasks?.map((task) => (
            <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div>
                <p className="font-medium text-sm">{task.task_type}</p>
                <p className="text-xs text-gray-500">{departmentNames[task.department]} · {task.description}</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-xs ${
                task.status === 'completed' ? 'bg-green-100 text-green-700' :
                task.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {task.status}
              </span>
            </div>
          ))}
          {(!tasks?.tasks || tasks.tasks.length === 0) && (
            <p className="text-center py-8 text-gray-500">暂无任务</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GovernancePage;
