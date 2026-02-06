# OpenReview 论文分析爬虫

一个功能强大的 OpenReview 论文爬虫工具，支持多会议、多年份、自动化分析和多格式输出。

## ✨ 主要特性

- 🎯 **多会议支持**：支持 ICLR、NeurIPS、ICML、CVPR 等多个顶会
- 📊 **多格式输出**：Excel、HTML、Markdown 三种格式，满足不同需求
- 🤖 **AI 智能分析**：集成 Gemini AI，自动生成论文分析报告
- 🔍 **灵活筛选**：支持关键词匹配、评分门槛、正则表达式等多种筛选方式
- 📈 **数据可视化**：自动生成评分分布图、关键词词云等统计图表
- ⚡ **高效并发**：多线程处理，支持速率限制，避免 API 限流
- 🛠️ **模块化设计**：清晰的代码结构，易于维护和扩展

## 📦 项目结构

```
openreview/
├── main.py                    # 主程序入口
├── config.yaml                # 配置文件
├── config.py                  # 配置加载模块
├── .env.example               # 环境变量模板
├── utils/                     # 工具模块
│   ├── rate_limiter.py       # API速率限制器
│   ├── logger.py             # 日志配置
│   └── text_processor.py     # 文本处理工具
├── core/                      # 核心功能模块
│   ├── openreview_client.py  # OpenReview API封装
│   ├── gemini_client.py      # Gemini API封装
│   └── pdf_processor.py      # PDF下载和解析
├── analysis/                  # 分析模块
│   ├── paper_filter.py       # 论文筛选逻辑
│   └── prompt_builder.py     # Prompt构建器
├── output/                    # 输出模块
│   ├── excel_exporter.py     # Excel导出
│   ├── html_exporter.py      # HTML报告生成
│   ├── markdown_exporter.py  # Markdown归档
│   └── statistics_generator.py  # 统计报告生成
├── templates/                 # HTML模板
│   └── report_template.html
├── analyses/                  # 输出目录（自动创建）
└── logs/                      # 日志目录（自动创建）
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- uv (推荐) 或 pip

### 2. 安装依赖

使用 uv（推荐）：
```bash
uv sync
```

或使用 pip：
```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

方法一：创建 `.env` 文件
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 Gemini API Key
```

方法二：直接修改 `config.yaml`
```yaml
api:
  gemini_api_key: "your_gemini_api_key_here"
```

### 4. 运行程序

```bash
uv run main.py
```

## ⚙️ 配置说明

所有配置都在 `config.yaml` 文件中，主要配置项说明：

### 会议配置

```yaml
conferences:
  - name: "ICLR"
    year: 2026
    invitation: "ICLR.cc/2026/Conference/-/Submission"

active_conference_index: 0  # 当前使用的会议（0表示第一个）
```

### 筛选条件

```yaml
filtering:
  keywords:
    - "multimodal"
    - "MLLM"
    - "VLM"
  score_threshold: 6.0  # 评分门槛
  use_regex: true       # 使用词边界匹配
```

### 分析模式

```yaml
analysis:
  mode: "SIMPLE"  # "SIMPLE" (快速) 或 "FULL" (深度)
  max_pdf_pages: 15
  max_text_length: 40000
```

### 输出格式

```yaml
output:
  formats:
    excel: true
    html: true
    markdown: true
  statistics:
    enable: true
```

## 📂 输出文件说明

运行成功后，会在 `analyses/` 目录下生成以下文件：

```
analyses/ICLR2026_multimodal_SIMPLE_20250115_143022/
├── summary.xlsx           # Excel摘要（AI分析前200字）
├── report.html            # HTML完整报告（推荐阅读）
├── papers/                # Markdown归档文件夹
│   ├── README.md          # 论文索引
│   ├── paper_001_xxx.md   # 各篇论文详细分析
│   └── ...
├── statistics/            # 统计报告
│   ├── rating_distribution.png     # 评分分布图
│   ├── keyword_wordcloud.png       # 关键词词云
│   └── statistics_summary.txt      # 统计摘要
├── audit_log.txt          # 操作审计日志
└── metadata.json          # 运行元数据（可选）
```

## 🎨 使用示例

### 示例1：爬取 ICLR 2026 多模态论文

1. 修改 `config.yaml`：
```yaml
active_conference_index: 0  # ICLR
filtering:
  keywords: ["multimodal", "MLLM", "VLM"]
  score_threshold: 6.0
```

2. 运行：
```bash
uv run main.py
```

### 示例2：爬取 NeurIPS 2025 论文（FULL模式）

1. 修改 `config.yaml`：
```yaml
active_conference_index: 1  # NeurIPS
analysis:
  mode: "FULL"  # 下载PDF全文分析
```

2. 运行：
```bash
uv run main.py
```

## 📊 输出格式对比

| 格式 | 优点 | 适用场景 |
|------|------|----------|
| Excel | 快速浏览、排序筛选 | 初步筛选论文 |
| HTML | 完整内容、Markdown渲染、阅读体验好 | 详细阅读分析 |
| Markdown | 版本控制友好、易于编辑 | 归档和二次整理 |

## 🔧 高级功能

### 1. 自定义 Prompt 模板

在 `config.yaml` 中修改 `prompts` 部分：

```yaml
prompts:
  simple_mode: |
    作为 AI 研究员，请分析以下论文...
  full_mode: |
    请阅读以下论文全文...
```

### 2. 调整速率限制

```yaml
rate_limit:
  openreview:
    max_requests: 58
    time_window: 60
  gemini:
    max_requests: 1000
    time_window: 60
```

### 3. 自定义日志级别

```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
  console: true
  audit_log: true
```

## 🐛 常见问题

### Q1: 提示"请配置有效的 GEMINI_API_KEY"

**A:** 请确保在 `.env` 文件或 `config.yaml` 中正确配置了 API Key。

### Q2: 未找到符合条件的论文

**A:** 尝试以下解决方案：
- 降低 `score_threshold`（如改为 5.0）
- 调整 `keywords` 列表
- 检查 `invitation` 配置是否正确

### Q3: PDF 下载失败

**A:** 这是正常现象，程序会自动使用 abstract 和 tldr 作为备选文本。

### Q4: 词云图中文显示为方框

**A:** 需要安装中文字体，或修改 `statistics_generator.py` 中的字体配置。

##贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [OpenReview](https://openreview.net/) - 论文数据源
- [Google Gemini](https://ai.google.dev/) - AI 分析引擎

---

**Happy Paper Reading! 📚✨**

