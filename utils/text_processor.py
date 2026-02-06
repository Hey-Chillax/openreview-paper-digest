"""
文本处理工具模块
提供关键词匹配、文件名清理等功能
"""

import re
from typing import List


class KeywordMatcher:
    """关键词匹配器"""
    
    def __init__(self, keywords: List[str], use_regex: bool = True):
        """
        初始化关键词匹配器
        
        Args:
            keywords: 关键词列表
            use_regex: 是否使用正则表达式（词边界匹配）
        """
        self.keywords = keywords
        self.use_regex = use_regex
        
        if use_regex:
            # 预编译正则表达式以提高性能
            self.patterns = [
                re.compile(r'\b' + re.escape(kw.lower()) + r'\b', re.IGNORECASE)
                for kw in keywords
            ]
        else:
            # 简单匹配：转换为小写
            self.keywords_lower = [kw.lower() for kw in keywords]
    
    def match(self, text: str) -> bool:
        """
        检查文本是否匹配任一关键词
        
        Args:
            text: 待匹配的文本
        
        Returns:
            是否匹配
        """
        if not text:
            return False
        
        if self.use_regex:
            # 使用正则表达式匹配（词边界）
            return any(pattern.search(text) for pattern in self.patterns)
        else:
            # 简单字符串匹配
            text_lower = text.lower()
            return any(kw in text_lower for kw in self.keywords_lower)
    
    def find_matched_keywords(self, text: str) -> List[str]:
        """
        找出文本中匹配的所有关键词
        
        Args:
            text: 待匹配的文本
        
        Returns:
            匹配的关键词列表
        """
        if not text:
            return []
        
        matched = []
        
        if self.use_regex:
            for i, pattern in enumerate(self.patterns):
                if pattern.search(text):
                    matched.append(self.keywords[i])
        else:
            text_lower = text.lower()
            for kw in self.keywords:
                if kw.lower() in text_lower:
                    matched.append(kw)
        
        return matched


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        max_length: 最大长度
    
    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    cleaned = re.sub(illegal_chars, '_', filename)
    
    # 移除首尾空格和点号
    cleaned = cleaned.strip('. ')
    
    # 限制长度
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    # 如果为空，使用默认名称
    if not cleaned:
        cleaned = "untitled"
    
    return cleaned


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后添加的后缀
    
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_summary(text: str, max_length: int = 200) -> str:
    """
    提取文本摘要（前N个字符，智能断句）
    
    Args:
        text: 原始文本
        max_length: 最大长度
    
    Returns:
        摘要文本
    """
    if not text or len(text) <= max_length:
        return text
    
    # 截取到最大长度
    truncated = text[:max_length]
    
    # 尝试在句号、换行符处截断
    for delimiter in ['\n\n', '\n', '。', '. ', '！', '? ']:
        last_delimiter = truncated.rfind(delimiter)
        if last_delimiter > max_length * 0.7:  # 至少保留70%的内容
            return truncated[:last_delimiter + len(delimiter)].strip() + "\n..."
    
    # 如果找不到合适的断句点，直接截断
    return truncated + "..."


def clean_whitespace(text: str) -> str:
    """
    清理文本中的多余空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        清理后的文本
    """
    # 移除行首行尾空白
    text = text.strip()
    
    # 合并多个空格为一个
    text = re.sub(r' +', ' ', text)
    
    # 合并多个换行符为最多两个
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

