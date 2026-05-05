# Exam Char Key

A comprehensive Chinese language learning platform that specializes in **ancient Chinese character explanations**, and AI-powered study assistance.

## Features

**Note**: This application requires an OpenAI-compatible API key. It supports any provider with an OpenAI-compatible API (DashScope for Qwen models, OpenRouter, OpenAI, etc.). Configure via `server/.env`.

### 🎯 Core Functionality

- **AI-Powered Quick Answers**: Get instant responses to Chinese language questions
- **Deep Text Analysis**: Comprehensive analysis of ancient Chinese texts with detailed annotations
- **Character Dictionary Integration**: Real-time character explanations and definitions from ZDIC
- **Textbook Integration**: Verbatim related character definitions in textbook
- **Frequency Analysis**: Statistical analysis of character usage across different contexts

### 🤖 AI Capabilities

- **Multiple AI Models**: Three configurable models for dictionary preprocessing, quick answering, and deep thinking
- **Provider Agnostic**: Supports any OpenAI-compatible API (Qwen via DashScope, OpenRouter, OpenAI, etc.)
- **Contextual Understanding**: AI models trained specifically for Chinese language nuances
- **Real-time Processing**: Streaming SSE responses for better user experience

### 🔐 Authentication & Quota

- **OAuth Login**: Sign in with GitHub or Gitee
- **Daily Quota**: Configurable query limits for authenticated users and guests
- **History Sync**: Per-user query history backed by SQLite

### 📚 Educational Tools

- **History Tracking**: Keep track of your queries and learning progress
- **Export**: Export history to JSON, Word (.docx), or Anki (.apkg) format
- **Legacy Migration**: Import history from the old localStorage-based version
- **Corpus Collection**: Automatically builds a searchable corpus from user queries
- **Interactive Interface**: Modern Vue.js frontend with responsive design

## Technology Stack

### Frontend

- **Vue 3** (3.5+) with TypeScript
- **Vite** (v8) for fast development and building
- **TailwindCSS** (v4) with `@tailwindcss/vite` plugin
- **Pinia** (v3) for state management
- **Vue Router** (v5) for navigation
- **VueUse** for composable utilities
- **Vue DevTools** integration via Vite plugin
- **pnpm** for package management

### Backend

- **FastAPI** for high-performance API
- **Python 3.12+**
- **Uvicorn** ASGI server
- **OpenAI API** compatible client (DashScope, OpenRouter, OpenAI, etc.)
- **SQLite** for local database and caching
- **httpx** for async HTTP requests
- **BeautifulSoup4** for ZDIC dictionary scraping
- **PyJWT** for authentication tokens
- **Docker** & **Docker Compose** for containerization

## Installation

### Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm
- Docker (optional, for containerized deployment)

### Quick Start with Docker

1. **Clone the repository**

   ```bash
   git clone https://github.com/AsithaKanchana1/exam-char-key.git
   cd exam-char-key
   ```

2. **Set up environment variables**

   ```bash
   cp server/.env.example server/.env
   # Edit server/.env with your API keys
   ```

3. **Run with Docker Compose**

   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Open your browser and navigate to `http://localhost:5173`

### Manual Installation

1. **Clone and setup environment**

   ```bash
   git clone https://github.com/AsithaKanchana1/exam-char-key.git
   cd exam-char-key
   cp server/.env.example server/.env
   # Edit server/.env with your API keys
   ```

2. **Install backend dependencies**

   ```bash
   pip install -r server/requirements.txt
   ```

3. **Install frontend dependencies**

   ```bash
   cd client
   pnpm install
   cd ..
   ```

4. **Run the development server**

   ```bash
   python run_dev.py
   ```

   This starts both the Vite dev server (port 5173 for frontend) and the FastAPI backend (port 8000). The Vite dev server proxies `/api` requests to the backend automatically.

## Configuration

### Environment Variables

Create a `server/.env` file based on `server/.env.example`:

