#!/bin/bash

echo "================================"
echo "Freezer Inventory Tracker"
echo "Running All Tests"
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

# Backend Tests
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

echo ""
echo ""

# Frontend Tests
echo -e "${YELLOW}Running Frontend Tests...${NC}"
echo "================================"
cd ../frontend

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

echo ""
echo ""

# Summary
echo "================================"
echo "Test Summary"
echo "================================"

if [ "$BACKEND_PASSED" = true ]; then
    echo -e "Backend:  ${GREEN}✓ PASSED${NC}"
else
    echo -e "Backend:  ${RED}✗ FAILED${NC}"
fi

if [ "$FRONTEND_PASSED" = true ]; then
    echo -e "Frontend: ${GREEN}✓ PASSED${NC}"
else
    echo -e "Frontend: ${RED}✗ FAILED${NC}"
fi

echo ""

# Exit with error if any tests failed
if [ "$BACKEND_PASSED" = true ] && [ "$FRONTEND_PASSED" = true ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
fi
