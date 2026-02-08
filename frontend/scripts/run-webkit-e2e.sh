#!/bin/bash

# Webkit E2E Test Execution Script
# This script runs E2E tests specifically for Webkit browser with comprehensive logging

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$FRONTEND_DIR")"

echo "=========================================="
echo "Webkit E2E Test Execution"
echo "=========================================="
echo "Time: $(date)"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "Checking backend server..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running${NC}"
else
    echo -e "${RED}✗ Backend server is not running${NC}"
    echo "Please start the backend server first:"
    echo "  cd backend && uv run uvicorn app.main:app --reload"
    exit 1
fi

# Check if frontend is running
echo "Checking frontend server..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend server is running${NC}"
else
    echo -e "${RED}✗ Frontend server is not running${NC}"
    echo "Please start the frontend server first:"
    echo "  cd frontend && pnpm dev"
    exit 1
fi

echo ""
echo "=========================================="
echo "Installing Playwright browsers (if needed)"
echo "=========================================="
cd "$FRONTEND_DIR"
pnpm exec playwright install webkit

echo ""
echo "=========================================="
echo "Running Webkit E2E Tests"
echo "=========================================="

# Run tests with detailed output
TEST_EXIT_CODE=0
pnpm exec playwright test --project=webkit --reporter=list,html || TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All Webkit E2E tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
fi

# Generate report location
echo ""
echo "HTML Report available at: file://$FRONTEND_DIR/playwright-report/index.html"

# Show test results summary
if [ -f "$FRONTEND_DIR/test-results/.last-run.json" ]; then
    echo ""
    echo "Last run summary:"
    cat "$FRONTEND_DIR/test-results/.last-run.json" 2>/dev/null || echo "Summary not available"
fi

echo ""
echo "=========================================="
echo "Webkit-Specific Feedback Collection"
echo "=========================================="
echo ""
echo "Please review the following aspects in Webkit:"
echo "1. File upload functionality"
echo "2. Form interactions and validation"
echo "3. Button clicks and navigation"
echo "4. File download triggers"
echo "5. Error message displays"
echo "6. Loading states and spinners"
echo "7. Responsive behavior"
echo ""
echo "Known Webkit-specific considerations:"
echo "- Webkit has stricter security policies for file operations"
echo "- Download behavior may differ from Chromium"
echo "- Form validation timing might be different"
echo "- Event handling order can vary"
echo ""

exit $TEST_EXIT_CODE