```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-xxxxxxxx
MODEL_DICT_PREPROCESS=xiaomi/mimo-v2.5
MODEL_QUICK_ANSWER=xiaomi/mimo-v2.5
MODEL_DEEP_THINK=xiaomi/mimo-v2.5
QUOTA_USER_DAILY=50
QUOTA_GUEST_DAILY=50
APP_BASE_URL=http://localhost:5173
JWT_SECRET=
DB_PATH=../db/data.db
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITEE_CLIENT_ID=
GITEE_CLIENT_SECRET=
```

### API Configuration

The application supports any OpenAI-compatible API service. Configure via `server/.env`:

| Variable | Description | Example |
|---|---|---|
| `LLM_BASE_URL` | API endpoint base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` (Qwen), `https://openrouter.ai/api/v1` |
| `LLM_API_KEY` | Your API key | `sk-...` |
| `MODEL_DICT_PREPROCESS` | Model for structuring raw dictionary data into JSON | `qwen-turbo`, `gpt-3.5-turbo` |
| `MODEL_QUICK_ANSWER` | Model for fast inline character explanations | `qwen3-8b-ft-202508031744-1c46` |
| `MODEL_DEEP_THINK` | Model for comprehensive deep analysis | `qwen3-8b-ft-202508031744-1c46`, `gpt-4o` |

### JWT Secret

`JWT_SECRET` is used to sign authentication tokens. Generate a secure random value:

```bash
# Option 1: openssl (Linux/macOS/Git Bash)
openssl rand -hex 32

# Option 2: Python (cross-platform)
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and set it as `JWT_SECRET` in your `server/.env` or Coolify environment variables. If left empty, the server will fall back to `LLM_API_KEY` as the JWT secret.

### OAuth Configuration

To enable GitHub/Gitee login, register OAuth applications and set the corresponding `*_CLIENT_ID` and `*_CLIENT_SECRET` environment variables. The callback URL should be `{APP_BASE_URL}/api/oauth2-redirect`.

## Usage

### Basic Workflow

1. **Text Input**: Add Chinese text or characters you want to analyze
2. **AI Analysis**: Get instant AI-powered explanations and interpretations
3. **Character Lookup**: Click on characters for detailed dictionary definitions (sourced from ZDIC and AI-structured)
4. **Deep Analysis**: Access comprehensive annotations and contextual information
5. **History Review**: Track your learning progress through the history feature

### Authentication

- Click "Login" to sign in via GitHub or Gitee
- Authenticated users get per-user history, higher quota, and export capabilities
- Guest users can still query with a shared daily pool

### Export

- Export your query history to JSON, Word (.docx), or Anki (.apkg) format
- Anki export is powered by an external service

## Development

### Project Structure

```
exam-char-key/
├── client/                          # Vue 3 frontend
│   ├── src/
│   │   ├── App.vue                  # Root component
│   │   ├── main.ts                  # Entry point
│   │   ├── types.ts                 # TypeScript type definitions
│   │   ├── assets/
│   │   │   └── main.css             # Global TailwindCSS styles
│   │   ├── components/
│   │   │   ├── DictDisplay.vue      # Dictionary lookup display
│   │   │   ├── QueryPanel.vue       # Main query interface
│   │   │   ├── SelectionTooltip.vue # Text selection tooltip
│   │   │   └── TextContent.vue      # Text content viewer
│   │   ├── router/
│   │   │   └── index.ts             # Vue Router configuration
│   │   ├── stores/
│   │   │   ├── auth.ts              # Authentication state (Pinia)
│   │   │   └── words.ts             # Query/words state (Pinia)
│   │   └── views/
│   │       ├── HomeView.vue         # Main search/query view
│   │       ├── HistoryView.vue      # Query history view
│   │       └── ProfileView.vue      # User profile & export
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts               # Vite config with /api proxy
│   └── tsconfig*.json
├── server/                          # FastAPI backend
│   ├── main.py                      # App entry, routes, CORS, SSE pipeline
│   ├── config.py                    # Pydantic settings from .env
│   ├── auth.py                      # GitHub/Gitee OAuth + JWT auth
│   ├── db_helper.py                 # SQLite database helpers (dict cache, quota, history, corpus)
│   ├── spider.py                    # ZDIC scraping + AI structuring pipeline
│   ├── prompt.py                    # LLM prompt templates
│   ├── log_helper.py                # Logging configuration
│   ├── import_corpus.py             # Corpus import utility
│   ├── requirements.txt
│   └── .env.example                 # Environment variable template
├── train/                           # ML training pipeline
│   ├── extractor/                   # PDF textbook extraction & classification
│   │   ├── textbook_extractor.py
│   │   ├── ancient_classifier.py
│   │   ├── model_extractor.py
│   │   └── unmarker.py
│   ├── dataset_generator/           # Training dataset generation
│   │   ├── flash_dataset_generator.py
│   │   ├── thinking_prompt_generator.py
│   │   ├── thinking_batch_converter.py
│   │   ├── evaluate_prompt_generator.py
│   │   └── filter_dataset_generator.py
│   ├── evaluator/                   # Model evaluation
│   │   ├── evaluators.py
│   │   ├── evaluation_concluder.py
│   │   ├── evaluation_prompts_generator.py
│   │   ├── graph_maker.py
│   │   └── xlsx_converter.py
│   ├── frequency_statistics.py      # Character frequency analysis
│   ├── models.py                    # Data models
│   └── utils.py                     # Shared utilities
├── db/                              # SQLite database (auto-created)
├── logs/                            # Application logs
├── scripts/
│   └── install.sh                   # Setup script
├── docker-compose.yml               # Docker Compose configuration
├── Dockerfile                       # Multi-stage build (frontend → backend)
├── run_dev.py                       # Development launcher (Vite + Uvicorn)
└── README.md
```

## Training & AI Models

The project includes training scripts for:

- **Ancient Text Classification**: Automatically detect classical Chinese texts, extracting them from Chinese textbooks.
- **Character Frequency Analysis**: Statistical analysis of character usage
- **Dataset Generation**: Create training data from textbooks and literature

### Training Scripts

If you'd like to train on your own, you're supposed to execute the scripts in the following order:

```bash
python -m train.extractor.textbook_extractor
python -m train.extractor.ancient_classifier
python -m train.extractor.model_extractor
python -m train.extractor.textbook_extractor # This should be run again, at this time non-ancient works will be sorted out.

