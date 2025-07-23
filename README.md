# Exam Char Key

A comprehensive Chinese language learning platform that specializes in **ancient Chinese character explanations**, and AI-powered study assistance.

## Features

**Note**: This application currently requires an API key from Alibaba Cloud's DashScope service to access the Qwen AI models. Please ensure you have the necessary credentials before running the application. This might be configurable later.

### 🎯 Core Functionality

- **AI-Powered Quick Answers**: Get instant responses to Chinese language questions
- **Deep Text Analysis**: Comprehensive analysis of ancient Chinese texts with detailed annotations
- **Character Dictionary Integration**: Real-time character explanations and definitions from ZDIC
- **Textbook Integration**: Verbatim related character definitions in textbook

### 🤖 AI Capabilities

- **Multiple AI Models**: Integration with Qwen models, both official (for general tasks) and fine-tuned model (for explanations)
- **Contextual Understanding**: AI models trained specifically for Chinese language nuances
- **Real-time Processing**: Streaming AI responses for better user experience

### 📚 Educational Tools

- **History Tracking**: Keep track of your queries and learning progress, with export functionality for future revision
- **Interactive Interface**: Modern Vue.js frontend with responsive design

## Technology Stack

### Frontend

- **Vue 3** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **Pinia** for state management
- **Vue Router** for navigation
- **Reka UI** for component library
- **pnpm** for package management

### Backend

- **FastAPI** for high-performance API
- **Python 3.9+**
- **OpenAI API** integration (Qwen models)
- **Docker** & **Docker Compose** for containerization

## Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- pnpm
- Docker (or deployment tools that support Docker)

### Quick Start with Docker

1. **Clone the repository**

   ```bash
   git clone https://github.com/AsithaKanchana1/exam-char-key.git
   cd exam-char-key
   ```

2. **Set up environment variables**

   ```bash
   # Create .env file in the root directory
   echo "API_KEY=your_openai_api_key_here" > .env
   ```

3. **Run with Docker Compose** (alternatively, deploy it to [Coolify

   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Open your browser and navigate to `http://localhost:4122`

### Manual Installation

1. **Clone and setup environment**

   ```bash
   git clone https://github.com/AsithaKanchana1/exam-char-key.git
   cd exam-char-key
   echo "API_KEY=your_openai_api_key_here" > .env
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

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
API_KEY=your_openai_api_key_here
```

### API Configuration

The application uses Alibaba Cloud's DashScope API (Qwen models). Configure your API settings in `server/main.py`:

- **Base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Models Available**:
  - `qwen-plus`: General purpose model
  - `qwen-turbo`: Fast response model
  - `qwen3-14b-ft-202506272014-8e62`: Specialized ancient Chinese model

## Usage

### Basic Workflow

1. **Text Input**: Add Chinese text or characters you want to analyze
2. **AI Analysis**: Get quick AI-powered explanations and interpretations
3. **Character Lookup**: Click on characters for detailed dictionary definitions
4. **Deep Analysis**: Access comprehensive annotations and contextual information
5. **History Review**: Track your learning progress through the history feature

## Development

### Project Structure

```text
exam-char-key/
├── client/                 # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page views
│   │   ├── stores/         # Pinia stores
│   │   └── router/         # Vue Router configuration
├── server/                 # FastAPI backend
│   ├── main.py            # API endpoints
│   ├── requirements.txt   # Python dependencies
│   └── textbook.json     # Educational content
├── train/                 # ML training scripts
│   ├── ancient_classifier.py
│   └── dataset_generator.py
└── scripts/               # Utility scripts
```

### Development Scripts

#### Frontend Development

```bash
cd client
pnpm run dev     # Start development server
pnpm run build   # Build for production
pnpm run preview # Preview production build
```

#### Backend Development

```bash
uvicorn server.main:app --host 0.0.0.0 --port 4122 --reload
```

#### Run Both (Development)

```bash
python run_dev.py
```

### API Endpoints

- `GET /` - Serve frontend application
- `POST /api/query` - Quick & Deep AI responses & ZDIC lookup
- `POST /api/search-original` - Search original context of given excerpts

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
python -m train.extractor.guwen_extractor
python -m train.extractor.textbook_extractor # This should be run again, at this time non-ancient works will be sorted out.

python -m train.dataset_generator.flash_dataset_generator
python -m train.dataset_generator.thinking_prompt_generator
python -m train.dataset_generator.thinking_batch_converter
### !Batch reasoning and place result in train/result/dataset-thinking-batch-completion-{1,2}.json
python -m train.dataset_generator.evaluate_prompt_generator
### !Batch reasoning and place result in train/result/dataset-thinking-evaluation-completion-{1,2}.json
python -m train.dataset_generator.thinking_dataset_generator
```

**Fine Tune**: Using SFT algorithm, dataset `train/result/dataset-flash.jsonl` and `train/result/dataset-thinking.jsonl` to fine-tune the Qwen3-14b and Qwen3-8b model, respectively.

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
- Contributors to the Chinese language learning community
