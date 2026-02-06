"""
Gemini API 客户端封装
提供论文分析功能
"""

import time
from typing import Optional
from google import genai
from utils.rate_limiter import GeminiRateLimiter
from utils.logger import AuditLogger
import logging


class GeminiClient:
    """Gemini API 客户端"""
    
    def __init__(self, config, audit_logger: Optional[AuditLogger] = None):
        """
        初始化 Gemini 客户端
        
        Args:
            config: 配置对象
            audit_logger: 审计日志记录器
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取 API Key 和模型名称
        api_key = config.get_api_key()
        self.model_name = config.get_gemini_model()
        
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            raise ValueError("请配置有效的 GEMINI_API_KEY")
        
        # 初始化 Gemini 客户端
        self.client = genai.Client(api_key=api_key)
        
        # 初始化速率限制器
        rate_config = config.get('rate_limit', 'gemini', default={})
        self.rate_limiter = GeminiRateLimiter(
            max_requests=rate_config.get('max_requests', 1000),
            time_window=rate_config.get('time_window', 60)
        )
        
        # 重试配置
        retry_config = config.get('retry', default={})
        self.max_retries = retry_config.get('max_retries', 3)
        self.base_delay = retry_config.get('base_delay', 0.5)
        
        self.logger.info(f"✅ Gemini 客户端初始化成功 (模型: {self.model_name})")
    
    def analyze_paper(self, prompt: str) -> str:
        """
        分析论文（带重试机制）

        Args:
            prompt: 分析提示词

        Returns:
            分析结果文本
        """
        retries = 0

        while retries < self.max_retries:
            try:
                # 应用速率限制
                self.rate_limiter.wait_if_needed()

                # 记录API调用
                if self.audit_logger:
                    self.audit_logger.log_api_call('gemini')

                # 调用 Gemini API（使用完整模型路径）
                full_model_name = f"models/{self.model_name}" if not self.model_name.startswith("models/") else self.model_name
                response = self.client.models.generate_content(
                    model=full_model_name,
                    contents=prompt
                )

                return response.text

            except Exception as e:
                retries += 1
                error_msg = str(e)

                # 记录错误
                if self.audit_logger:
                    self.audit_logger.log_error(f"Gemini API 调用失败 (尝试 {retries}/{self.max_retries})", e)

                if retries < self.max_retries:
                    # 重试前等待
                    wait_time = self.base_delay * (2 ** (retries - 1))  # 指数退避
                    self.logger.warning(f"⚠️  Gemini API 调用失败，{wait_time:.1f}秒后重试... (错误: {error_msg})")
                    time.sleep(wait_time)
                else:
                    # 所有重试都失败
                    self.logger.error(f"❌ Gemini API 调用彻底失败: {error_msg}")
                    return "AI 分析失败：达到最大重试次数"

        return "AI 分析失败：未知错误"
    
    def batch_analyze(self, prompts: list) -> list:
        """
        批量分析论文
        
        Args:
            prompts: 提示词列表
        
        Returns:
            分析结果列表
        """
        results = []
        total = len(prompts)
        
        for i, prompt in enumerate(prompts, 1):
            self.logger.info(f"🤖 正在分析论文 {i}/{total}...")
            result = self.analyze_paper(prompt)
            results.append(result)
        
        return results