python -m train.dataset_generator.flash_dataset_generator
python -m train.dataset_generator.thinking_prompt_generator
python -m train.dataset_generator.thinking_batch_converter
### !Batch reasoning and place result in train/result/dataset-thinking-batch-completion-{1,2,3}.json
python -m train.dataset_generator.evaluate_prompt_generator
### !Batch reasoning and place result in train/result/dataset-thinking-evaluation-completion-{1,2}.json
python -m train.dataset_generator.thinking_dataset_generator
```

**Fine Tune**: Using SFT algorithm, dataset `train/result/dataset-flash.jsonl` and `train/result/dataset-thinking.jsonl` to fine-tune 2 separate Qwen3-8b models.

### Development Guidelines

- Follow TypeScript best practices for frontend code
- Use Python type hints in backend code
- Maintain consistent code formatting

## Support

For support, questions, or feature requests: create an issue on GitHub, or contact the development team

## Acknowledgments

- **Qwen AI Models** by Alibaba Cloud for advanced language processing
- **ZDIC** for comprehensive Chinese character dictionary
- **Vue.js** and **FastAPI** communities for excellent frameworks
- **[Leximory](https://github.com/NarixHine/leximory)** for UI/UX & system design inspiration
- **中国哲学书电子化计划 ([ctext.org](https://ctext.org))**, **识典古籍 ([shidianguji.com](https://www.shidianguji.com))**, and **古文岛 ([guwendao.net](https://www.guwendao.net))** for providing extensive classical Chinese text repositories
- Contributors to the Chinese language learning community
