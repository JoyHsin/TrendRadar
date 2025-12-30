# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

**TrendRadar** - 热点新闻聚合与分析工具

- **版本**: v4.5.0
- **语言**: Python 3.10+
- **核心功能**: 多平台热点新闻聚合、关键词筛选、智能推送、AI 分析（MCP 协议）
- **部署方式**: GitHub Actions、Docker、本地运行

## 核心架构

### 1. 模块化架构

项目采用清晰的模块化设计，主要包含两个独立包：

```
trendradar/          # 主应用包（新闻抓取、分析、推送）
├── core/            # 核心业务逻辑（配置、分析、频率统计）
├── crawler/         # 数据抓取（热榜 + RSS）
├── storage/         # 存储管理（本地 SQLite + 远程 S3）
├── notification/    # 通知系统（多渠道推送）
├── report/          # 报告生成（HTML）
└── utils/           # 工具函数

mcp_server/          # MCP 服务器包（AI 分析接口）
├── tools/           # MCP 工具集（17个分析工具）
├── services/        # 业务服务层
└── utils/           # MCP 工具函数
```

### 2. 存储架构（v4.0.0 重构）

**多后端存储系统**：
- **Local Backend**: SQLite 数据库（Docker/本地环境默认）
- **Remote Backend**: S3 兼容云存储（GitHub Actions 默认，支持 Cloudflare R2/阿里云 OSS/腾讯云 COS）
- **Auto Backend**: 根据运行环境自动选择

**数据格式**：
- SQLite: 主存储格式，按日期分库 `output/{type}/{date}.db`
- TXT: 可选快照格式（向后兼容）
- HTML: 报告展示格式

**关键文件路径**：
- 新闻数据: `output/news/YYYY-MM-DD.db`
- RSS 数据: `output/rss/YYYY-MM-DD.db`
- HTML 报告: `output/html/YYYY-MM-DD/`

### 3. 推送模式策略

三种运行模式（`config.yaml` 中的 `report.mode`）：

| 模式 | 值 | 推送逻辑 | 适用场景 |
|------|-----|---------|---------|
| 当日汇总 | `daily` | 按时推送当日所有匹配新闻 | 企业管理者、普通用户 |
| 当前榜单 | `current` | 按时推送当前榜单匹配新闻 | 自媒体人、内容创作者 |
| 增量监控 | `incremental` | 仅推送新增内容 | 投资者、交易员 |

### 4. 通知系统架构

**多渠道支持**（支持多账号配置，v3.5.0+）：
- 企业微信、飞书、钉钉、Telegram
- 邮件、ntfy、Bark、Slack

**推送流程**：
1. `NotificationDispatcher`: 统一调度器
2. `PushManager`: 推送窗口控制
3. Channel Senders: 各渠道发送器（支持分批推送）
4. Formatters: 格式转换器（Markdown/纯文本）

### 5. MCP 服务器（AI 分析）

基于 FastMCP 2.0 实现，提供 17 个智能分析工具：

**工具分类**：
- 基础查询: `get_latest_news`, `get_news_by_date`, `get_trending_topics`
- 智能检索: `search_news`, `find_related_news`
- 高级分析: `analyze_topic_trend`, `analyze_sentiment`, `aggregate_news`, `compare_periods`
- RSS 查询: `get_latest_rss`, `search_rss`, `get_rss_feeds_status`
- 系统管理: `get_current_config`, `get_system_status`, `resolve_date_range`

**传输模式**：
- STDIO: 直接进程通信（推荐，Claude Desktop/Cursor）
- HTTP: HTTP 服务器模式（端口 3333，需手动启动）

## 开发指南

### 常用命令

```bash
# 安装依赖
# Windows: setup-windows.bat
# Mac/Linux: ./setup-mac.sh

# 运行主程序
python -m trendradar
# 或安装后
trendradar

# 启动 MCP HTTP 服务器（AI 分析）
# Windows: start-http.bat
# Mac/Linux: ./start-http.sh
# 或手动
uv run python -m mcp_server.server --transport http --port 3333

# Docker 部署
cd docker
docker compose up -d

# Docker 管理命令
docker exec -it trendradar python manage.py status    # 查看状态
docker exec -it trendradar python manage.py run       # 手动执行
docker exec -it trendradar python manage.py logs      # 查看日志
docker exec -it trendradar python manage.py config    # 显示配置
```

