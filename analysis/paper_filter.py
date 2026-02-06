"""
论文筛选模块
根据关键词和评分筛选论文
"""

from typing import Optional, Dict, Any
from utils.text_processor import KeywordMatcher
from utils.logger import AuditLogger
import logging


class PaperFilter:
    """论文筛选器"""
    
    def __init__(self, config, audit_logger: Optional[AuditLogger] = None):
        """
        初始化论文筛选器
        
        Args:
            config: 配置对象
            audit_logger: 审计日志记录器
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取筛选配置
        self.keywords = config.get_keywords()
        self.score_threshold = config.get_score_threshold()
        self.use_regex = config.get('filtering', 'use_regex', default=True)
        
        # 初始化关键词匹配器
        self.keyword_matcher = KeywordMatcher(self.keywords, use_regex=self.use_regex)
        
        self.logger.info(f"✅ 论文筛选器初始化成功 (关键词: {len(self.keywords)}个, 评分门槛: {self.score_threshold})")
    
    def check_keywords(self, paper_info: Dict[str, Any]) -> bool:
        """
        检查论文是否匹配关键词

        Args:
            paper_info: 论文信息字典

        Returns:
            是否匹配
        """
        # 如果没有设置关键词，则全部通过
        if not self.keywords:
            return True

        # 组合标题和关键词进行匹配
        title = paper_info.get('title', '')
        keywords = paper_info.get('keywords', [])

        combined_text = title + " " + " ".join(keywords)

        return self.keyword_matcher.match(combined_text)
    
    def check_rating(self, rating: Optional[float]) -> bool:
        """
        检查评分是否达标

        Args:
            rating: 论文评分

        Returns:
            是否达标
        """
        # 如果没有设置评分门槛（<=0），则全部通过
        if self.score_threshold <= 0:
            return True

        if rating is None:
            return False

        return rating >= self.score_threshold
    
    def filter_paper(self, paper_info: Dict[str, Any], rating: Optional[float]) -> Optional[str]:
        """
        筛选论文
        
        Args:
            paper_info: 论文信息字典
            rating: 论文评分
        
        Returns:
            如果通过筛选返回 None，否则返回筛选失败原因
        """
        # 检查关键词
        if not self.check_keywords(paper_info):
            return "关键词不匹配"
        
        # 检查评分
        if not self.check_rating(rating):
            if rating is None:
                return "无评分"
            else:
                return f"评分过低 ({rating:.2f} < {self.score_threshold})"
        
        # 通过筛选
        return None
    
    def get_matched_keywords(self, paper_info: Dict[str, Any]) -> list:
        """
        获取论文匹配的关键词
        
        Args:
            paper_info: 论文信息字典
        
        Returns:
            匹配的关键词列表
        """
        title = paper_info.get('title', '')
        keywords = paper_info.get('keywords', [])
        
        combined_text = title + " " + " ".join(keywords)
        
        return self.keyword_matcher.find_matched_keywords(combined_text)

