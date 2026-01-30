# Backend - PowerPoint Maker

This is the FastAPI-based backend for the PowerPoint Maker application.

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.12+
- **Agent Framework**: BeeAI Framework
- **PPTX Processing**: python-pptx
- **Testing**: Pytest

## Setup

1.  Install dependencies (using `uv` is recommended):
    ```bash
    uv sync
    ```

## Scripts

- `uv run fastapi dev app/main.py`: Start the development server.
- `uv run pytest`: Run tests.
- `uv run ruff check .`: Lint code.
- `uv run ruff format .`: Format code.

## API Endpoints

- `POST /api/analyze-template`: Analyze a PPTX template structure.
- `POST /api/research`: Research a topic and generate slide content.
- `POST /api/generate`: Generate the final PPTX file.

## Testing

We use **Pytest** for testing.

```bash
uv run pytest
```

### Test Directory Structure

- `tests/unit`: Unit tests for services and logical components.
- `tests/integration`: API integration tests.
