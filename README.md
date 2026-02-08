# PowerPoint Maker

An AI-powered application that generates PowerPoint presentations from a template and a topic.

## Features

- **Template Analysis**: Upload your corporate or custom PowerPoint templates.
- **AI Research**: Automatically researches the provided topic using advanced AI agents.
- **Text Input**: Transform raw text into structured presentations with AI-powered layout selection.
- **Content Generation**: Generates slide content structured to fit your template's layout.
- **PowerPoint Generation**: Produces a downloadable `.pptx` file with preserved formatting.
- **Preview**: Review and edit the generated content before downloading.

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) (Recommended)
- Or: Python 3.12+ and Node.js (LTS)

### Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    mise install
    ```
    (Or manually install backend dependencies with `uv` and frontend with `pnpm`)

### Configuration

Create a `.env` file in the `backend` directory based on `.env.example`:

#### Required Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `WATSONX_API_KEY` | Yes | API Key for IBM watsonx | - |
| `WATSONX_PROJECT_ID` | Yes | Project ID for IBM watsonx | - |
| `WATSONX_URL` | Yes | IBM watsonx API endpoint | `https://us-south.ml.cloud.ibm.com` |

#### Optional Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | No | API Key for OpenAI (alternative provider) | - |
| `ANTHROPIC_API_KEY` | No | API Key for Anthropic Claude (alternative provider) | - |
| `GOOGLE_API_KEY` | No | API Key for Google Gemini (alternative provider) | - |
| `HOST` | No | Server host address | `0.0.0.0` |
| `PORT` | No | Server port number | `8000` |
| `DEBUG` | No | Debug mode | `false` |
| `CORS_ORIGINS` | No | Allowed CORS origins (comma-separated) | `http://localhost:5173` |
| `MAX_UPLOAD_SIZE` | No | Maximum file upload size (bytes) | `10485760` (10MB) |
| `RESEARCH_TIMEOUT` | No | Research operation timeout (seconds) | `180` |
| `LOG_LEVEL` | No | Logging level | `INFO` |

#### LLM Provider Setup

This project uses the BeeAI Framework, which supports multiple LLM providers.

##### Primary: IBM watsonx (Recommended)
1. Sign up at [IBM Cloud](https://cloud.ibm.com/)
2. Create a watsonx.ai project
3. Get your API key and Project ID from the credentials page
4. Set `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, and `WATSONX_URL` in `.env`

##### Alternative Providers (Optional)

**OpenAI:**
1. Get API key from [OpenAI Platform](https://platform.openai.com/)
2. Uncomment and set `OPENAI_API_KEY` in `.env`

**Anthropic Claude:**
1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Uncomment and set `ANTHROPIC_API_KEY` in `.env`

**Google Gemini:**
1. Get API key from [Google AI Studio](https://makersuite.google.com/)
2. Uncomment and set `GOOGLE_API_KEY` in `.env`

**Provider Selection Priority:**
The system automatically selects the first available provider in this order:
1. Claude (if `ANTHROPIC_API_KEY` is set)
2. OpenAI (if `OPENAI_API_KEY` is set)
3. Gemini (if `GOOGLE_API_KEY` is set)
4. IBM watsonx (if `WATSONX_API_KEY` is set)


### Usage

#### Option 1: Web Search (Topic-based)

1.  Start the development servers:
    ```bash
    mise run dev
    ```
2.  Open your browser to `http://localhost:5173`.
3.  Upload a PowerPoint template (`.pptx`).
4.  Select the "Web Search" tab.
5.  Enter a topic (e.g., "The Future of AI").
6.  Click "Generate Content".
7.  Review the proposed slides and click "Download PowerPoint".

#### Option 2: Text Input (Direct Content)

1.  Start the development servers (if not already running).
2.  Open your browser to `http://localhost:5173`.
3.  Upload a PowerPoint template (`.pptx`) or use the default template.
4.  Select the "Text Input" tab.
5.  Paste or type your content (up to 10,000 characters).
6.  Click "Generate from Text".
7.  The AI will automatically:
    - Structure your content into slides
    - Select appropriate layouts for each slide
    - Handle text overflow with smart strategies
    - Balance Two-Column layouts
8.  Review the proposed slides and click "Download PowerPoint".

**Text Input Features:**
- **AI Layout Selection**: Automatically chooses the best layout type for each slide
- **Overflow Management**: Detects and resolves text overflow using layout changes, page splits, or summarization
- **Two-Column Support**: Intelligently creates comparison slides with balanced columns
- **Timeout Protection**: 60-second processing limit with graceful error handling
- **Character Counter**: Real-time feedback on text length (0 / 10,000)

## 📚 Documentation

- [Contributing Guide](CONTRIBUTING.md) - Development setup and contribution guidelines
- [Architecture](docs/architecture.md) - System architecture and design
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## 📊 Project Status

- **Test Coverage**: Backend 93%, Frontend 93.47%
- **Test Success Rate**: 100% (74/74 backend, 24/24 frontend)
- **E2E Coverage**: 100% (Chromium, Firefox, WebKit)
- **Code Quality**: A+ (94/100)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

[MIT](LICENSE) - Copyright (c) 2026 PowerPoint Maker Contributors
