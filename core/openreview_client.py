"""
OpenReview API 客户端封装
提供论文获取、评分查询等功能
"""

import openreview
from typing import List, Optional, Dict, Any
from utils.rate_limiter import OpenReviewRateLimiter
from utils.logger import AuditLogger
import logging


class OpenReviewClient:
    """OpenReview API 客户端"""
    
    def __init__(self, config, audit_logger: Optional[AuditLogger] = None):
        """
        初始化 OpenReview 客户端
        
        Args:
            config: 配置对象
            audit_logger: 审计日志记录器
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger('openreview_crawler')
        
        # 初始化 OpenReview 客户端
        base_url = config.get('api', 'openreview_base_url', default='https://api2.openreview.net')
        self.client = openreview.api.OpenReviewClient(baseurl=base_url)
        
        # 初始化速率限制器
        rate_config = config.get('rate_limit', 'openreview', default={})
        self.rate_limiter = OpenReviewRateLimiter(
            max_requests=rate_config.get('max_requests', 58),
            time_window=rate_config.get('time_window', 60)
        )
        
        self.logger.info("✅ OpenReview 客户端初始化成功")
    
    def get_all_submissions(self, invitation: str) -> List:
        """
        获取所有投稿论文
        
        Args:
            invitation: 会议的 invitation 字符串
        
        Returns:
            论文列表
        """
        self.logger.info(f"📥 正在获取投稿列表: {invitation}")
        
        self.rate_limiter.wait_if_needed()
        if self.audit_logger:
            self.audit_logger.log_api_call('openreview')
        
        try:
            submissions = self.client.get_all_notes(invitation=invitation)
            self.logger.info(f"✅ 成功获取 {len(submissions)}篇论文")
            return submissions
        except Exception as e:
            self.logger.error(f"❌ 获取投稿列表失败: {e}")
            if self.audit_logger:
                self.audit_logger.log_error("获取投稿列表失败", e)
            raise
    
    def get_paper_notes(self, forum_id: str) -> List:
        """
        获取论文的所有 notes（包括评审意见）
        
        Args:
            forum_id: 论文的 forum ID
        
        Returns:
            notes 列表
        """
        self.rate_limiter.wait_if_needed()
        if self.audit_logger:
            self.audit_logger.log_api_call('openreview')
        
        try:
            notes = self.client.get_notes(forum=forum_id)
            return notes
        except Exception as e:
            self.logger.warning(f"⚠️  获取论文 notes 失败 (forum={forum_id}): {e}")
            if self.audit_logger:
                self.audit_logger.log_error(f"获取论文notes失败 (forum={forum_id})", e)
            return []
    
    def extract_ratings(self, notes: List) -> List[float]:
        """
        从 notes 中提取评分
        
        Args:
            notes: notes 列表
        
        Returns:
            评分列表
        """
        ratings = []
        
        for note in notes:
            if 'rating' in note.content:
                val_raw = note.content['rating']['value']
                try:
                    # 处理不同格式的评分
                    if isinstance(val_raw, str):
                        # 格式如 "8: Top 50%"
                        val = float(val_raw.split(':')[0].strip())
                    else:
                        val = float(val_raw)
                    ratings.append(val)
                except (ValueError, TypeError) as e:
                    self.logger.debug(f"⚠️  无法解析评分: {val_raw}")
                    continue
        
        return ratings
    
    def get_paper_rating(self, forum_id: str) -> Optional[float]:
        """
        获取论文的平均评分
        
        Args:
            forum_id: 论文的 forum ID
        
        Returns:
            平均评分，如果没有评分则返回 None
        """
        notes = self.get_paper_notes(forum_id)
        ratings = self.extract_ratings(notes)
        
        if not ratings:
            return None
        
        return sum(ratings) / len(ratings)
    
    def extract_paper_info(self, note) -> Dict[str, Any]:
        """
        提取论文基本信息
        
        Args:
            note: OpenReview note 对象
        
        Returns:
            论文信息字典
        """
        content = note.content
        
        return {
            'id': note.id,
            'title': content.get('title', {}).get('value', 'N/A'),
            'abstract': content.get('abstract', {}).get('value', ''),
            'tldr': content.get('TL;DR', {}).get('value', 'No TL;DR'),
            'keywords': content.get('keywords', {}).get('value', []),
            'link': f"https://openreview.net/forum?id={note.id}",
            'pdf_link': f"https://openreview.net/pdf?id={note.id}",
        }

