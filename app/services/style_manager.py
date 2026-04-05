"""
StyleManager - 代理风格配置管理器
负责加载、解析和管理不同分析风格的配置
"""
from typing import Dict, Any, List, Optional
import os
import yaml
from pathlib import Path


class StyleManager:
    """
    风格管理器 - 单例模式
    负责加载和管理代理风格配置
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_dir: str = None):
        """
        初始化风格管理器
        
        Args:
            config_dir: 配置文件目录路径，默认为项目根目录下的config/agent_styles
        """
        if self._initialized:
            return
        
        # 设置配置目录
        if config_dir is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            config_dir = os.path.join(project_root, 'config', 'agent_styles')
        
        self.config_dir = Path(config_dir)
        self.styles: Dict[str, Dict[str, Any]] = {}
        
        # 加载所有风格配置
        self._load_all_styles()
        
        self._initialized = True
        print(f"✅ StyleManager initialized with {len(self.styles)} styles")
    
    def _load_all_styles(self) -> None:
        """加载所有风格配置文件"""
        if not self.config_dir.exists():
            print(f"⚠️ Config directory not found: {self.config_dir}")
            return
        
        # 扫描所有YAML文件
        for yaml_file in self.config_dir.glob("*.yaml"):
            style_name = yaml_file.stem  # 文件名（不含扩展名）
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    style_config = yaml.safe_load(f)
                    self.styles[style_name] = style_config
                    print(f"✅ Loaded style: {style_name}")
            except Exception as e:
                print(f"❌ Error loading style {style_name}: {str(e)}")
    
    def get_style(self, style_name: str) -> Dict[str, Any]:
        """
        获取指定风格的完整配置
        
        Args:
            style_name: 风格名称（conservative/balanced/aggressive）
            
        Returns:
            Dict: 风格配置字典
            
        Raises:
            ValueError: 如果风格不存在
        """
        if style_name not in self.styles:
            available = list(self.styles.keys())
            raise ValueError(f"Style '{style_name}' not found. Available styles: {available}")
        
        return self.styles[style_name]
    
    def get_agent_style(self, style_name: str, agent_name: str) -> Dict[str, Any]:
        """
        获取指定风格下特定代理的配置
        
        Args:
            style_name: 风格名称
            agent_name: 代理名称
            
        Returns:
            Dict: 代理配置字典
        """
        style = self.get_style(style_name)
        
        # 尝试多种代理名称格式
        agent_key = agent_name
        if agent_key not in style:
            # 尝试转换为下划线格式
            agent_key = agent_name.replace('-', '_')
        
        if agent_key not in style:
            # 尝试转换为连字符格式
            agent_key = agent_name.replace('_', '-')
        
        if agent_key not in style:
            raise ValueError(f"Agent '{agent_name}' not found in style '{style_name}'")
        
        return style[agent_key]
    
    def list_styles(self) -> List[str]:
        """
        获取所有可用风格列表
        
        Returns:
            List[str]: 风格名称列表
        """
        return list(self.styles.keys())
    
    def get_style_description(self, style_name: str) -> str:
        """
        获取风格描述
        
        Args:
            style_name: 风格名称
            
        Returns:
            str: 风格描述
        """
        descriptions = {
            "conservative": "保守型：注重数据可靠性和风险控制，偏好低风险资产，强调稳健投资",
            "balanced": "均衡型：平衡风险与收益，综合考虑多种因素，提供中肯建议",
            "aggressive": "进取型：关注高增长潜力，接受较高风险，寻找投资机会"
        }
        
        return descriptions.get(style_name, f"风格：{style_name}")
    
    def get_style_metadata(self, style_name: str) -> Dict[str, Any]:
        """
        获取风格元数据
        
        Args:
            style_name: 风格名称
            
        Returns:
            Dict: 风格元数据
        """
        return {
            "name": style_name,
            "description": self.get_style_description(style_name),
            "agents": list(self.get_style(style_name).keys())
        }
    
    def reload_styles(self) -> None:
        """重新加载所有风格配置"""
        self.styles.clear()
        self._load_all_styles()
        print(f"✅ Reloaded {len(self.styles)} styles")


# 全局单例实例
style_manager = StyleManager()
