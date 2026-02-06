"""
API速率限制器
用于控制OpenReview和Gemini API的请求频率，避免触发限流
"""

import time
import threading
from collections import deque
from typing import Optional


class BaseRateLimiter:
    """基础速率限制器"""
    
    def __init__(self, max_requests: int, time_window: int, name: str = "API"):
        """
        初始化速率限制器
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口大小（秒）
            name: 限制器名称（用于日志）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.name = name
        self.request_times = deque()
        self.lock = threading.Lock()
    
    def wait_if_needed(self) -> float:
        """
        如果需要等待，则等待到允许请求为止
        
        Returns:
            等待时间（秒），0表示无需等待
        """
        with self.lock:
            current_time = time.time()
            
            # 清理过期的请求记录
            while self.request_times and current_time - self.request_times[0] > self.time_window:
                self.request_times.popleft()
            
            # 检查是否需要等待
            if len(self.request_times) >= self.max_requests:
                oldest_request = self.request_times[0]
                wait_time = self.time_window - (current_time - oldest_request) + 0.5  # 额外缓冲0.5秒
                
                if wait_time > 0:
                    # print(f"⏳ {self.name} 速率限制: 等待 {wait_time:.2f}秒...")
                    time.sleep(wait_time)
                    current_time = time.time()
                    
                    # 再次清理过期记录
                    while self.request_times and current_time - self.request_times[0] > self.time_window:
                        self.request_times.popleft()
                    
                    self.request_times.append(current_time)
                    return wait_time
            
            # 记录本次请求时间
            self.request_times.append(current_time)
            return 0.0
    
    def get_current_rate(self) -> int:
        """
        获取当前时间窗口内的请求数
        
        Returns:
            请求数
        """
        with self.lock:
            current_time = time.time()
            # 清理过期记录
            while self.request_times and current_time - self.request_times[0] > self.time_window:
                self.request_times.popleft()
            return len(self.request_times)
    
    def reset(self):
        """重置限制器"""
        with self.lock:
            self.request_times.clear()


class OpenReviewRateLimiter(BaseRateLimiter):
    """OpenReview API 速率限制器"""
    
    def __init__(self, max_requests: int = 58, time_window: int = 60):
        """
        初始化 OpenReview 速率限制器
        
        Args:
            max_requests: 时间窗口内最大请求数（默认58次）
            time_window: 时间窗口大小（默认60秒）
        """
        super().__init__(max_requests, time_window, name="OpenReview")


class GeminiRateLimiter(BaseRateLimiter):
    """Gemini API 速率限制器"""
    
    def __init__(self, max_requests: int = 1000, time_window: int = 60):
        """
        初始化 Gemini 速率限制器
        
        Args:
            max_requests: 时间窗口内最大请求数（默认1000次，Tier 1）
            time_window: 时间窗口大小（默认60秒）
        """
        super().__init__(max_requests, time_window, name="Gemini")


# 装饰器：自动应用速率限制
def rate_limited(limiter: BaseRateLimiter):
    """
    速率限制装饰器
    
    Args:
        limiter: 速率限制器实例
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            limiter.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    return decorator