### 配置文件

**核心配置文件**（修改后需重启）：

1. **`config/config.yaml`** - 主配置文件
   - 应用设置（时区、版本检查）
   - 报告配置（模式、排序、数量限制）
   - 通知配置（推送渠道、时间窗口）
   - 存储配置（后端选择、保留天数）
   - 平台配置（监控平台列表）
   - RSS 配置（订阅源、新鲜度过滤）
   - 高级配置（权重、代理、爬虫）

2. **`config/frequency_words.txt`** - 关键词配置
   - 普通词：基础匹配
   - 必须词 `+`：限定范围
   - 过滤词 `!`：排除干扰
   - 数量限制 `@数字`：控制显示数量
   - 全局过滤 `[GLOBAL_FILTER]`：全局排除
   - 词组分隔：空行分隔不同主题

3. **`.github/workflows/crawler.yml`** - GitHub Actions 定时任务
   - Cron 表达式控制执行频率
   - 环境变量配置（Secrets）

### 环境变量优先级

配置优先级：**环境变量 > config.yaml**

**关键环境变量**（Docker/GitHub Actions）：
```bash
# 存储配置
STORAGE_BACKEND=auto|local|remote
S3_BUCKET_NAME=your-bucket
S3_ACCESS_KEY_ID=your-key
S3_SECRET_ACCESS_KEY=your-secret
S3_ENDPOINT_URL=https://...
LOCAL_RETENTION_DAYS=30
REMOTE_RETENTION_DAYS=30

# 应用配置
ENABLE_CRAWLER=true|false
ENABLE_NOTIFICATION=true|false
REPORT_MODE=daily|current|incremental
TIMEZONE=Asia/Shanghai

# 推送配置
PUSH_WINDOW_ENABLED=true|false
PUSH_WINDOW_START=09:00
PUSH_WINDOW_END=18:00

# 通知渠道（支持多账号，用 ; 分隔）
FEISHU_WEBHOOK_URL=url1;url2
TELEGRAM_BOT_TOKEN=token1;token2
TELEGRAM_CHAT_ID=id1;id2
```

### 代码规范

**Python 代码风格**：
- 使用 UTF-8 编码：`# coding=utf-8`
- 类型提示：函数参数和返回值必须标注类型
- 文档字符串：使用三引号文档字符串说明模块/类/函数用途
- 命名约定：
  - 类：PascalCase（如 `NewsAnalyzer`）
  - 函数/方法：snake_case（如 `load_config`）
  - 常量：UPPER_SNAKE_CASE（如 `VERSION_CHECK_URL`）
  - 私有方法：前导下划线（如 `_init_storage_manager`）

**模块化原则**：
- 单一职责：每个模块/类专注一个功能
- 依赖注入：通过 `AppContext` 管理共享状态
- 配置集中：所有配置通过 `config.yaml` 和环境变量管理
- 错误处理：使用自定义异常类（如 `MCPError`）

### 关键设计模式

1. **Context 模式** (`trendradar/context.py`)
   - `AppContext` 类管理全局配置和共享资源
   - 提供统一的时间、存储、通知接口
   - 生命周期管理（初始化、清理）

2. **Strategy 模式** (推送模式)
   - `MODE_STRATEGIES` 字典定义三种模式的行为
   - 运行时根据配置选择策略

3. **Factory 模式** (存储后端)
   - `StorageManager` 根据配置创建不同后端
   - 统一接口，多种实现（Local/Remote）

4. **Dispatcher 模式** (通知系统)
   - `NotificationDispatcher` 统一调度多渠道推送
   - 各渠道独立发送，失败不影响其他渠道

### 数据流程

