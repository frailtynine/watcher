# Test Infrastructure

## Overview

This test infrastructure is designed to be:
- **Robust**: Uses PostgreSQL for tests (same as production)
- **Simple**: Minimal configuration, easy to understand
- **Universal**: Works in development and CI/CD (GitHub Actions)

## Architecture

### Test Database
- Uses a separate PostgreSQL database: `newswatcher_test`
- Automatically creates and drops tables for each test
- Runs in the same Docker container as development database
- No manual setup required

### Key Components

1. **conftest.py** - Test fixtures
   - `event_loop`: Session-scoped event loop
   - `db_engine`: Creates/tears down test database per test
   - `db_session`: Provides clean database session
   - `client`: HTTP client for API testing

2. **test_models.py** - Model creation tests
   - Tests basic model creation
   - Validates relationships
   - Checks constraints

## Running Tests

### Locally (Development)

```bash
# Start the development environment first
make dev

# Run all tests
make test

# Run specific test file
make test-unit FILE=tests/test_models.py

# Run with coverage
make test-coverage
```

### In CI/CD (GitHub Actions)

The same commands work in CI/CD because:
- Test database runs in Docker (portable)
- Configuration uses environment variables
- No external dependencies

Example GitHub Actions workflow:

```yaml
- name: Start services
  run: docker-compose -f docker-compose.dev.yml up -d db

- name: Run tests
  run: docker-compose -f docker-compose.dev.yml exec -T backend pytest tests/ -v
```

## Writing Tests

### Model Tests

```python
@pytest.mark.asyncio
async def test_create_model(db_session):
    """Test creating a model."""
    obj = MyModel(field="value")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    
    assert obj.id is not None
    assert obj.field == "value"
```

### API Tests

```python
@pytest.mark.asyncio
async def test_api_endpoint(client):
    """Test an API endpoint."""
    response = await client.get("/api/endpoint")
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

## Best Practices

1. **Use PostgreSQL for tests**: Matches production environment
2. **Clean state per test**: Each test gets fresh tables
3. **Async all the way**: Use `@pytest.mark.asyncio` and `async def`
4. **Mark slow tests**: Use `@pytest.mark.slow` for integration tests
5. **Keep tests isolated**: Don't depend on test execution order

## Troubleshooting

### Database connection errors
```bash
# Ensure database is running
docker-compose -f docker-compose.dev.yml ps db

# Check database logs
docker-compose -f docker-compose.dev.yml logs db
```

### Tests hang
- Check event loop fixture scope
- Ensure all async functions use `await`
- Verify database session is properly closed

### Import errors
```bash
# Make sure you're running tests from Docker
docker-compose -f docker-compose.dev.yml exec backend pytest tests/
```

## Test Database

The test database (`newswatcher_test`) is automatically:
- Created when first test runs
- Cleaned between tests
- Shared across all tests in same run
- Isolated from development database

No manual database setup needed!
