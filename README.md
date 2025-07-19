# Exam Char Key

A comprehensive Chinese language learning platform that specializes in ancient Chinese text analysis, character explanations, and AI-powered study assistance.

## Features

### 🎯 Core Functionality

- **AI-Powered Quick Answers**: Get instant responses to Chinese language questions
- **Deep Text Analysis**: Comprehensive analysis of ancient Chinese texts with detailed annotations
- **Character Dictionary Integration**: Real-time character explanations and definitions from ZDIC
- **Passage Annotation**: Interactive text annotation system for ancient Chinese literature
- **Search & Query System**: Advanced search functionality for Chinese characters and texts

### 🤖 AI Capabilities

- **Multiple AI Models**: Integration with Qwen models for different use cases
- **Ancient Text Classification**: Automatic detection of classical Chinese texts
- **Contextual Understanding**: AI models trained specifically for Chinese language nuances
- **Real-time Processing**: Streaming AI responses for better user experience

### 📚 Educational Tools

- **Textbook Integration**: Built-in textbook content for structured learning
- **History Tracking**: Keep track of your queries and learning progress
- **Interactive Interface**: Modern Vue.js frontend with responsive design

## Technology Stack

### Frontend

- **Vue 3** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **Pinia** for state management
- **Vue Router** for navigation
- **TipTap** for rich text editing
- **Reka UI** for component library

### Backend

- **FastAPI** for high-performance API
- **Python 3.8+**
- **OpenAI API** integration (Qwen models)
- **BeautifulSoup** for web scraping
- **Uvicorn** ASGI server

### Development & Deployment

- **Docker** & **Docker Compose** for containerization
- **pnpm** for package management
- **TypeScript** for type safety

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- pnpm
- Docker (optional)

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

3. **Run with Docker Compose**

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
APP_ENV=development
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

### Features Overview

#### Add Text Component

- Input Chinese text for analysis
- Support for both modern and ancient Chinese

#### Quick Answer

- Instant AI responses to language questions
- Fast turbo model for immediate feedback

#### Deep Answer

- Comprehensive analysis using advanced AI models
- Detailed explanations with cultural and historical context

#### Character Dictionary (ZDIC Integration)

- Real-time character definitions
- Etymology and usage examples
- Pronunciation guides

#### Passage Annotation

- Interactive text highlighting
- Contextual annotations
- Save and review annotated passages

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
- `POST /ai/quick` - Quick AI responses
- `POST /ai/deep` - Deep analysis with advanced models
- `GET /zdic/{character}` - Character dictionary lookup
- `POST /annotate` - Text annotation functionality

## Training & AI Models

The project includes training scripts for:

- **Ancient Text Classification**: Automatically detect classical Chinese texts
- **Character Frequency Analysis**: Statistical analysis of character usage
- **Dataset Generation**: Create training data from textbooks and literature

### Training Scripts

```bash
python train/ancient_classifier.py    # Train ancient text classifier
python train/frequency_statistics.py  # Analyze character frequencies
python train/dataset_generator.py     # Generate training datasets
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow TypeScript best practices for frontend code
- Use Python type hints in backend code
- Write tests for new features
- Maintain consistent code formatting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, questions, or feature requests:

- Create an issue on GitHub
- Contact the development team

## Acknowledgments

- **Qwen AI Models** by Alibaba Cloud for advanced language processing
- **ZDIC** for comprehensive Chinese character dictionary
- **Vue.js** and **FastAPI** communities for excellent frameworks
- Contributors to the Chinese language learning community

---

**Note**: This application requires an API key from Alibaba Cloud's DashScope service to access the Qwen AI models. Please ensure you have the necessary credentials before running the application.