"""
统计报告生成模块
生成数据可视化图表和统计摘要
"""

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import logging

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class StatisticsGenerator:
    """统计报告生成器"""
    
    def __init__(self, config):
        """
        初始化统计报告生成器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取配置
        self.enabled_charts = config.get('output', 'statistics', 'charts', default=[])
        
        self.logger.info(f"✅ 统计报告生成器初始化成功 (图表: {len(self.enabled_charts)}个)")
    
    def generate_all(self, df: pd.DataFrame, output_dir: Path):
        """
        生成所有统计报告
        
        Args:
            df: 数据框
            output_dir: 输出目录
        """
        stats_dir = output_dir / "statistics"
        stats_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"📊 正在生成统计报告: {stats_dir}")
        
        # 生成各类图表
        for chart_type in self.enabled_charts:
            try:
                if chart_type == 'rating_distribution':
                    self.generate_rating_distribution(df, stats_dir)
                elif chart_type == 'keyword_wordcloud':
                    self.generate_keyword_wordcloud(df, stats_dir)
                elif chart_type == 'direction_pie':
                    self.generate_direction_pie(df, stats_dir)
            except Exception as e:
                self.logger.warning(f"⚠️  生成 {chart_type} 失败: {e}")
        
        # 生成统计摘要文本
        self.generate_summary_text(df, stats_dir)
        
        self.logger.info(f"✅ 统计报告已生成: {stats_dir}")
    
    def generate_rating_distribution(self, df: pd.DataFrame, output_dir: Path):
        """
        生成评分分布直方图
        
        Args:
            df: 数据框
            output_dir: 输出目录
        """
        if 'Rating' not in df.columns:
            self.logger.warning("⚠️  数据中无 Rating 列，跳过评分分布图")
            return
        
        plt.figure(figsize=(10, 6))
        plt.hist(df['Rating'], bins=20, edgecolor='black', color='#007bff', alpha=0.7)
        plt.xlabel('评分', fontsize=12)
        plt.ylabel('论文数量', fontsize=12)
        plt.title('论文评分分布', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        
        output_path = output_dir / 'rating_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.debug(f"✅ 评分分布图已生成: {output_path}")
    
    def generate_keyword_wordcloud(self, df: pd.DataFrame, output_dir: Path):
        """
        生成关键词词云
        
        Args:
            df: 数据框
            output_dir: 输出目录
        """
        if 'Keywords' not in df.columns:
            self.logger.warning("⚠️  数据中无 Keywords 列，跳过词云图")
            return
        
        # 合并所有关键词
        all_keywords = " ".join(df['Keywords'].dropna().astype(str))
        
        if not all_keywords.strip():
            self.logger.warning("⚠️  关键词为空，跳过词云图")
            return
        
        # 生成词云
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis',
            max_words=100,
            relative_scaling=0.5
        ).generate(all_keywords)
        
        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('关键词词云', fontsize=14, fontweight='bold', pad=20)
        
        output_path = output_dir / 'keyword_wordcloud.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.debug(f"✅ 关键词词云已生成: {output_path}")
    
    def generate_summary_text(self, df: pd.DataFrame, output_dir: Path):
        """
        生成统计摘要文本
        
        Args:
            df: 数据框
            output_dir: 输出目录
        """
        if 'Rating' not in df.columns:
            return
        
        # 计算统计指标
        rating_stats = df['Rating'].describe()
        
        summary = f"""
{'='*60}
             论文分析统计报告
{'='*60}

基本统计:
  - 论文总数:       {len(df)} 篇
  - 平均评分:       {rating_stats['mean']:.2f}
  - 评分标准差:     {rating_stats['std']:.2f}
  - 最高评分:       {rating_stats['max']:.2f}
  - 最低评分:       {rating_stats['min']:.2f}
  - 评分中位数:     {rating_stats['50%']:.2f}
  - 25%分位数:      {rating_stats['25%']:.2f}
  - 75%分位数:      {rating_stats['75%']:.2f}

评分分布:
"""
        
        # 统计各评分区间的论文数
        bins = [0, 3, 5, 6, 7, 8, 10]
        labels = ['0-3', '3-5', '5-6', '6-7', '7-8', '8-10']
        df['Rating_Range'] = pd.cut(df['Rating'], bins=bins, labels=labels)
        rating_counts = df['Rating_Range'].value_counts().sort_index()
        
        for label, count in rating_counts.items():
            percentage = count / len(df) * 100
            summary += f"  - {label}分:        {count:3d} 篇 ({percentage:5.1f}%)\n"
        
        summary += f"\n{'='*60}\n"
        
        # 保存统计摘要
        output_path = output_dir / 'statistics_summary.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        self.logger.debug(f"✅ 统计摘要已生成: {output_path}")

    def generate_direction_pie(self, df: pd.DataFrame, output_dir: Path):
        """
        生成研究方向分布饼图

        Args:
            df: 数据框
            output_dir: 输出目录
        """
        import re

        if 'AI_Analysis' not in df.columns:
            self.logger.warning("⚠️  数据中无 AI_Analysis 列，跳过研究方向饼图")
            return

        # 提取研究方向（从AI分析结果中）
        directions = []

        for analysis in df['AI_Analysis'].dropna():
            # 尝试匹配多种模式
            patterns = [
                r'\*\*具体方向\*\*[：:]\s*([^\n\*]+)',  # **具体方向**: xxx
                r'\*\*研究方向\*\*[：:]\s*([^\n\*]+)',  # **研究方向**: xxx
                r'研究方向[：:]\s*([^\n]+)',           # 研究方向: xxx
                r'方向[：:]\s*([^\n]+)',               # 方向: xxx
            ]

            direction = None
            for pattern in patterns:
                match = re.search(pattern, str(analysis))
                if match:
                    direction = match.group(1).strip()
                    # 清理方向文本（去除多余符号）
                    direction = re.sub(r'[\[\]\(\)（）]', '', direction)
                    direction = direction.split('、')[0]  # 只取第一个方向
                    direction = direction.split('/')[0]   # 只取第一个方向
                    break

            if direction and len(direction) < 50:  # 忽略过长的文本
                directions.append(direction)
            else:
                directions.append('其他')

        if not directions:
            self.logger.warning("⚠️  未能提取研究方向，跳过饼图")
            return

        # 统计方向分布
        from collections import Counter
        direction_counts = Counter(directions)

        # 合并小类别（<3%的归为"其他"）
        total = len(directions)
        threshold = total * 0.03

        major_directions = {}
        other_count = 0

        for direction, count in direction_counts.items():
            if count >= threshold and direction != '其他':
                major_directions[direction] = count
            else:
                other_count += count

        if other_count > 0:
            major_directions['其他'] = other_count

        # 生成饼图
        plt.figure(figsize=(10, 8))
        colors = plt.cm.Set3(range(len(major_directions)))

        wedges, texts, autotexts = plt.pie(
            major_directions.values(),
            labels=major_directions.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10}
        )

        # 美化文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        plt.title('研究方向分布', fontsize=14, fontweight='bold', pad=20)
        plt.axis('equal')

        output_path = output_dir / 'direction_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.debug(f"✅ 研究方向饼图已生成: {output_path}")

