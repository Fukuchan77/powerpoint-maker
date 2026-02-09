#!/bin/bash
set -e

echo "🔧 Setting up Git hooks for powerpoint-maker..."
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
  echo "❌ Error: Not in a git repository root"
  exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create pre-push hook
echo "📝 Creating pre-push hook..."
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook for powerpoint-maker
# Runs type checking, tests, and build verification before pushing

echo "🚀 Running pre-push checks..."
echo ""

# Change to repository root
cd "$(git rev-parse --show-toplevel)"

# Backend: Linting and fast unit tests
echo "📦 Backend: Linting and fast tests..."
cd backend

# Check if uv is available
if ! command -v uv &> /dev/null; then
  echo "❌ Error: uv is not installed. Please install it first."
  echo "   Visit: https://docs.astral.sh/uv/"
  exit 1
fi

# Run backend checks
if ! uv run ruff check .; then
  echo "❌ Backend linting failed"
  echo "💡 Fix with: mise run format"
  exit 1
fi

echo "   ✓ Linting passed"

# Run only fast unit tests (exclude integration tests)
if ! uv run pytest tests/unit -v --tb=short -x; then
  echo "❌ Backend unit tests failed"
  echo "💡 Run locally: cd backend && uv run pytest tests/unit -v"
  exit 1
fi

echo "   ✓ Unit tests passed"
cd ..

# Frontend: Type check, tests, and build verification
echo ""
echo "📦 Frontend: Type check, tests, and build..."
cd frontend

# Check if pnpm is available
if ! command -v pnpm &> /dev/null; then
  echo "❌ Error: pnpm is not installed. Please install it first."
  echo "   Visit: https://pnpm.io/installation"
  exit 1
fi

# Type check
if ! pnpm exec tsc --noEmit; then
  echo "❌ Frontend type check failed"
  echo "💡 Fix type errors and try again"
  exit 1
fi

echo "   ✓ Type check passed"

# Run tests
if ! pnpm test --run; then
  echo "❌ Frontend tests failed"
  echo "💡 Run locally: cd frontend && pnpm test"
  exit 1
fi

echo "   ✓ Tests passed"

# Build verification
if ! pnpm build; then
  echo "❌ Frontend build failed"
  echo "💡 Fix build errors and try again"
  exit 1
fi

echo "   ✓ Build passed"
cd ..

echo ""
echo "✅ All pre-push checks passed! Pushing to remote..."
echo ""
EOF

# Make hook executable
chmod +x .git/hooks/pre-push

echo "✅ Git hooks installed successfully!"
echo ""
echo "📋 Installed hooks:"
echo "  - pre-push: Runs before git push"
echo ""
echo "🔍 Pre-push hook will run:"
echo "  Backend:"
echo "    ✓ Ruff linting"
echo "    ✓ Fast unit tests (tests/unit)"
echo ""
echo "  Frontend:"
echo "    ✓ TypeScript type checking"
echo "    ✓ Vitest unit tests"
echo "    ✓ Build verification"
echo ""
echo "⏱️  Estimated time: 1-3 minutes"
echo ""
echo "💡 Tips:"
echo "  - To skip checks (not recommended): git push --no-verify"
echo "  - To run checks manually: mise run pre-push-check"
echo "  - Pre-commit hooks are managed by .pre-commit-config.yaml"
echo ""
echo "🎯 Next steps:"
echo "  1. Install pre-commit hooks: pre-commit install"
echo "  2. Test the setup: mise run pre-push-check"
echo ""