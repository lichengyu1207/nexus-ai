import grpc
from concurrent import futures
import json
from typing import Dict, Any
import consul

class AgentGRPCServer:
    """智能体gRPC服务器"""
    
    def __init__(self, agent_name: str, port: int, agent_instance: Any):
        self.agent_name = agent_name
        self.port = port
        self.agent_instance = agent_instance
        self.server = None
        self.consul_client = consul.Consul(host='localhost', port=8500)
    
    def start(self):
        """启动gRPC服务器"""
        # 创建gRPC服务器
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # 注册服务（这里需要根据生成的pb2文件进行注册）
        # agent_pb2_grpc.add_AgentServiceServicer_to_server(
        #     self._create_servicer(),
        #     self.server
        # )
        
        # 绑定端口
        self.server.add_insecure_port(f'[::]:{self.port}')
        
        # 启动服务器
        self.server.start()
        
        # 注册到Consul
        self._register_to_consul()
        
        print(f"智能体 {self.agent_name} gRPC服务器已启动，端口: {self.port}")
    
    def stop(self):
        """停止gRPC服务器"""
        if self.server:
            self.server.stop(0)
            print(f"智能体 {self.agent_name} gRPC服务器已停止")
    
    def _create_servicer(self):
        """创建服务实现"""
        # 这里需要根据生成的pb2文件创建服务实现
        pass
    
    def _register_to_consul(self):
        """注册到Consul"""
        try:
            self.consul_client.agent.service.register(
                name=self.agent_name,
                service_id=f"{self.agent_name}-{self.port}",
                address='localhost',
                port=self.port,
                check=consul.Check.tcp('localhost', self.port, interval='10s')
            )
            print(f"智能体 {self.agent_name} 已注册到Consul")
        except Exception as e:
            print(f"注册到Consul失败: {e}")


class AgentGRPCClient:
    """智能体gRPC客户端"""
    
    def __init__(self):
        self.consul_client = consul.Consul(host='localhost', port=8500)
        self.channels: Dict[str, grpc.Channel] = {}
    
    def execute(
        self,
        agent_name: str,
        task_id: str,
        action: str,
        params: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            agent_name: 智能体名称
            task_id: 任务ID
            action: 动作类型
            params: 参数
            
        Returns:
            执行结果
        """
        # 获取服务地址
        address = self._get_service_address(agent_name)
        if not address:
            raise Exception(f"未找到智能体服务: {agent_name}")
        
        # 获取或创建通道
        if agent_name not in self.channels:
            self.channels[agent_name] = grpc.insecure_channel(address)
        
        channel = self.channels[agent_name]
        
        # 创建存根（这里需要根据生成的pb2文件创建）
        # stub = agent_pb2_grpc.AgentServiceStub(channel)
        
        # 创建请求
        # request = agent_pb2.TaskRequest(
        #     task_id=task_id,
        #     action=action,
        #     params=params
        # )
        
        # 调用服务
        # response = stub.Execute(request)
        
        # 返回结果
        # return {
        #     "success": response.success,
        #     "result": json.loads(response.result) if response.result else None,
        #     "error": response.error
        # }
        
        # 模拟返回
        return {
            "success": True,
            "result": {"message": "执行成功"},
            "error": None
        }
    
    def get_status(self, agent_name: str) -> Dict[str, Any]:
        """
        获取智能体状态
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            状态信息
        """
        # 获取服务地址
        address = self._get_service_address(agent_name)
        if not address:
            raise Exception(f"未找到智能体服务: {agent_name}")
        
        # 获取或创建通道
        if agent_name not in self.channels:
            self.channels[agent_name] = grpc.insecure_channel(address)
        
        channel = self.channels[agent_name]
        
        # 创建存根（这里需要根据生成的pb2文件创建）
        # stub = agent_pb2_grpc.AgentServiceStub(channel)
        
        # 调用服务
        # response = stub.GetStatus(agent_pb2.Empty())
        
        # 返回结果
        # return {
        #     "agent_name": response.agent_name,
        #     "status": response.status,
        #     "task_count": response.task_count,
        #     "cpu_usage": response.cpu_usage,
        #     "memory_usage": response.memory_usage
        # }
        
        # 模拟返回
        return {
            "agent_name": agent_name,
            "status": "active",
            "task_count": 10,
            "cpu_usage": 15.5,
            "memory_usage": 25.3
        }
    
    def _get_service_address(self, agent_name: str) -> str:
        """
        从Consul获取服务地址
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            服务地址
        """
        try:
            services = self.consul_client.agent.services()
            for service_id, service in services.items():
                if service['Service'] == agent_name:
                    return f"{service['Address']}:{service['Port']}"
            return None
        except Exception as e:
            print(f"从Consul获取服务地址失败: {e}")
            return None
    
    def close(self):
        """关闭所有通道"""
        for channel in self.channels.values():
            channel.close()
        self.channels.clear()
