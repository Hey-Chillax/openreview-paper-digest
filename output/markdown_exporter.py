"""
Markdown 导出模块
为每篇论文生成独立的 Markdown 文件
"""

import pandas as pd
from pathlib import Path
from utils.text_processor import sanitize_filename
import logging


class MarkdownExporter:
    """Markdown 导出器"""
    
    def __init__(self, config):
        """
        初始化 Markdown 导出器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取会议信息
        conference = config.get_active_conference()
        self.conference_name = conference['name']
        self.conference_year = conference['year']
        
        self.logger.info("✅ Markdown 导出器初始化成功")
    
    def export(self, df: pd.DataFrame, output_dir: Path) -> Path:
        """
        导出 Markdown 文件
        
        Args:
            df: 数据框
            output_dir: 输出目录
        
        Returns:
            papers 子目录路径
        """
        papers_dir = output_dir / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"📝 正在生成 Markdown 文件: {papers_dir}")
        
        # 生成每篇论文的 Markdown 文件
        for idx, row in df.iterrows():
            self._export_single_paper(row, idx, papers_dir)
        
        # 生成索引文件
        self._generate_index(df, papers_dir)
        
        self.logger.info(f"✅ Markdown 文件已保存: {papers_dir} (共 {len(df)}篇)")
        return papers_dir
    
    def _export_single_paper(self, row: pd.Series, index: int, output_dir: Path):
        """
        导出单篇论文的 Markdown 文件
        
        Args:
            row: 论文数据行
            index: 索引
            output_dir: 输出目录
        """
        # 生成文件名
        title_short = sanitize_filename(row['Title'], max_length=40)
        filename = f"paper_{index+1:03d}_{title_short}.md"
        filepath = output_dir / filename
        
        # 生成 Markdown 内容
        content = self._format_paper_markdown(row, index + 1)
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _format_paper_markdown(self, row: pd.Series, paper_number: int) -> str:
        """
        格式化论文为 Markdown 内容
        
        Args:
            row: 论文数据行
            paper_number: 论文编号
        
        Returns:
            Markdown 内容
        """
        content = f"""# {row['Title']}

---

## 📋 基本信息

- **论文编号**: #{paper_number:03d}
- **会议**: {self.conference_name} {self.conference_year}
- **评分**: {row['Rating']:.2f}
- **分析模式**: {row.get('Mode', 'N/A')}
- **关键词**: {row.get('Keywords', 'N/A')}

## 🔗 链接

- **OpenReview**: [{row['Link']}]({row['Link']})
- **PDF**: [{row['PDF']}]({row['PDF']})

---

## 🤖 AI 分析

{row.get('AI_Analysis', '无分析内容')}

---

*生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return content
    
    def _generate_index(self, df: pd.DataFrame, output_dir: Path):
        """
        生成索引文件 README.md
        
        Args:
            df: 数据框
            output_dir: 输出目录
        """
        index_path = output_dir / "README.md"
        
        # 按评分降序排列
        df_sorted = df.sort_values(by='Rating', ascending=False)
        
        # 生成索引内容
        content = f"""# {self.conference_name}{self.conference_year} 论文分析索引

共收录 **{len(df)}** 篇论文

---

## 📊 统计信息

- **平均评分**: {df['Rating'].mean():.2f}
- **最高评分**: {df['Rating'].max():.2f}
- **最低评分**: {df['Rating'].min():.2f}
- **评分中位数**: {df['Rating'].median():.2f}

---

## 📑 论文列表

| # | 标题 | 评分 | 文件 |
|---|------|------|------|
"""
        
        # 添加论文列表
        for idx, row in df_sorted.iterrows():
            title_short = sanitize_filename(row['Title'], max_length=40)
            filename = f"paper_{idx+1:03d}_{title_short}.md"
            
            # 截断标题用于显示
            display_title = row['Title'][:60] + '...' if len(row['Title']) > 60 else row['Title']
            
            content += f"| {idx+1:03d} | {display_title} | {row['Rating']:.2f} | [{filename}]({filename}) |\n"
        
        content += f"""
---

*生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 保存索引文件
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.debug(f"✅ 索引文件已生成: {index_path}")

