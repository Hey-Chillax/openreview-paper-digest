# OpenReview 论文筛选与 AI 解读

从 OpenReview 拉取顶会投稿，按关键词和审稿均分筛选，再调用 Gemini 逐篇解读，输出 Excel、HTML、Markdown 报告和统计图。

以 2026 年 2 月的一次运行为例：ICLR 2026 共 18,949 篇投稿，用仓库里的默认配置（6 个关键词、均分 ≥ 5.0、FULL 模式）筛出 121 篇，全程约 18 分钟，121 篇 PDF 全部解析成功。

## 工作流程

1. **拉取投稿**：通过 OpenReview API 读取会议的全部投稿（需要登录，见下文）。
2. **关键词筛选**：在标题和作者关键词中匹配，不区分大小写，命中任意一个即保留。
3. **评分筛选**：读取论文下所有公开审稿意见的 `rating`，取平均分，低于门槛的跳过。没有公开评分的论文一律跳过（门槛设为 0 也一样）。
4. **AI 解读**：
   - `SIMPLE`：只把标题和 TL;DR 发给模型（不含摘要），快速提炼要点；
   - `FULL`：下载 PDF，解析前 15 页、截取前 100,000 字符发给模型做深度剖析；PDF 下载或解析失败时改用摘要和 TL;DR。
5. **导出**：Excel 摘要、HTML 完整报告、逐篇 Markdown、统计图、审计日志和运行元数据。

论文处理是多线程并发的，OpenReview 和 Gemini 各自限速，Gemini 调用失败会指数退避重试。

## 快速开始

### 1. 安装

