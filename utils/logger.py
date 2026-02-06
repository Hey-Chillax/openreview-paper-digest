"""
日志配置模块
提供统一的日志记录功能和审计日志
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


def setup_logger(config) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        config: 配置对象
    
    Returns:
        配置好的Logger实例
    """
    # 创建日志目录
    log_file = Path(config.get('logging', 'file', default='logs/openreview_crawler.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 获取日志级别
    log_level = config.get('logging', 'level', default='INFO')
    
    # 创建logger
    logger = logging.getLogger('openreview_crawler')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除已有的处理器（避免重复）
    logger.handlers.clear()
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    if config.get('logging', 'console', default=True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


class AuditLogger:
    """审计日志记录器 - 记录操作统计和性能指标"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化审计日志
        
        Args:
            logger: 日志记录器实例
        """
        self.logger = logger
        self.start_time = time.time()
        self.api_calls: Dict[str, int] = {
            'openreview': 0,
            'gemini': 0
        }
        self.errors = []
        self.papers_processed = 0
        self.papers_filtered = 0
        self.pdf_downloaded = 0
        self.pdf_failed = 0
    
    def log_api_call(self, api_name: str):
        """
        记录API调用
        
        Args:
            api_name: API名称 ('openreview' 或 'gemini')
        """
        if api_name in self.api_calls:
            self.api_calls[api_name] += 1
    
    def log_error(self, error_msg: str, exception: Optional[Exception] = None):
        """
        记录错误
        
        Args:
            error_msg: 错误消息
            exception: 异常对象（可选）
        """
        error_info = {
            'time': datetime.now().isoformat(),
            'message': error_msg,
            'exception': str(exception) if exception else None
        }
        self.errors.append(error_info)
        
        if self.logger:
            if exception:
                self.logger.error(f"{error_msg}: {exception}")
            else:
                self.logger.error(error_msg)
    
    def log_paper_processed(self):
        """记录处理了一篇论文"""
        self.papers_processed += 1
    
    def log_paper_filtered(self):
        """记录筛选掉一篇论文"""
        self.papers_filtered += 1
    
    def log_pdf_download(self, success: bool):
        """
        记录PDF下载结果
        
        Args:
            success: 是否成功
        """
        if success:
            self.pdf_downloaded += 1
        else:
            self.pdf_failed += 1
    
    def get_elapsed_time(self) -> float:
        """
        获取运行时间
        
        Returns:
            运行时间（秒）
        """
        return time.time() - self.start_time
    
    def generate_report(self) -> str:
        """
        生成审计报告
        
        Returns:
            审计报告文本
        """
        elapsed = self.get_elapsed_time()
        minutes, seconds = divmod(int(elapsed), 60)
        
        report = f"""
{'='*60}
                  审计报告
{'='*60}
运行时间: {minutes}分{seconds}秒 ({elapsed:.2f}秒)

API调用统计:
  - OpenReview API: {self.api_calls['openreview']}次
  - Gemini API:     {self.api_calls['gemini']}次

论文处理统计:
  - 已处理论文:     {self.papers_processed}篇
  - 筛选掉的论文:   {self.papers_filtered} 篇
  - 成功率:         {self.papers_processed / max(1, self.papers_processed + self.papers_filtered) * 100:.1f}%

PDF下载统计:
  - 成功下载:       {self.pdf_downloaded} 个
  - 下载失败:       {self.pdf_failed} 个
  - 成功率:         {self.pdf_downloaded / max(1, self.pdf_downloaded + self.pdf_failed) * 100:.1f}%

错误统计:
  - 错误总数:       {len(self.errors)} 个
{'='*60}
"""
        
        if self.errors:
            report += "\n最近的错误:\n"
            for i, error in enumerate(self.errors[-5:], 1):  # 只显示最近5个错误
                report += f"  {i}. [{error['time']}] {error['message']}\n"
        
        return report
    
    def save_report(self, output_dir: Path):
        """
        保存审计报告到文件
        
        Args:
            output_dir: 输出目录
        """
        report_file = output_dir / "audit_log.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())
        
        if self.logger:
            self.logger.info(f"审计报告已保存至: {report_file}")

