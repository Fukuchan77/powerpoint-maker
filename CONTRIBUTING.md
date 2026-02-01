# Contributing to PowerPoint Maker

Welcome! Thank you for your interest in contributing to the PowerPoint Maker project.

## 🚀 Development Environment Setup

### Prerequisites

- [mise](https://mise.jdx.dev/) (recommended) or:
  - Python 3.12+
  - Node.js 18+ (LTS)
  - pnpm 8+

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Fukuchan77/powerpoint-maker.git
cd powerpoint-maker
```

2. Install dependencies:

```bash
# Using mise (recommended)
mise install

# Or manually
cd backend && uv sync
cd ../frontend && pnpm install
```

3. Set up environment variables:

```bash
cd backend
cp .env.example .env
# Edit .env file to add your API keys
```

## 🏃 Running Development Servers

### Start Both Servers (Recommended)

```bash
mise run dev
```

### Start Individually

```bash
# Backend (port 8000)
cd backend
uv run fastapi dev app/main.py

# Frontend (port 5173)
cd frontend
pnpm dev
```

## 🧪 Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_generator.py

# Run tests with markers
uv run pytest -m "not slow"
```

**Coverage Target**: 90%+ (Current: Backend 93%, Frontend 93.47%)

### Frontend Tests

```bash
cd frontend

# Unit and integration tests
pnpm test

# With coverage
pnpm test -- --coverage

# E2E tests
pnpm test:e2e

# Specific browser only
pnpm test:e2e --project=chromium
```

## 📝 Coding Standards

### Backend (Python)

- **Formatter**: Ruff
- **Linter**: Ruff
- **Line Length**: 120 characters
- **Quote Style**: Double quotes

```bash
cd backend

# Check formatting
uv run ruff format --check .

# Apply formatting
uv run ruff format .

# Check linting
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .
```

### Frontend (TypeScript/React)

- **Formatter**: Prettier
- **Linter**: ESLint
- **Framework**: React 19 + Vite

```bash
cd frontend

# Check formatting
pnpm format

# Check linting
pnpm lint

# Auto-fix linting issues
pnpm lint --fix
```

## 🌳 Git Workflow

### Branch Naming Convention

```
feature/feature-name      New features
fix/issue-description     Bug fixes
docs/document-name        Documentation updates
refactor/target           Refactoring
test/test-target          Test additions/modifications
```

### Commit Messages

```
feat: add new feature
fix: fix bug
docs: update documentation
style: code style changes (no functional impact)
refactor: refactoring
test: add or modify tests
chore: build process or tool changes
```

### Pull Request Flow

1. **Create a branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Commit changes**

```bash
git add .
git commit -m "feat: add new feature"
```

3. **Run tests**

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && pnpm test
```

4. **Push and create PR**

```bash
git push origin feature/your-feature-name
```

5. **Include in PR description**:
   - Overview of changes
   - Related issue number
   - Test results
   - Screenshots (if UI changes)

## ✅ Pull Request Checklist

Before creating a PR, verify:

- [ ] All tests pass
- [ ] No linter/formatter errors
- [ ] Coverage maintained at 90%+
- [ ] Tests added for new features
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow convention
- [ ] Related issues are linked

## 🏗️ Project Structure

### Backend

```
backend/
├── app/
│   ├── api/          # FastAPI routes
│   ├── services/     # Business logic
│   ├── core/         # Core features (LLM, logging)
│   ├── models/       # Data models
│   ├── schemas.py    # Pydantic schemas
│   └── main.py       # Application entry point
└── tests/
    ├── unit/         # Unit tests
    └── integration/  # Integration tests
```

### Frontend

```
frontend/
├── src/
│   ├── components/   # React components
│   ├── utils/        # Utility functions
│   ├── types.ts      # TypeScript type definitions
│   └── App.tsx       # Main application
└── e2e/             # Playwright E2E tests
```

## 🐛 Bug Reports

When reporting a bug, please include:

1. **Bug description**: What is happening
2. **Steps to reproduce**: How to reproduce the issue
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: OS, browser, versions
6. **Screenshots**: If possible

## 💡 Feature Requests

We welcome feature proposals! Please create an issue including:

1. **Feature description**: What you want to achieve
2. **Use case**: When this would be useful
3. **Implementation ideas**: Technical approach (optional)
4. **Alternatives**: Other solutions (optional)

## 📚 Reference Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [BeeAI Framework](https://github.com/i-am-bee/bee-agent-framework)
- [python-pptx Documentation](https://python-pptx.readthedocs.io/)

## 🙏 Acknowledgments

Thank you for contributing to the project! Your contributions make PowerPoint Maker better.

## 📞 Support

If you have questions or issues:

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and discussions

---

Happy coding! 🚀
