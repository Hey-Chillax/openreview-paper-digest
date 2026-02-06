"""
OpenReview 论文分析爬虫 - 主程序
支持多会议、多年份、自动化分析和多格式输出
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 导入配置和工具模块
from config import load_config
from utils import setup_logger, AuditLogger

# 导入核心功能模块
from core import OpenReviewClient, GeminiClient, PDFProcessor

# 导入分析模块
from analysis import PaperFilter, PromptBuilder

# 导入输出模块
from output import ExcelExporter, HTMLExporter, MarkdownExporter, StatisticsGenerator



def process_single_paper(
    or_client: OpenReviewClient,
    gemini_client: GeminiClient,
    pdf_processor: PDFProcessor,
    paper_filter: PaperFilter,
    prompt_builder: PromptBuilder,
    note,
    config
) -> dict:
    """
    单个论文处理流程

    Args:
        or_client: OpenReview 客户端
        gemini_client: Gemini 客户端
        pdf_processor: PDF 处理器
        paper_filter: 论文筛选器
        prompt_builder: Prompt 构建器
        note: OpenReview note 对象
        config: 配置对象

    Returns:
        论文分析结果字典，如果被筛选掉则返回 None
    """
    try:
        # 1. 提取论文基本信息
        paper_info = or_client.extract_paper_info(note)

        # 2. 关键词筛选
        if not paper_filter.check_keywords(paper_info):
            return None

        # 3. 获取评分并筛选
        rating = or_client.get_paper_rating(note.id)
        filter_reason = paper_filter.filter_paper(paper_info, rating)

        if filter_reason:
            return None

        # 4. 准备分析数据
        mode = config.get_analysis_mode()
        full_text = None

        if mode.upper() == 'FULL':
            # 下载并提取 PDF
            full_text = pdf_processor.extract_with_fallback(
                paper_info['pdf_link'],
                paper_info['abstract'],
                paper_info['tldr']
            )

        # 5. 构建 Prompt 并调用 AI
        prompt = prompt_builder.build_prompt(paper_info, full_text)
        ai_analysis = gemini_client.analyze_paper(prompt)

        # 6. 返回结果
        return {
            'Title': paper_info['title'],
            'Rating': round(rating, 2),
            'Mode': mode,
            'AI_Analysis': ai_analysis,
            'Keywords': ", ".join(paper_info['keywords']),
            'Link': paper_info['link'],
            'PDF': paper_info['pdf_link']
        }

    except Exception as e:
        # 记录错误但不中断流程
        return None


def create_output_directory(config) -> Path:
    """
    创建输出目录

    Args:
        config: 配置对象

    Returns:
        输出目录路径
    """
    # 获取会议信息
    conference = config.get_active_conference()
    mode = config.get_analysis_mode()
    keywords_str = "_".join(config.get_keywords()[:2])  # 使用前两个关键词

    # 生成目录名: ICLR2026_multimodal_SIMPLE_20250115_143022
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{conference['name']}{conference['year']}_{keywords_str}_{mode}_{timestamp}"

    # 创建完整路径
    output_dir = config.get_output_dir() / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def export_results(df: pd.DataFrame, output_dir: Path, config, logger, audit_logger=None, start_time=None):
    """
    导出分析结果到多种格式

    Args:
        df: 结果数据框
        output_dir: 输出目录
        config: 配置对象
        logger: 日志记录器
        audit_logger: 审计日志记录器（可选）
        start_time: 程序开始时间（可选）
    """
    logger.info("📤 正在导出分析结果...")

    # Excel 导出
    if config.is_format_enabled('excel'):
        exporter = ExcelExporter(config)
        excel_path = output_dir / "summary.xlsx"
        exporter.export(df, excel_path)

    # HTML 导出
    if config.is_format_enabled('html'):
        exporter = HTMLExporter(config)
        html_path = output_dir / "report.html"
        exporter.export(df, html_path)

    # Markdown 导出
    if config.is_format_enabled('markdown'):
        exporter = MarkdownExporter(config)
        exporter.export(df, output_dir)

    # CSV 导出（可选）
    if config.get('output', 'formats', 'csv', default=False):
        logger.info("📄 生成CSV文件...")
        csv_path = output_dir / 'summary.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"✅ CSV文件已保存: {csv_path}")

    # 统计报告
    if config.get('output', 'statistics', 'enable', default=False):
        generator = StatisticsGenerator(config)
        generator.generate_all(df, output_dir)

    # 元数据文件
    if audit_logger and start_time:
        logger.info("📋 生成元数据文件...")
        import json
        import time

        conference = config.get_active_conference()
        elapsed_time = time.time() - start_time

        metadata = {
            "conference": {
                "name": conference['name'],
                "year": conference['year'],
                "invitation": conference['invitation']
            },
            "filtering": {
                "keywords": config.get_keywords(),
                "score_threshold": config.get('filtering', 'score_threshold', default=0),
                "use_regex": config.get('filtering', 'use_regex', default=False)
            },
            "analysis": {
                "mode": config.get('analysis', 'mode', default='SIMPLE'),
                "max_pdf_pages": config.get('analysis', 'max_pdf_pages', default=15),
                "max_text_length": config.get('analysis', 'max_text_length', default=40000)
            },
            "statistics": {
                "total_papers": len(df),
                "avg_rating": float(df['Rating'].mean()) if len(df) > 0 else 0,
                "max_rating": float(df['Rating'].max()) if len(df) > 0 else 0,
                "min_rating": float(df['Rating'].min()) if len(df) > 0 else 0,
                "median_rating": float(df['Rating'].median()) if len(df) > 0 else 0
            },
            "execution": {
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
                "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_seconds": round(elapsed_time, 2),
                "openreview_api_calls": audit_logger.api_calls['openreview'],
                "gemini_api_calls": audit_logger.api_calls['gemini'],
                "pdf_downloads_success": audit_logger.pdf_downloaded,
                "pdf_downloads_failed": audit_logger.pdf_failed,
                "errors_count": len(audit_logger.errors)
            },
            "output_formats": {
                "excel": config.is_format_enabled('excel'),
                "html": config.is_format_enabled('html'),
                "markdown": config.is_format_enabled('markdown'),
                "csv": config.get('output', 'formats', 'csv', default=False)
            }
        }

        metadata_path = output_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 元数据文件已保存: {metadata_path}")


def main():
    """主程序入口"""
    import time
    start_time = time.time()  # 记录开始时间

    # 1. 加载配置
    print("🔧 正在加载配置...")
    config = load_config()

    # 2. 设置日志
    logger = setup_logger(config)
    audit_logger = AuditLogger(logger)

    # 3. 显示运行信息
    conference = config.get_active_conference()
    mode = config.get_analysis_mode()
    max_workers = config.get_max_workers()

    logger.info("="*60)
    logger.info("    OpenReview 论文分析爬虫")
    logger.info("="*60)
    logger.info(f"会议: {conference['name']} {conference['year']}")
    logger.info(f"模式: {mode}")
    logger.info(f"关键词: {', '.join(config.get_keywords())}")
    logger.info(f"评分门槛: {config.get_score_threshold()}")
    logger.info(f"并发数: {max_workers}")
    logger.info("="*60)

    try:
        # 4. 初始化客户端
        logger.info("🔗 正在初始化客户端...")
        or_client = OpenReviewClient(config, audit_logger)
        gemini_client = GeminiClient(config, audit_logger)
        pdf_processor = PDFProcessor(config, audit_logger)

        # 5. 初始化分析模块
        paper_filter = PaperFilter(config, audit_logger)
        prompt_builder = PromptBuilder(config)

        # 6. 获取论文列表
        logger.info("📥 正在获取论文列表...")
        submissions = or_client.get_all_submissions(conference['invitation'])
        logger.info(f"✅ 获取到 {len(submissions)} 篇投稿")

        # 7. 并发处理论文
        results = []
        logger.info(f"🔎 开始筛选和分析论文 (并发数: {max_workers})...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(
                    process_single_paper,
                    or_client,
                    gemini_client,
                    pdf_processor,
                    paper_filter,
                    prompt_builder,
                    note,
                    config
                ): note for note in submissions
            }

            # 收集结果
            for future in tqdm(as_completed(futures), total=len(submissions), desc="处理进度"):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        audit_logger.log_paper_processed()
                    else:
                        audit_logger.log_paper_filtered()
                except Exception as e:
                    logger.error(f"处理论文时出错: {e}")
                    audit_logger.log_error("处理论文失败", e)

        # 8. 导出结果
        if results:
            logger.info(f"✅ 筛选出 {len(results)}篇符合条件的论文")

            # 创建数据框并排序
            df = pd.DataFrame(results).sort_values(by='Rating', ascending=False)

            # 创建输出目录
            output_dir = create_output_directory(config)
            logger.info(f"📁 输出目录: {output_dir}")

            # 导出结果
            export_results(df, output_dir, config, logger, audit_logger, start_time)

            # 保存审计报告
            if config.get('logging', 'audit_log', default=True):
                audit_logger.save_report(output_dir)

            logger.info("="*60)
            logger.info("🎉 分析完成！")
            logger.info(f"📊 共筛选出 {len(results)} 篇论文")
            logger.info(f"📁 结果保存在: {output_dir}")
            logger.info("="*60)

            # 打印审计报告
            print(audit_logger.generate_report())
        else:
            logger.warning("="*60)
            logger.warning("❌ 未找到符合条件的论文")
            logger.warning("建议:")
            logger.warning("  1. 降低评分门槛 (当前: {})".format(config.get_score_threshold()))
            logger.warning("  2. 调整关键词列表")
            logger.warning("  3. 检查会议配置是否正确")
            logger.warning("="*60)

    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}", exc_info=True)
        audit_logger.log_error("程序执行失败", e)
        raise


if __name__ == "__main__":
    main()