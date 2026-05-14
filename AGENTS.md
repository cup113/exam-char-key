# exam-char-key

AI-assisted Classical Chinese learning platform. See [CONTEXT.md](./CONTEXT.md) for domain model and [docs/adr/](./docs/adr/) for architecture decisions.

## 项目架构

```
client (Vite + Vue 3 + Pinia + TypeScript + Tailwind CSS v4)
  └─ src/
      ├─ stores/     Pinia 状态管理（words.ts 查询状态，auth.ts 登录/配额，theme.ts 深色模式）
      ├─ views/      页面：AdminView（管理后台）、HomeView（主页面）、HistoryView、ProfileView
      ├─ components/ 组件：DeepAnalysisSplit、DictDisplay、LoginButtons、QueryPanel、SelectionTooltip、TextContent
      └─ router/     路由配置

server (FastAPI + SQLite + OpenAI SDK)
  ├─ .env.example   示例环境变量（此文件可读，.env 不允许读取）
  ├─ main.py        FastAPI 应用入口，路由定义
  ├─ spider.py      汉典爬虫 + LLM 结构化 + dict 格式化
  ├─ db_helper.py   Database 类（缓存、配额、历史记录）+ 模块级默认实例
  ├─ auth.py        GitHub/Gitee OAuth + JWT
  ├─ admin.py       SQLAdmin 后台（ModelView + JWT 鉴权）
  ├─ config.py      配置（含 ADMIN_USERS 白名单）
  ├─ prompt.py      LLM 提示词模板
  ├─ log_helper.py  日志配置
  ├─ import_corpus.py  语料导入工具
  ├─ tests/
  │   ├── conftest.py              测试环境（临时 DB + JWT fixture）
  │   ├── test_admin.py            14 个用例（鉴权、模型列表、admin API、导入语料）
  │   └── test_db_helper.py        30 个用例（Database 类全覆盖 — 表创建、配额、缓存、历史记录、语料、隔离性）
  ├─ pytest.ini     配置 (pythonpath = .)
  ├─ requirements.txt
  └─ .env.example
```

## 环境变量配置流程

新增环境变量需同步更新以下 **5 个位置**，缺一不可：

| # | 文件 | 操作 |
|---|------|------|
| 1 | `server/config.py` | `Settings` 类中声明字段 + 默认值（例：`ZDIC_TIMEOUT: int = 30`） |
| 2 | 使用该变量的 `.py` 文件 | 通过 `settings.XXX` 调用，禁止硬编码 |
| 3 | `server/.env.example` | 添加示例值，供开发/部署参考 |
| 4 | `docker-compose.yml` | `environment` 块添加 `- XXX=${XXX:-}`，确保容器内可用 |
| 5 | `server/tests/conftest.py` | 若变量影响未 mock 的逻辑，需覆盖测试值 |

现有完整环境变量列表见 `server/.env.example`（共 16 项），此文件可公开读取，`.env` 禁止读取。

train (Fine-tuning on DashScope, inactive now)

docker-compose.yml, Dockerfile (Linux Coolify Deployment)

run_dev.py (Windows Local Development)

## 常用命令

### 前端（client/）

```bash
pnpm dev          # 启动开发服务器
pnpm build        # 生产构建
pnpm type-check   # TypeScript 类型检查
```

### 后端（server/）

```bash
ruff check .      # 代码检查
ruff format .     # 代码格式化
python ../run_dev.py  # 启动开发服务器
pytest            # 运行服务端测试
```
