# exam-char-key

Exam Char Key — 面向文言文学习的 AI 辅助平台，提供精准的汉字释义，助力高效学习与研究。现代前后端技术栈，支持容器化部署与学习进度管理。

## 项目架构

```
client (Vite + Vue 3 + Pinia + TypeScript + Tailwind CSS v4)
  └─ src/
      ├─ stores/     Pinia 状态管理（words.ts 查询状态，auth.ts 登录/配额）
      ├─ views/      页面：HomeView（主页面）、HistoryView、ProfileView
      ├─ components/ 组件：TextContent、SelectionTooltip、QueryPanel、DictDisplay
      └─ router/     路由配置

server (FastAPI + SQLite + OpenAI SDK)
  ├─ .env.example   示例环境变量（此文件可读，.env 不允许读取）
  ├─ main.py        FastAPI 应用入口，路由定义
  ├─ spider.py      汉典爬虫 + LLM 结构化 + dict 格式化
  ├─ db_helper.py   SQLite 数据库操作（缓存、配额、历史记录）
  ├─ auth.py        GitHub/Gitee OAuth + JWT
  ├─ config.py      配置
  └─ prompt.py      LLM 提示词模板

train (Fine-tuning on DashScope, inactive now)

docker-compose.yml, Dockerfile (Linux Coolify Deployment)

run_dev.py (Windows Local Development)
```

## 数据流转

```
用户选词 → SelectionTooltip (mode: quick/deep)
  └─ wordsStore.queryWord()
       ├─ GET /api/query/quick     ← SSE 流 → quickAnswer
       ├─ GET /api/query/corpus    ← JSON    → corpusEntries
       ├─ GET /api/query/dictionary← JSON    → dictResult
       └─ (deep 模式) GET /api/query/deep ← SSE 流 → deepThink
              ↑ deep 需等待 dictionary 完成后由服务端从缓存取 dict_data，格式化为文本后拼入 prompt
       └─ status: done → QueryPanel 展示
```

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
```
