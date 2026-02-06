"""
Prompt 构建模块
根据不同模式构建分析提示词
"""

from typing import Optional, Dict, Any
import logging


class PromptBuilder:
    """Prompt 构建器"""
    
    def __init__(self, config):
        """
        初始化 Prompt 构建器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取配置
        self.mode = config.get_analysis_mode()
        self.max_text_length = config.get('analysis', 'max_text_length', default=40000)
        
        # 获取会议信息
        conference = config.get_active_conference()
        self.conference_name = conference['name']
        self.conference_year = conference['year']
        
        # 获取 Prompt 模板
        self.simple_template = config.get_prompt_template('simple')
        self.full_template = config.get_prompt_template('full')
        
        self.logger.info(f"✅ Prompt 构建器初始化成功 (模式: {self.mode})")
    
    def build_simple_prompt(self, paper_info: Dict[str, Any]) -> str:
        """
        构建简单模式的 Prompt
        
        Args:
            paper_info: 论文信息字典
        
        Returns:
            Prompt 文本
        """
        return self.simple_template.format(
            conference=self.conference_name,
            year=self.conference_year,
            title=paper_info.get('title', 'N/A'),
            tldr=paper_info.get('tldr', 'No TL;DR')
        )
    
    def build_full_prompt(self, paper_info: Dict[str, Any], full_text: str) -> str:
        """
        构建完整模式的 Prompt
        
        Args:
            paper_info: 论文信息字典
            full_text: PDF 全文文本
        
        Returns:
            Prompt 文本
        """
        # 截断文本到最大长度
        context_text = full_text[:self.max_text_length] if full_text else "PDF 解析失败，仅依据摘要分析。"
        
        return self.full_template.format(
            conference=self.conference_name,
            year=self.conference_year,
            title=paper_info.get('title', 'N/A'),
            context_text=context_text
        )
    
    def build_prompt(self, paper_info: Dict[str, Any], full_text: Optional[str] = None) -> str:
        """
        根据配置的模式构建 Prompt
        
        Args:
            paper_info: 论文信息字典
            full_text: PDF 全文文本（仅 FULL 模式需要）
        
        Returns:
            Prompt 文本
        """
        if self.mode.upper() == 'SIMPLE':
            return self.build_simple_prompt(paper_info)
        elif self.mode.upper() == 'FULL':
            if full_text is None:
                self.logger.warning("⚠️  FULL 模式但未提供 full_text，降级为 SIMPLE 模式")
                return self.build_simple_prompt(paper_info)
            return self.build_full_prompt(paper_info, full_text)
        else:
            self.logger.error(f"❌ 未知的分析模式: {self.mode}，使用 SIMPLE 模式")
            return self.build_simple_prompt(paper_info)