**主流程** (`trendradar/__main__.py:NewsAnalyzer.run()`):
```
1. 初始化配置 → 创建 AppContext
2. 抓取热榜数据 → DataFetcher.crawl_websites()
3. 抓取 RSS 数据 → RSSFetcher.fetch_all()
4. 保存到存储后端 → StorageManager.save_news_data()
5. 检测新增标题 → AppContext.detect_new_titles()
6. 关键词匹配统计 → AppContext.count_frequency()
7. 生成 HTML 报告 → AppContext.generate_html()
8. 发送通知 → NotificationDispatcher.dispatch_all()
9. 清理资源 → AppContext.cleanup()
```

**MCP 分析流程** (`mcp_server/server.py`):
```
1. 客户端连接 → FastMCP 处理请求
2. 工具调用 → 路由到对应 Tools 类
3. 读取数据 → StorageManager 加载 SQLite
4. 数据分析 → 各种分析算法
5. 返回结果 → JSON 格式响应
```

### 测试与调试

**本地测试**：
```bash
# 测试主程序
python -m trendradar

# 测试 MCP 服务器（STDIO）
uv run python -m mcp_server.server

# 测试 MCP 服务器（HTTP）
uv run python -m mcp_server.server --transport http --port 3333
# 访问 http://localhost:3333/mcp 验证

# 使用 MCP Inspector 调试
npx @modelcontextprotocol/inspector
```

**Docker 调试**：
```bash
# 查看日志
docker logs -f trendradar

# 进入容器
docker exec -it trendradar /bin/bash

# 手动执行
docker exec -it trendradar python -m trendradar
```

### 常见问题排查

1. **配置不生效**
   - 检查环境变量是否覆盖了 config.yaml
   - Docker 环境需重启容器：`docker restart trendradar`

2. **数据读取失败**
   - 确认 output 目录存在且有数据
   - 检查日期格式：YYYY-MM-DD
   - 验证存储后端配置正确

3. **推送失败**
   - 检查 webhook URL 是否正确
   - 验证网络连接（代理配置）
   - 查看日志中的详细错误信息

4. **MCP 连接失败**
   - STDIO 模式：确认 UV 路径正确
   - HTTP 模式：确认服务已启动，端口未被占用
   - 检查项目路径无中文字符

## 重要注意事项

### 安全性

- **敏感信息管理**：
  - GitHub Actions: 使用 GitHub Secrets 存储 webhook URL、token
  - Docker: 使用 `.env` 文件（已在 `.gitignore` 中）
  - 本地开发: 确保 config.yaml 不提交到公开仓库

- **Webhook 保护**：
  - 不要在代码中硬编码 webhook URL
  - 不要将 webhook URL 提交到 Git
  - 定期轮换 token 和密钥

### 版本兼容性

- **v4.0.0 重大变更**：
  - 存储结构完全重构，不兼容 v3.x 数据
  - 数据库格式从单文件改为按日期分库
  - 文件路径格式变更（ISO 格式）

- **向后兼容**：
  - TXT 格式保留用于兼容旧版本
  - 环境变量配置向后兼容

### 性能优化

- **批量操作**：
  - 数据库使用批量插入
  - 通知系统支持分批推送

- **缓存策略**：
  - 配置文件缓存在 AppContext
  - 存储管理器单例模式

- **资源管理**：
  - 使用 `try-finally` 确保资源释放
  - AppContext.cleanup() 清理数据库连接

### 多语言支持

- **用户界面**：中文为主
- **代码注释**：中文
- **文档**：中文（README.md）+ 英文（README-EN.md）
- **日志输出**：中文

## 项目特色

1. **零技术门槛部署**：GitHub Actions 一键 Fork 即用
2. **灵活的推送策略**：三种模式适应不同需求
3. **智能关键词筛选**：5种语法精准过滤
4. **多渠道推送**：8种通知渠道，支持多账号
5. **AI 智能分析**：MCP 协议集成，17种分析工具
6. **云端存储支持**：GitHub Actions 不污染仓库
7. **RSS 订阅支持**：统一格式，与热榜合并推送

## 相关文档

- **部署教程**: README.md（中文）、README-EN.md（英文）
- **MCP 使用**: README-MCP-FAQ.md（中文）、README-MCP-FAQ-EN.md（英文）
- **Cherry Studio 配置**: README-Cherry-Studio.md
- **项目主页**: https://github.com/sansan0/TrendRadar
