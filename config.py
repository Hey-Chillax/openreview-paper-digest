"""
配置加载模块
负责加载和管理 config.yaml 配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)
        
        # 从环境变量读取 API Key (优先级高于配置文件)
        self._load_api_key_from_env()
    
    def _load_api_key_from_env(self):
        """从环境变量加载 API Key"""
        env_key = os.getenv('GEMINI_API_KEY')
        if env_key:
            self.data['api']['gemini_api_key'] = env_key
            print("✅ 从环境变量加载 GEMINI_API_KEY")
        elif self.data['api']['gemini_api_key'] == 'YOUR_API_KEY_HERE':
            print("⚠️  警告: 请设置 GEMINI_API_KEY 环境变量或在 config.yaml 中配置")
    
    def get_active_conference(self) -> Dict[str, Any]:
        """
        获取当前激活的会议配置
        
        Returns:
            会议配置字典，包含 name, year, invitation
        """
        index = self.data['active_conference_index']
        conferences = self.data['conferences']
        
        if index < 0 or index >= len(conferences):
            raise ValueError(f"无效的会议索引: {index}, 共有 {len(conferences)} 个会议配置")
        
        return conferences[index]
    
    def get(self, *keys, default=None) -> Any:
        """
        获取嵌套配置值
        
        Args:
            *keys: 配置键路径，例如 get('api', 'gemini_api_key')
            default: 默认值
        
        Returns:
            配置值
        """
        value = self.data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_api_key(self) -> str:
        """获取 Gemini API Key"""
        return self.get('api', 'gemini_api_key')
    
    def get_gemini_model(self) -> str:
        """获取 Gemini 模型名称"""
        return self.get('api', 'gemini_model', default='gemini-2.0-flash-exp')
    
    def get_keywords(self) -> list:
        """获取筛选关键词列表"""
        return self.get('filtering', 'keywords', default=[])
    
    def get_score_threshold(self) -> float:
        """获取评分门槛"""
        return self.get('filtering', 'score_threshold', default=6.0)
    
    def get_analysis_mode(self) -> str:
        """获取分析模式"""
        return self.get('analysis', 'mode', default='SIMPLE')
    
    def get_max_workers(self) -> int:
        """获取最大并发数"""
        return self.get('concurrency', 'max_workers', default=5)
    
    def get_output_dir(self) -> Path:
        """获取输出目录路径"""
        base_dir = self.get('output', 'base_dir', default='analyses')
        return Path(base_dir)
    
    def is_format_enabled(self, format_name: str) -> bool:
        """
        检查某种输出格式是否启用
        
        Args:
            format_name: 格式名称，如 'excel', 'html', 'markdown'
        
        Returns:
            是否启用
        """
        return self.get('output', 'formats', format_name, default=False)
    
    def get_prompt_template(self, mode: Optional[str] = None) -> str:
        """
        获取 Prompt 模板
        
        Args:
            mode: 模式，'simple' 或 'full'，默认使用配置中的模式
        
        Returns:
            Prompt 模板字符串
        """
        if mode is None:
            mode = self.get_analysis_mode().lower()
        
        template_key = f"{mode}_mode"
        return self.get('prompts', template_key, default="")
    
    def __repr__(self) -> str:
        conference = self.get_active_conference()
        return (f"<Config: {conference['name']} {conference['year']}, "
                f"Mode={self.get_analysis_mode()}, "
                f"Keywords={len(self.get_keywords())}>")


# 全局配置实例（懒加载）
_config_instance: Optional[Config] = None


def load_config(config_path: str = "config.yaml") -> Config:
    """
    加载配置（单例模式）
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        Config实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


def get_config() -> Config:
    """
    获取全局配置实例
    
    Returns:
        Config实例
    """
    if _config_instance is None:
        return load_config()
    return _config_instance