需要 Python ≥ 3.12 和 [uv](https://docs.astral.sh/uv/)（没有的话先 `pip install uv`）。在仓库根目录执行：

```bash
uv sync
```

### 2. 配置凭据

凭据都通过环境变量传入，不要写进仓库：

| 环境变量 | 用途 |
|---|---|
| `GEMINI_API_KEY` | Gemini API Key，在 [Google AI Studio](https://aistudio.google.com/apikey) 创建 |
| `OPENREVIEW_USERNAME` | OpenReview 登录邮箱 |
| `OPENREVIEW_PASSWORD` | OpenReview 密码 |
| `OPENREVIEW_TOTP_SECRET` | 可选，OpenReview 两步验证的 TOTP 密钥，见下文方案二 |

Linux / macOS：

```bash
export GEMINI_API_KEY="..."
export OPENREVIEW_USERNAME="..."
export OPENREVIEW_PASSWORD="..."
```

Windows PowerShell：

```powershell
$env:GEMINI_API_KEY = "..."
$env:OPENREVIEW_USERNAME = "..."
$env:OPENREVIEW_PASSWORD = "..."
```

- OpenReview 目前不允许匿名读取论文，不登录会返回 `403 ChallengeRequiredError`。openreview-py 读到 `OPENREVIEW_USERNAME` 和 `OPENREVIEW_PASSWORD` 会自动登录，登录有效期 1 周。
- `GEMINI_API_KEY` 的优先级高于 `config.yaml` 里的 `api.gemini_api_key`。也可以把 key 直接填进 `config.yaml`，但那样就不要再提交这个文件。
- 不想每次手动 `export`，可以把这几行写进仓库之外、只有自己能读的文件（如 `~/.config/openreview/credentials.env`，`chmod 600`），运行前 `source` 一下。

#### 账号开了两步验证时

OpenReview 账号开了身份验证器（TOTP）两步验证的话，登录时还需要 6 位验证码。有两种处理方式。

**方案一：在终端里手动输入（推荐）**

不需要额外配置。程序启动登录时会提示：

```
Multi-factor authentication is required.
Using method: totp
Enter TOTP code from your authenticator app:
```

输入身份验证器 App 里当前的验证码即可，每次运行只在开始时输一次。限制是必须在开着的交互式终端里运行，不能放到后台（`nohup`、`&`）或定时任务里，否则会报 `MfaRequiredError ... Interactive login required (TTY)`。

**方案二：设置 TOTP 密钥，自动生成验证码**

把开启两步验证时拿到的密钥设为环境变量 `OPENREVIEW_TOTP_SECRET`，程序会用它自动生成验证码，可以在后台或定时任务里运行：

```bash
export OPENREVIEW_TOTP_SECRET="..."          # Windows PowerShell：$env:OPENREVIEW_TOTP_SECRET = "..."
```

- 密钥是一串 Base32 字符：开启两步验证时可以手动输入身份验证器的那串字符，也就是二维码里 `otpauth://` 链接的 `secret=` 参数。中间带空格也没关系。
- 当初没保存这个密钥的话，需要在 OpenReview 里关闭再重新开启两步验证，并用身份验证器 App 重新扫码。
- 风险：密钥和密码存在一起后，拿到这几个变量的人就能直接登录你的账号，两步验证不再起保护作用。只在确实需要无人值守运行时使用，并把它们存放在仓库之外、只有自己能读的地方。

### 3. 运行

在仓库根目录执行（`config.yaml` 和 `templates/` 按相对路径读取）：

```bash
uv run main.py
```

结果写入 `analyses/`，日志写入 `logs/`。

## 配置说明

所有配置都在 `config.yaml` 中，下表是仓库里的默认值。

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `api.gemini_model` | `gemini-3-pro-preview` | Google 已于 2026-03-09 下线这个预览版，该名字现在自动指向 `gemini-3.1-pro-preview`；想更快更省可换 `gemini-3.5-flash` |
| `conferences` | ICLR 2026、NeurIPS 2025、ICML 2025、CVPR 2025 | 每项是会议名、年份和 OpenReview 的 `invitation` |
| `active_conference_index` | `0` | 本次运行哪个会议，按上面列表的下标选，`0` 即 ICLR 2026 |
| `filtering.keywords` | `TTT`、`Test-Time Training`、`TTS`、`Test-time Scaling`、`in-context learning`、`context learning` | 按字面匹配，不支持正则语法 |
| `filtering.score_threshold` | `5.0` | 审稿均分门槛 |
| `filtering.use_regex` | `true` | `true` 按整词匹配（`TTS` 不会命中 `TTSR`），`false` 按子串匹配 |
| `analysis.mode` | `FULL` | `SIMPLE` 或 `FULL`，见上文 |
| `analysis.max_pdf_pages` | `15` | FULL 模式解析的 PDF 页数 |
| `analysis.max_text_length` | `100000` | 发给模型的正文字符数上限 |
| `analysis.pdf_timeout` | `15` | PDF 下载超时（秒） |
| `concurrency.max_workers` | `10` | 并发线程数 |
| `rate_limit.openreview` | 每 60 秒 58 次 | |
| `rate_limit.gemini` | 每 60 秒 1000 次 | 按 Gemini 付费 Tier 1 配额设置；用免费额度时请调低，并减小 `max_workers` |
| `retry` | 最多 3 次，基础间隔 0.5 秒 | Gemini 调用失败时指数退避 |
| `output.formats` | Excel、HTML、Markdown 开，CSV 关 | |
| `output.excel.summary_length` | `500` | Excel 里每篇 AI 解读保留的字符数 |
| `output.statistics.charts` | 评分分布、关键词词云、研究方向饼图 | 研究方向从 AI 解读的「细分领域」一项提取 |
| `logging` | `INFO`，写入 `logs/openreview_crawler.log` | `audit_log: true` 时在输出目录写 `audit_log.txt` |

### 自定义 Prompt

`prompts.simple_mode` 和 `prompts.full_mode` 是两套模板，用 Python 的 `str.format` 填充：

- `simple_mode` 可用 `{conference}`、`{year}`、`{title}`、`{tldr}`；
- `full_mode` 可用 `{conference}`、`{year}`、`{title}`、`{context_text}`（PDF 正文）。

模板里要写字面的花括号时，写成 `{{` 和 `}}`。

默认模板面向多模态大模型（MLLM）研究：SIMPLE 输出中文标题、标签、一句话贡献、创新点、对 MLLM 的启发和推荐指数；FULL 输出论文画像、技术解构（架构、训练、数据）、实验结论，以及局限性和可以继续做的方向。

## 输出

每次运行生成一个目录，命名为 `<会议><年份>_<前两个关键词>_<模式>_<时间>`：

```
analyses/ICLR2026_TTT_Test-Time Training_FULL_20260206_172952/
├── summary.xlsx                     # 每篇一行，按评分降序，AI 解读保留前 500 字符
├── report.html                      # 完整报告，Markdown 已渲染，推荐阅读
├── papers/
│   ├── README.md                    # 论文索引
│   └── paper_001_<标题>.md          # 每篇一份完整解读
├── statistics/
│   ├── rating_distribution.png      # 评分分布
│   ├── keyword_wordcloud.png        # 关键词词云
│   ├── direction_distribution.png   # 研究方向饼图
│   └── statistics_summary.txt       # 统计摘要
├── audit_log.txt                    # API 调用次数、PDF 下载成功率、耗时
└── metadata.json                    # 本次运行的配置和统计
```

`csv: true` 时还会生成 `summary.csv`。

## 常见问题

**`403 ChallengeRequiredError: Challenge verification required`**

OpenReview 要求登录后才能通过 API 读取论文。设置 `OPENREVIEW_USERNAME` 和 `OPENREVIEW_PASSWORD` 后重新运行。

**`MfaRequiredError: ... Interactive login required (TTY)`**

账号开了两步验证，但程序不是在交互式终端里运行的（比如放到了后台）。在终端里直接运行（方案一），或者设置 `OPENREVIEW_TOTP_SECRET`（方案二）。

**提示「请配置有效的 GEMINI_API_KEY」**

没有设置环境变量 `GEMINI_API_KEY`，`config.yaml` 里也还是占位符 `YOUR_API_KEY_HERE`。

**筛选结果为 0**

- 降低 `score_threshold`，或调整 `keywords`；
- 检查 `invitation` 是否正确；
- 评分筛选依赖公开的审稿评分（字段名 `rating`）。目前只用 ICLR 2026 实际跑过；其他会议如果不公开评审，或评分字段不叫 `rating`，会筛不出论文。

**PDF 下载失败**

属于正常情况，会自动改用摘要和 TL;DR。失败次数记在 `audit_log.txt` 里。

**统计图里的中文显示成方框**

图表字体按 SimHei、Microsoft YaHei、Arial Unicode MS 的顺序查找，Linux 上通常都没有。装好任意中文字体后，修改 `output/statistics_generator.py` 开头的 `plt.rcParams['font.sans-serif']`。

## 使用须知

- 请遵守 OpenReview 的使用条款和限速。论文和审稿意见的版权归原作者，生成的报告仅供个人研究使用。
- FULL 模式会把每篇论文最多 100,000 字符的正文发给 Gemini，按 token 计费。建议先用 SIMPLE 模式或少量关键词试跑。

## 项目结构

```
├── main.py                      # 入口：拉取 → 筛选 → 解读 → 导出
├── config.yaml                  # 全部配置
├── config.py                    # 读取配置；环境变量 GEMINI_API_KEY 优先
├── core/
│   ├── openreview_client.py     # 登录（含两步验证）、读取投稿和审稿评分
│   ├── gemini_client.py         # 调用 Gemini，失败重试
│   └── pdf_processor.py         # 下载 PDF 并提取文本
├── analysis/
│   ├── paper_filter.py          # 关键词和评分筛选
│   └── prompt_builder.py        # 按模式填充 Prompt
├── output/                      # Excel / HTML / Markdown 导出和统计图
├── utils/                       # 日志、限速、文本处理
└── templates/report_template.html
```

## 许可证

[MIT](LICENSE)

## 致谢

- [OpenReview](https://openreview.net/)：论文和审稿数据
- [Google Gemini](https://ai.google.dev/)：论文解读
