"""
HTML 导出模块
生成带 Markdown 渲染的 HTML 报告
"""

import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
import markdown
import logging


class HTMLExporter:
    """HTML 导出器"""
    
    def __init__(self, config):
        """
        初始化 HTML 导出器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取会议信息
        conference = config.get_active_conference()
        self.conference_name = conference['name']
        self.conference_year = conference['year']
        
        # 初始化 Jinja2 环境
        template_dir = Path('templates')
        if template_dir.exists():
            self.env = Environment(loader=FileSystemLoader('templates'))
        else:
            self.env = None
        
        self.logger.info("✅ HTML 导出器初始化成功")
    
    def export(self, df: pd.DataFrame, output_path: Path) -> Path:
        """
        导出 HTML 报告
        
        Args:
            df: 数据框
            output_path: 输出文件路径
        
        Returns:
            实际保存的文件路径
        """
        self.logger.info(f"📄 正在生成 HTML 报告: {output_path}")
        
        # 准备数据
        papers = df.to_dict('records')
        
        # 渲染 Markdown 为 HTML
        for paper in papers:
            if 'AI_Analysis' in paper and paper['AI_Analysis']:
                paper['AI_Analysis_HTML'] = markdown.markdown(
                    paper['AI_Analysis'],
                    extensions=['extra', 'codehilite', 'tables']
                )
            else:
                paper['AI_Analysis_HTML'] = "<p>无分析内容</p>"
        
        # 计算统计信息
        stats = {
            'total_count': len(papers),
            'avg_rating': df['Rating'].mean() if 'Rating' in df.columns else 0,
            'max_rating': df['Rating'].max() if 'Rating' in df.columns else 0,
            'min_rating': df['Rating'].min() if 'Rating' in df.columns else 0,
        }
        
        # 使用模板或默认模板
        if self.env and self._template_exists('report_template.html'):
            template = self.env.get_template('report_template.html')
        else:
            template = Template(self._get_default_template())
        
        # 渲染 HTML
        from datetime import datetime
        html_content = template.render(
            papers=papers,
            conference_name=self.conference_name,
            conference_year=self.conference_year,
            stats=stats,
            now=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 保存文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"✅ HTML 报告已保存: {output_path}")
        return output_path
    
    def _template_exists(self, template_name: str) -> bool:
        """检查模板是否存在"""
        return (Path('templates') / template_name).exists()
    
    def _get_default_template(self) -> str:
        """获取默认的 HTML 模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ conference_name }} {{ conference_year }} 论文分析报告</title>

    <!-- MathJax 3 配置和加载 -->
    <script>
        MathJax = {
            tex: {
                inlineMath: [['$', '$']],
                displayMath: [['$$', '$$']],
                processEscapes: true,
                processEnvironments: true
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }
        };
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>

    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        .stats {
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .stats p { margin: 5px 0; }
        .paper {
            border: 1px solid #ddd;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            background: #fafafa;
        }
        .paper-title {
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .paper-meta {
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
        }
        .rating {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 3px 10px;
            border-radius: 3px;
            font-weight: bold;
        }
        .keywords {
            color: #28a745;
            font-style: italic;
        }
        .analysis {
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-left: 4px solid #007bff;
        }
        .links {
            margin-top: 10px;
        }
        .links a {
            color: #007bff;
            text-decoration: none;
            margin-right: 15px;
        }
        .links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ conference_name }}{{ conference_year }} 论文分析报告</h1>
        
        <div class="stats">
            <p><strong>论文总数:</strong> {{ stats.total_count }}篇</p>
            <p><strong>平均评分:</strong> {{ "%.2f"|format(stats.avg_rating) }}</p>
            <p><strong>评分范围:</strong> {{ "%.2f"|format(stats.min_rating) }}- {{ "%.2f"|format(stats.max_rating) }}</p>
        </div>
        
        {% for paper in papers %}
        <div class="paper">
            <div class="paper-title">{{ paper.Title }}</div>
            <div class="paper-meta">
                <span class="rating">评分: {{ paper.Rating }}</span>
                {% if paper.Keywords %}
                <span class="keywords">关键词: {{ paper.Keywords }}</span>
                {% endif %}
            </div>
            
            <div class="analysis">
                {{ paper.AI_Analysis_HTML | safe }}
            </div>
            
            <div class="links">
                <a href="{{ paper.Link }}" target="_blank">🔗 查看原文</a>
                <a href="{{ paper.PDF }}" target="_blank">📄 下载PDF</a>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
        """

