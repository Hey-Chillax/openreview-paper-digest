"""
PDF下载和解析模块
提供PDF文本提取功能
"""

import io
import requests
import pypdf
from typing import Optional
from utils.logger import AuditLogger
import logging


class PDFProcessor:
    """PDF 处理器"""
    
    def __init__(self, config, audit_logger: Optional[AuditLogger] = None):
        """
        初始化 PDF 处理器
        
        Args:
            config: 配置对象
            audit_logger: 审计日志记录器
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取配置
        self.max_pages = config.get('analysis', 'max_pdf_pages', default=15)
        self.timeout = config.get('analysis', 'pdf_timeout', default=15)
        
        self.logger.info(f"✅ PDF 处理器初始化成功 (最大页数: {self.max_pages}, 超时: {self.timeout}秒)")
    
    def download_and_extract(self, pdf_url: str) -> Optional[str]:
        """
        下载并提取 PDF 文本
        
        Args:
            pdf_url: PDF 下载链接
        
        Returns:
            提取的文本，失败则返回 None
        """
        try:
            # 下载 PDF
            self.logger.debug(f"📥 正在下载 PDF: {pdf_url}")
            response = requests.get(pdf_url, stream=True, timeout=self.timeout)
            
            if response.status_code != 200:
                self.logger.warning(f"⚠️  PDF 下载失败 (状态码: {response.status_code})")
                if self.audit_logger:
                    self.audit_logger.log_pdf_download(False)
                return None
            
            # 解析 PDF
            pdf_file = io.BytesIO(response.content)
            reader = pypdf.PdfReader(pdf_file)
            
            # 提取文本（使用列表拼接优化）
            text_parts = []
            page_limit = min(len(reader.pages), self.max_pages)
            
            for i in range(page_limit):
                try:
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    self.logger.debug(f"⚠️  提取第 {i+1}页失败: {e}")
                    continue
            
            if not text_parts:
                self.logger.warning("⚠️  PDF 文本提取为空")
                if self.audit_logger:
                    self.audit_logger.log_pdf_download(False)
                return None
            
            text = "\n".join(text_parts)
            
            # 记录成功
            if self.audit_logger:
                self.audit_logger.log_pdf_download(True)
            
            self.logger.debug(f"✅ PDF 文本提取成功 (共 {page_limit} 页, {len(text)} 字符)")
            return text
        
        except requests.Timeout:
            self.logger.warning(f"⚠️  PDF 下载超时: {pdf_url}")
            if self.audit_logger:
                self.audit_logger.log_pdf_download(False)
            return None
        
        except Exception as e:
            self.logger.warning(f"⚠️  PDF 处理失败: {e}")
            if self.audit_logger:
                self.audit_logger.log_pdf_download(False)
                self.audit_logger.log_error(f"PDF处理失败: {pdf_url}", e)
            return None
    
    def extract_with_fallback(self, pdf_url: str, abstract: str, tldr: str) -> str:
        """
        提取 PDF 文本，失败时使用 abstract 和 tldr 作为备选
        
        Args:
            pdf_url: PDF 下载链接
            abstract: 论文摘要
            tldr: 论文 TL;DR
        
        Returns:
            提取的文本或备选文本
        """
        pdf_text = self.download_and_extract(pdf_url)
        
        if pdf_text:
            return pdf_text
        
        # PDF 提取失败，使用备选文本
        fallback_text = f"Abstract: {abstract}\n\nTL;DR: {tldr}"
        self.logger.debug("ℹ️  使用 abstract 和 tldr 作为备选文本")
        return fallback_text

