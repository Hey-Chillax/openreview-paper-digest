"""
Excel 导出模块
生成格式化的 Excel 报告
"""

import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from utils.text_processor import extract_summary
import logging


class ExcelExporter:
    """Excel 导出器"""
    
    def __init__(self, config):
        """
        初始化 Excel 导出器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger('openreview_crawler')
        
        # 获取配置
        self.summary_length = config.get('output', 'excel', 'summary_length', default=200)
        self.auto_adjust_width = config.get('output', 'excel', 'auto_adjust_width', default=True)
        self.enable_wrap_text = config.get('output', 'excel', 'enable_wrap_text', default=True)
        
        self.logger.info(f"✅ Excel 导出器初始化成功 (摘要长度: {self.summary_length}字符)")
    
    def export(self, df: pd.DataFrame, output_path: Path) -> Path:
        """
        导出 Excel 文件
        
        Args:
            df: 数据框
            output_path: 输出文件路径
        
        Returns:
            实际保存的文件路径
        """
        self.logger.info(f"📊 正在生成 Excel 文件: {output_path}")
        
        # 准备数据：添加摘要列
        df_export = df.copy()
        
        if 'AI_Analysis' in df_export.columns:
            # 创建摘要列
            df_export['AI_Analysis_Summary'] = df_export['AI_Analysis'].apply(
                lambda x: extract_summary(x, self.summary_length) + "\n\n[完整内容请查看HTML报告]"
            )
            
            # 调整列顺序：将摘要列放在 AI_Analysis 后面
            cols = df_export.columns.tolist()
            ai_index = cols.index('AI_Analysis')
            cols.insert(ai_index + 1, cols.pop(cols.index('AI_Analysis_Summary')))
            df_export = df_export[cols]
        
        # 导出 Excel
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_export.to_excel(output_path, index=False, engine='openpyxl')
        
        # 格式化 Excel
        if self.auto_adjust_width or self.enable_wrap_text:
            self._format_excel(output_path)
        
        self.logger.info(f"✅ Excel 文件已保存: {output_path}")
        return output_path
    
    def _format_excel(self, file_path: Path):
        """
        格式化 Excel 文件
        
        Args:
            file_path: Excel 文件路径
        """
        try:
            wb = load_workbook(file_path)
            ws = wb.active
            
            # 设置列宽
            if self.auto_adjust_width:
                column_widths = {
                    'A': 50,   # Title
                    'B': 10,   # Rating
                    'C': 15,   # Mode
                    'D': 80,   # AI_Analysis
                    'E': 80,   # AI_Analysis_Summary
                    'F': 30,   # Keywords
                    'G': 50,   # Link
                    'H': 50    # PDF
                }
                
                for col_letter, width in column_widths.items():
                    if col_letter in ws.column_dimensions:
                        ws.column_dimensions[col_letter].width = width
            
            # 启用文本换行和对齐
            if self.enable_wrap_text:
                for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
                    for cell in row:
                        cell.alignment = Alignment(
                            wrap_text=True,
                            vertical='top',
                            horizontal='left'
                        )
            
            # 设置标题行样式
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 设置行高（自动）
            for row in range(2, ws.max_row + 1):
                ws.row_dimensions[row].height = None  # 自动调整
            
            wb.save(file_path)
            self.logger.debug("✅ Excel 格式化完成")
        
        except Exception as e:
            self.logger.warning(f"⚠️  Excel 格式化失败: {e}")

