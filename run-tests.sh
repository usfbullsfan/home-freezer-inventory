#!/bin/bash

# Parse arguments
TEST_SUITE="${1:-all}"  # Default to 'all' if no argument

# Validate argument
case "$TEST_SUITE" in
  backend|frontend|all)
    # Valid argument, continue
    ;;
  *)
    echo "Usage: ./run-tests.sh [backend|frontend|all]"
    echo ""
    echo "Examples:"
    echo "  ./run-tests.sh           # Run all tests (default)"
    echo "  ./run-tests.sh backend   # Run only backend tests"
    echo "  ./run-tests.sh frontend  # Run only frontend tests"
    exit 1
    ;;
esac

echo "================================"
echo "Freezer Inventory Tracker"
if [ "$TEST_SUITE" = "all" ]; then
    echo "Running All Tests"
else
    echo "Running ${TEST_SUITE^} Tests Only"
fi
echo "================================"
echo ""

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall success
BACKEND_PASSED=false
FRONTEND_PASSED=false
RUN_BACKEND=false
RUN_FRONTEND=false

# Determine which tests to run
if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "backend" ]; then
    RUN_BACKEND=true
fi

if [ "$TEST_SUITE" = "all" ] || [ "$TEST_SUITE" = "frontend" ]; then
    RUN_FRONTEND=true
fi

# Backend Tests
if [ "$RUN_BACKEND" = true ]; then
    echo -e "${YELLOW}Running Backend Tests...${NC}"
    echo "================================"
    cd backend

    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt

    if pytest -v; then
        echo -e "${GREEN}✓ Backend tests passed${NC}"
        BACKEND_PASSED=true
    else
        echo -e "${RED}✗ Backend tests failed${NC}"
        BACKEND_PASSED=false
    fi

    cd ..
    echo ""
    echo ""
else
    BACKEND_PASSED=true  # Not run, so don't count as failure
fi

# Frontend Tests
if [ "$RUN_FRONTEND" = true ]; then
    echo -e "${YELLOW}Running Frontend Tests...${NC}"
    echo "================================"
    cd frontend

    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    if npm test -- --run; then
        echo -e "${GREEN}✓ Frontend tests passed${NC}"
        FRONTEND_PASSED=true
    else
        echo -e "${RED}✗ Frontend tests failed${NC}"
        FRONTEND_PASSED=false
    fi

    cd ..
    echo ""
    echo ""
else
    FRONTEND_PASSED=true  # Not run, so don't count as failure
fi

# Summary
echo "================================"
echo "Test Summary"
echo "================================"

if [ "$RUN_BACKEND" = true ]; then
    if [ "$BACKEND_PASSED" = true ]; then
        echo -e "Backend:  ${GREEN}✓ PASSED${NC}"
    else
        echo -e "Backend:  ${RED}✗ FAILED${NC}"
    fi
fi

if [ "$RUN_FRONTEND" = true ]; then
    if [ "$FRONTEND_PASSED" = true ]; then
        echo -e "Frontend: ${GREEN}✓ PASSED${NC}"
    else
        echo -e "Frontend: ${RED}✗ FAILED${NC}"
    fi
fi

echo ""

# Exit with error if any tests failed
if [ "$BACKEND_PASSED" = true ] && [ "$FRONTEND_PASSED" = true ]; then
    if [ "$TEST_SUITE" = "all" ]; then
        echo -e "${GREEN}All tests passed!${NC}"
    else
        echo -e "${GREEN}${TEST_SUITE^} tests passed!${NC}"
    fi
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
fi
