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
3.  **Setup Git hooks** (recommended):

    ```bash
    # Install pre-commit hooks (runs on commit)
    pre-commit install

    # Install pre-push hooks (runs before push)
    mise run setup-hooks
    # or alternatively:
    ./scripts/setup-git-hooks.sh
    ```

### Configuration

Create a `.env` file in the `backend` directory based on `.env.example`:

#### LLM Provider Configuration

| Variable             | Required    | Description                                                     | Default                             |
| -------------------- | ----------- | --------------------------------------------------------------- | ----------------------------------- |
| `LLM_PROVIDER`       | No          | LLM provider to use                                             | `ollama`                            |
| `LLM_MODEL`          | No          | LLM model name                                                  | `llama3.1`                          |
| `WATSONX_API_KEY`    | Conditional | API Key for IBM watsonx (required if `LLM_PROVIDER=watsonx`)    | -                                   |
| `WATSONX_PROJECT_ID` | Conditional | Project ID for IBM watsonx (required if `LLM_PROVIDER=watsonx`) | -                                   |
| `WATSONX_URL`        | No          | IBM watsonx API endpoint                                        | `https://us-south.ml.cloud.ibm.com` |
| `OPENAI_API_KEY`     | Conditional | API Key for OpenAI (required if `LLM_PROVIDER=openai`)          | -                                   |

#### Server Configuration

| Variable           | Required | Description                            | Default                 |
| ------------------ | -------- | -------------------------------------- | ----------------------- |
| `HOST`             | No       | Server host address                    | `0.0.0.0`               |
| `PORT`             | No       | Server port number                     | `8000`                  |
| `DEBUG`            | No       | Debug mode                             | `false`                 |
| `CORS_ORIGINS`     | No       | Allowed CORS origins (comma-separated) | `http://localhost:5173` |
| `MAX_UPLOAD_SIZE`  | No       | Maximum file upload size (bytes)       | `10485760` (10MB)       |
| `RESEARCH_TIMEOUT` | No       | Research operation timeout (seconds)   | `180`                   |
| `LOG_LEVEL`        | No       | Logging level                          | `INFO`                  |

#### LLM Provider Setup

This project uses the BeeAI Framework, which supports multiple LLM providers.

##### Option 1: Ollama (Default - Local)

1. Install [Ollama](https://ollama.ai/)
2. Pull a model: `ollama pull llama3.1`
3. Start Ollama service (runs on `http://localhost:11434` by default)
4. No `.env` configuration needed (uses defaults)

##### Option 2: IBM watsonx

1. Sign up at [IBM Cloud](https://cloud.ibm.com/)
2. Create a watsonx.ai project
3. Get your API key and Project ID from the credentials page
4. Configure in `.env`:
   ```bash
   LLM_PROVIDER=watsonx
   LLM_MODEL=ibm/granite-13b-chat-v2
   WATSONX_API_KEY=your-api-key-here
   WATSONX_PROJECT_ID=your-project-id-here
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   ```

##### Option 3: OpenAI

1. Get API key from [OpenAI Platform](https://platform.openai.com/)
2. Configure in `.env`:
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4
   OPENAI_API_KEY=your-openai-api-key-here
   ```

**Provider Selection:**

The LLM provider is configured via environment variables:

- `LLM_PROVIDER`: Specify the provider to use (`ollama`, `watsonx`, or `openai`)
- `LLM_MODEL`: Specify the model name (e.g., `llama3.1` for Ollama, `gpt-4` for OpenAI)

**Default**: If not specified, defaults to `ollama` with `llama3.1` model.

**Examples**:

```bash
# Use Ollama (default)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1

# Use IBM watsonx
LLM_PROVIDER=watsonx
LLM_MODEL=ibm/granite-13b-chat-v2

# Use OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
```

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

## � CI/CD Workflow

This project uses a 3-stage quality assurance approach:

### 1. Pre-commit (Local - Before Commit) ⚡

**Time: 5-15 seconds**

Automatically runs on `git commit`:

- Backend: Ruff linting and formatting
- Frontend: Biome linting and formatting
- General: Trailing whitespace, YAML/JSON validation

Managed by `.pre-commit-config.yaml`.

### 2. Pre-push (Local - Before Push) 🚀

**Time: 1-3 minutes**

Automatically runs on `git push`:

- Backend: Ruff linting + fast unit tests
- Frontend: TypeScript type checking + tests + build verification

**Install**: `mise run setup-hooks` or `./scripts/setup-git-hooks.sh`

**Manual run**: `mise run pre-push-check`

**Skip** (not recommended): `git push --no-verify`

### 3. GitHub Actions CI (Remote - After Push) ☁️

**Time: 5-15 minutes**

Runs on all branches and pull requests:

- Linting and formatting checks
- Backend: Full test suite + coverage
- Frontend: Full test suite + coverage
- E2E tests (Chromium)
- Build verification

### Available Commands

```bash
# Test commands
mise run test-fast        # Fast unit tests only (1-3 min)
mise run test-full        # All tests including integration (5-10 min)

# Check commands
mise run build-check      # Verify build works
mise run pre-push-check   # Run same checks as pre-push hook

# Setup
mise run setup-hooks      # Install git pre-push hooks

# Individual tasks
mise run backend:lint     # Lint backend only
mise run backend:test     # Test backend only
mise run frontend:lint    # Lint frontend only
mise run frontend:test    # Test frontend only
```

## �📄 License

[MIT](LICENSE) - Copyright (c) 2026 PowerPoint Maker Contributors
