# Testing Guide

This guide covers running tests for the Freezer Inventory Tracker application.

## Table of Contents

- [Backend Tests (Python/Pytest)](#backend-tests)
- [Frontend Tests (Vitest/React Testing Library)](#frontend-tests)
- [Continuous Integration](#continuous-integration)
- [Writing New Tests](#writing-new-tests)
- [Test Coverage](#test-coverage)

## Backend Tests

### Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Activate virtual environment:
```bash
source venv/bin/activate
```

3. Install test dependencies:
```bash
pip install -r requirements.txt
```

### Running Backend Tests

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run specific test file:**
```bash
pytest tests/test_auth.py
```

**Run specific test:**
```bash
pytest tests/test_auth.py::test_login_success
```

**Run with coverage report:**
```bash
pytest --cov=. --cov-report=html
```

The coverage report will be generated in `htmlcov/index.html`.

### Backend Test Structure

```
backend/tests/
├── conftest.py          # Test fixtures and configuration
├── test_auth.py         # Authentication endpoint tests
├── test_items.py        # Items CRUD endpoint tests
└── test_categories.py   # Categories endpoint tests
```

### Backend Test Coverage

Current test coverage includes:

**Authentication (`test_auth.py`):**
- ✅ Successful login
- ✅ Invalid username/password
- ✅ Missing credentials
- ✅ Protected route access with/without token
- ✅ Password change functionality

**Items API (`test_items.py`):**
- ✅ Create item (with/without custom QR code)
- ✅ Get items (all, by ID, by QR code)
- ✅ Update item details
- ✅ Update item status (consume, throw out)
- ✅ Delete item (admin vs user permissions)
- ✅ Search and filter items
- ✅ Custom added date functionality
- ✅ Duplicate QR code prevention

**Categories API (`test_categories.py`):**
- ✅ Get all categories
- ✅ Create new category
- ✅ Update category
- ✅ Delete category (permissions)

### Example Test Output

```bash
$ pytest -v
=================== test session starts ===================
collected 35 items

tests/test_auth.py::test_login_success PASSED         [ 2%]
tests/test_auth.py::test_login_invalid_username PASSED [ 5%]
...
tests/test_items.py::test_create_item_success PASSED  [42%]
tests/test_items.py::test_get_items_after_creation PASSED [45%]
...
=================== 35 passed in 2.45s ===================
```

## Frontend Tests

### Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

### Running Frontend Tests

**Run all tests:**
```bash
npm test
```

**Run tests in watch mode:**
```bash
npm test -- --watch
```

**Run tests with UI:**
```bash
npm run test:ui
```

**Run with coverage:**
```bash
npm run test:coverage
```

**Run specific test file:**
```bash
npm test -- ItemCard.test.jsx
```

### Frontend Test Structure

```
frontend/src/
├── test/
│   └── setup.js                    # Test configuration
├── components/
│   └── __tests__/
│       └── ItemCard.test.jsx       # Component tests
└── vitest.config.js                # Vitest configuration
```

### Frontend Test Coverage

Current test coverage includes:

**ItemCard Component:**
- ✅ Renders item name and details
- ✅ Displays QR code
- ✅ Calculates days in freezer correctly
- ✅ Shows expiration warnings
- ✅ Handles negative days (clock skew)
- ✅ Edit button functionality
- ✅ Status change functionality
- ✅ Notes display

### Example Test Output

```bash
$ npm test

 ✓ src/components/__tests__/ItemCard.test.jsx (9 tests)
   ✓ renders item name
   ✓ renders item details
   ✓ displays QR code
   ✓ calculates days in freezer
   ...

Test Files  1 passed (1)
     Tests  9 passed (9)
  Start at  10:30:15
  Duration  1.23s
```

## Test Fixtures and Mocks

### Backend Fixtures (conftest.py)

The backend tests use pytest fixtures for common test data:

- `app` - Flask application with test configuration
- `client` - Test client for making requests
- `admin_token` - JWT token for admin user
- `user_token` - JWT token for regular user
- `auth_headers_admin` - Authorization headers for admin
- `auth_headers_user` - Authorization headers for user
- `sample_item` - Pre-created test item

**Example usage:**
```python
def test_get_items(client, auth_headers_admin):
    response = client.get('/api/items/', headers=auth_headers_admin)
    assert response.status_code == 200
```

### Frontend Test Utilities (setup.js)

The frontend tests include mocks for:

- `localStorage` - Browser local storage
- `window.matchMedia` - Media query matching

## Writing New Tests

### Backend Test Example

```python
def test_new_feature(client, auth_headers_admin):
    """Test description"""
    # Arrange
    test_data = {'name': 'Test Item'}

    # Act
    response = client.post('/api/items/',
        json=test_data,
        headers=auth_headers_admin
    )

    # Assert
    assert response.status_code == 201
    assert response.json['name'] == 'Test Item'
```

### Frontend Test Example

```javascript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('handles button click', () => {
    const mockHandler = vi.fn();
    render(<MyComponent onClick={mockHandler} />);
    fireEvent.click(screen.getByRole('button'));
    expect(mockHandler).toHaveBeenCalled();
  });
});
```

## Test Coverage

### Backend Coverage Goals

- **Overall**: > 80%
- **Critical paths** (auth, items CRUD): > 90%
- **Edge cases**: Cover error handling, validation, permissions

### Frontend Coverage Goals

- **Components**: > 70%
- **Critical user flows**: 100%
- **Edge cases**: Error states, loading states, empty states

### Viewing Coverage Reports

**Backend:**
```bash
cd backend
pytest --cov=. --cov-report=html
open htmlcov/index.html  # macOS
```

**Frontend:**
```bash
cd frontend
npm run test:coverage
open coverage/index.html  # macOS
```

## Continuous Integration

### Running All Tests

From the project root:

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest

# Frontend tests
cd ../frontend
npm test
```

### Pre-commit Checks

Before committing code, run:

```bash
# Backend
cd backend
pytest --cov=. --cov-report=term-missing

# Frontend
cd ../frontend
npm run test:coverage
```

Ensure:
- ✅ All tests pass
- ✅ Coverage meets minimum thresholds
- ✅ No linting errors

## Common Issues and Solutions

### Backend

**Issue:** `ModuleNotFoundError`
```bash
# Solution: Ensure you're in the backend directory and venv is activated
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Issue:** Database conflicts
```bash
# Solution: Tests use in-memory SQLite, but ensure no test.db files exist
rm -f test.db
```

### Frontend

**Issue:** `Cannot find module`
```bash
# Solution: Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Issue:** Tests timeout
```bash
# Solution: Increase timeout in vitest.config.js
test: {
  testTimeout: 10000
}
```

## Test Data

### Default Test Users

**Admin User:**
- Username: `admin`
- Password: `admin123`
- Role: `admin`

**Regular User:**
- Username: `testuser`
- Password: `test123`
- Role: `user`

### Default Test Categories

1. Beef (365 days)
2. Chicken (270 days)
3. Pork (180 days)
4. Fish (180 days)

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Test names should describe what they test
3. **AAA Pattern**: Arrange, Act, Assert
4. **Mock External Services**: Don't rely on real APIs or databases
5. **Test Edge Cases**: Invalid input, missing data, permission errors
6. **Keep Tests Fast**: Use in-memory databases, avoid unnecessary delays
7. **Update Tests with Code**: Keep tests in sync with implementation

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://testingjavascript.com/)

## Getting Help

If you encounter issues:

1. Check this documentation
2. Review test examples in `tests/` directories
3. Check test output for error messages
4. Verify all dependencies are installed
5. Create an issue on GitHub with:
   - Test command used
   - Full error output
   - Environment details (OS, Python/Node version)
