FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini
COPY ./create_test_user.py ./create_test_user.py

# Expose port
ENV BACKEND_PORT=8000
EXPOSE ${BACKEND_PORT}

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload"]
