# PowerPoint Maker Troubleshooting Guide

## 🔧 Common Issues and Solutions

Last Updated: February 1, 2026

## 📋 Table of Contents

1. [Installation & Setup Issues](#installation--setup-issues)
2. [Backend Issues](#backend-issues)
3. [Frontend Issues](#frontend-issues)
4. [Testing Issues](#testing-issues)
5. [Performance Issues](#performance-issues)
6. [Known Issues](#known-issues)

---

## Installation & Setup Issues

### Issue: `ModuleNotFoundError: Optional module [duckduckgo] not found`

**Symptoms**:

```bash
ModuleNotFoundError: No module named 'ddgs'
```

**Cause**: Missing optional dependencies for BeeAI Framework

**Solution**:

```bash
cd backend

# Verify pyproject.toml has correct dependency
# "beeai-framework[duckduckgo]>=0.1.76"

# Reinstall dependencies
uv sync --reinstall

# Or install specific package
uv pip install 'beeai-framework[duckduckgo]>=0.1.76'
```

### Issue: `mise install` fails

**Symptoms**:

```bash
mise install failed: python@3.12 not found
```

**Solution**:

1. **Option 1: Install with mise**

```bash
mise install python@3.12
mise install node@20
```

2. **Option 2: Manual installation**

```bash
# Python 3.12+
brew install python@3.12  # macOS
# or visit https://www.python.org/downloads/

# Node.js 18+
brew install node@20  # macOS
# or visit https://nodejs.org/

# pnpm
npm install -g pnpm
```

---

## Backend Issues

### Issue: FastAPI server won't start

**Symptoms**:

```bash
ImportError: cannot import name 'X' from 'app'
```

**Solution**:

1. **Verify virtual environment**:

```bash
cd backend
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync
```

2. **Set up environment variables**:

```bash
cp .env.example .env
# Edit .env file to add your API keys
```

3. **Reinstall dependencies**:

```bash
uv sync --reinstall
```

### Issue: `AttributeError: 'dict' object has no attribute 'title'`

**Symptoms**:

```python
AttributeError: 'dict' object has no attribute 'title'
```

**Location**: `app/api/routes.py:82`

**Cause**: ResearchAgent returns a dictionary, but code expects SlideContent object

**Solution**: Add type checking

```python
# app/api/routes.py
from app.schemas import SlideContent

for i, slide in enumerate(slides):
    # Convert dict to SlideContent if needed
    if isinstance(slide, dict):
        slide_obj = SlideContent(**slide)
    else:
        slide_obj = slide

    print(f"[API] Slide {i + 1}: {slide_obj.title}")
```

### Issue: LLM response parsing error

**Symptoms**:

```python
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Location**: `app/services/research.py`

**Cause**: LLM response is not in JSON format

**Solution**: Fallback processing executes automatically, but can be improved:

```python
# Implement more robust parsing
def _extract_json_from_response(self, content: str) -> dict:
    # 1. Extract from Markdown code blocks
    # 2. Parse JSON
    # 3. Fallback (mock data)
```

### Issue: Template upload error

**Symptoms**:

```
422 Unprocessable Entity
```

**Cause**: File size or format restrictions

**Constraints**:

- Maximum file size: 50MB
- Supported format: `.pptx` only
- MIME type: `application/vnd.openxmlformats-officedocument.presentationml.presentation`

**Solution**:

1. Check file size
2. Verify file is .pptx format
3. Ensure file is not corrupted

---

## Frontend Issues

### Issue: `pnpm install` fails

**Symptoms**:

```bash
ERR_PNPM_FETCH_404
```

**Solution**:

```bash
cd frontend

# Clear cache
pnpm store prune

# Reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Issue: Development server won't start

**Symptoms**:

```
Error: Cannot find module 'vite'
```

**Solution**:

```bash
cd frontend

# Verify dependencies
pnpm install

# If port is in use
pnpm dev --port 5174

# Or clean environment
rm -rf node_modules .vite dist
pnpm install
```

### Issue: CORS error

**Symptoms**:

```
Access to XMLHttpRequest at 'http://localhost:8000/api/...'
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Cause**: Backend CORS configuration

**Solution**: Verify `backend/app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Timeout error

**Symptoms**:

```
Error: timeout of 180000ms exceeded
```

**Cause**: Slow LLM response

**Solution**: This is normal behavior. LLM takes 30-120 seconds to generate content.

- Timeout is set to 180 seconds (3 minutes)
- To extend timeout if needed:

```typescript
// frontend/src/components/TopicInput.tsx
const response = await axios.post('/api/research', null, {
  params: { topic },
  timeout: 300000, // Extend to 5 minutes
})
```

---

## Testing Issues

### Issue: Backend tests fail

**Symptoms**:

```bash
FAILED tests/unit/test_research_agent.py::test_research_agent_parses_chart_data
```

**Cause**: Mock configuration issues

**Solution**:

```bash
cd backend

# Run tests individually
uv run pytest tests/unit/test_research_agent.py -v

# Show detailed logs
uv run pytest tests/unit/test_research_agent.py -v -s

# Run specific test only
uv run pytest -k "test_research_agent_parses_chart_data" -v
```

### Issue: Frontend tests fail

**Symptoms**:

```
Expected: { params: { topic: 'Test Topic' } }
Received: { params: { topic: 'Test Topic' }, timeout: 180000 }
```

**Solution**: Update test expectations

```typescript
// frontend/src/components/__tests__/TopicInput.test.tsx
expect(axios.post).toHaveBeenCalledWith('/api/research', null, {
  params: { topic: 'Test Topic' },
  timeout: 180000, // Add this line
})
```

### Issue: E2E tests timeout

**Symptoms**:

```
Timeout 30000ms exceeded
```

**Solution**:

```typescript
// playwright.config.ts
export default defineConfig({
  timeout: 60000, // Extend to 60 seconds
  use: {
    navigationTimeout: 30000,
  },
})
```

---

## Performance Issues

### Issue: Slow presentation generation

**Symptoms**: Generation takes 2+ minutes

**Causes**:

1. LLM API response time
2. DuckDuckGo search time
3. Image retrieval

**Optimization Methods**:

1. **Implement caching** (future enhancement):

```python
# Cache template analysis results with Redis
```

2. **Parallel processing** (future enhancement):

```python
# Generate slides in parallel
```

3. **Progress display**:

```typescript
// Display progress in frontend
```

### Issue: High memory usage

**Symptoms**: Process consumes large amounts of memory

**Cause**: Processing large PPTX files

**Solution**:

1. Limit file size (currently 50MB)
2. Release resources after processing
3. Use memory profiling tools:

```bash
# Check backend memory usage
cd backend
uv run python -m memory_profiler app/services/generator.py
```

---

## Known Issues

### 1. ResearchAgent LLM Response Parsing

**Status**: ⚠️ In Progress

**Issue**: Mock LLM responses may not parse correctly

**Workaround**: Fallback processing generates mock slides

**Roadmap**: Improvements planned for Phase 2

### 2. FastAPI Deprecation Warnings

**Status**: 🟡 Low Priority

**Warning**:

```
on_event is deprecated, use lifespan event handlers
```

**Impact**: None (works with current version)

**Plan**: Will migrate in next major update

### 3. TopicInput.tsx Coverage

**Status**: 🟡 Improvement Recommended

**Current**: 84.37% coverage

**Target**: 90%+

**Plan**: Next sprint

---

## 🆘 Support

### If Issues Persist

1. **Check logs**:

```bash
# Backend
cd backend && uv run fastapi dev app/main.py

# Frontend
cd frontend && pnpm dev
```

2. **Enable detailed debugging**:

```bash
# Backend debug mode
cd backend
DEBUG=1 uv run fastapi dev app/main.py

# Frontend debug mode
cd frontend
VITE_DEBUG=true pnpm dev
```

3. **Create GitHub Issue**:

- [Issue Template](https://github.com/Fukuchan77/powerpoint-maker/issues/new)
- Include: bug details, reproduction steps, environment info

4. **Ask the community**:

- [GitHub Discussions](https://github.com/Fukuchan77/powerpoint-maker/discussions)

---

## 📚 Related Documentation

- [Architecture](./architecture.md)
- [Development Guide](../CONTRIBUTING.md)
- [README](../README.md)

---

**Last Updated**: February 1, 2026  
**Maintainers**: Project Team
