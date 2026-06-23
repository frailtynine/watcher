# NewsWatcher

A full-stack news monitoring app with authentication, automated ingestion, AI filtering, and Telegram delivery, built with FastAPI and React.

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Database
- **fastapi-users** - Authentication system
- **fastCRUD** - CRUD operations
- **SQLAlchemy** - ORM
- **uv** - Package manager
- **APScheduler** - Background jobs
- **Google Gemini** - AI filtering and newspaper updates
- **Telethon + python-telegram-bot** - Telegram ingestion and bot delivery

### Frontend
- **React** with TypeScript
- **Chakra UI** - Component library
- **RTK Query** - API state management
- **Vite** - Build tool

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **nginx** - Reverse proxy

## Quick Start

### Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd newswatcher
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Start development environment**
```bash
make dev
# OR
make up
```

This will:
- Build all Docker containers
- Start PostgreSQL database
- Run database migrations automatically
- Start the backend API
- Start the frontend development server
- Start nginx reverse proxy

4. **Access the application**
- Frontend: http://localhost
- Backend API: http://localhost/api
- API Docs: http://localhost/docs

### Production

1. **Create production environment file**
```bash
cp .env.example .env
```

2. **Update .env for production**
```bash
# Edit .env and set:
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-secure-secret-key-min-32-chars
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
ENVIRONMENT=production
BACKEND_PORT=8000
FRONTEND_PORT=80
VITE_API_URL=/api
```

3. **Build and run**
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

Production compose now stays closer to the source deployment setup: long-running services restart automatically, the frontend receives `VITE_API_URL` during the image build, PostgreSQL runs the bundled init script on a fresh volume, and nginx resolves upstream ports from environment variables at container start.

## Project Structure

```
newswatcher/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── api/              # API routes
│   │   ├── ai/               # AI consumer and providers
│   │   ├── delivery/         # Newspaper + Telegram delivery runtime
│   │   ├── producers/        # RSS/Telegram source producers
│   │   ├── core/             # Core configuration
│   │   └── db/               # Database setup
│   ├── alembic/              # Database migrations
│   ├── pyproject.toml        # Python dependencies
│   ├── alembic.ini           # Alembic config
│   ├── create_test_user.py   # Utility script
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── features/         # Feature modules
│   │   │   └── auth/         # Authentication
│   │   ├── services/         # API services
│   │   │   └── api.ts        # RTK Query API
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf.template   # nginx reverse proxy template
├── .github/workflows/
│   └── ci-cd.yml             # CI/CD pipeline
├── docker-compose.dev.yml    # Development compose
├── docker-compose.prod.yml   # Production compose
├── Makefile                  # Development commands
├── .env                      # Environment variables (gitignored)
├── .env.example              # Environment template
└── README.md
```

## Development Workflow

### Using Make Commands

The project includes a Makefile for common tasks:

```bash
# Start development environment
make dev

# View all services status
make status

# View logs
make logs              # All services
make logs-backend      # Backend only
make logs-frontend     # Frontend only

# Stop services
make down

# Clean everything (removes volumes)
make clean

# Rebuild from scratch
make rebuild
```

### Database Migrations

Migrations are automatically applied when you start the dev environment. To manage migrations manually:

```bash
# Create a new migration
make migrate-create MSG="add user profile table"

# Apply pending migrations
make migrate-upgrade

# Rollback last migration
make migrate-downgrade

# View migration history
make migrate-history

# View current migration
make migrate-current
```

### Backend Development

The backend runs with hot-reload enabled. Any changes to Python files in `backend/app/` will automatically restart the server.

**Access backend shell:**
```bash
make backend-shell
```

**Create a test user:**
```bash
make test-user
# Creates: test@example.com / password123
```

### Frontend Development

The frontend runs with Vite's hot module replacement. Changes to React components will be reflected immediately.

### Testing & Linting

```bash
make test
make test-unit FILE=tests/test_models.py
make test-coverage
make lint
```

On a fresh PostgreSQL volume, `docker/postgres/init.sql` creates `newswatcher_test` automatically. If your local database volume already existed before that script was added, recreate it with `make clean` or create the test database manually once in `psql`.

### Database Management

**Access PostgreSQL:**
```bash
make db-shell
```

**View logs:**
```bash
make logs
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/jwt/login` - Login (returns JWT token)
- `POST /api/auth/jwt/logout` - Logout
- `GET /api/users/me` - Get current user with masked/derived settings
- `PATCH /api/users/me` - Update current user settings and encrypt sensitive credentials before save

Sensitive settings are never returned as plaintext. Example response shape:

```json
{
  "settings": {
    "gemini_api_key": true,
    "telegram_bots": [
      {
        "id": 1,
        "bot_name": "newswatcher_bot",
        "bot_tg_id": "123456789",
        "is_active": true
      }
    ]
  }
}
```

### Core domain endpoints
- `/api/sources` - Create/list/update/delete sources (RSS and Telegram)
- `/api/news-tasks` - CRUD for filtering tasks
- `/api/associations` - Source-to-task associations
- `/api/news-items` - News items and per-task processing results
- `/api/newspapers` - Read/regenerate task newspaper
- `/api/telegram-bots` - Connect/disconnect Telegram bots
- `/api/news-tasks/{task_id}/telegram-bots/*` - Attach bots to tasks

### Documentation
- `/docs` - Swagger UI
- `/redoc` - ReDoc

## Environment Variables

All environment variables are configured in a single `.env` file in the root directory.

### Database
- `POSTGRES_USER` - PostgreSQL username (default: postgres)
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_DB` - Database name (default: newswatcher)
- `DATABASE_URL` - Full database connection string

### Backend
- `SECRET_KEY` - Secret key for JWT tokens (min 32 characters)
- `ENCRYPTION_KEY` - Fernet key used to encrypt user credentials in `user.settings`
- `BACKEND_GEMINI_API_KEY` - Backend-level Gemini key (used for newspaper generation)
- `BACKEND_CORS_ORIGINS` - Allowed CORS origins (JSON array)
- `ENVIRONMENT` - Environment (development/production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 1440 = 24 hours)
- `BACKEND_PORT` - Backend service port (default: 8000)
- `TELEGRAM_MANAGER_CHECK_INTERVAL_SECONDS` - User producer manager loop interval
- `TELEGRAM_APPS_MANAGER_CHECK_INTERVAL_SECONDS` - Telegram bot apps manager loop interval

### Frontend
- `FRONTEND_PORT` - Frontend service port (3000 for dev, set 80 for production compose)
- `VITE_API_URL` - Backend API URL (use `/api` for production, `http://localhost/api` for dev)

Production note:
- Always set `VITE_API_URL=/api` in production to avoid mixed-content (`https` page calling `http` API) errors.

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- HTTP-only cookies (when implemented)
- CORS protection
- Sensitive user settings are encrypted before they are stored in the database
- `/api/users/me` never returns secret values; it returns presence flags and derived bot metadata
- SQL injection protection via SQLAlchemy ORM

## CI/CD

GitHub Actions workflow is defined in `.github/workflows/ci-cd.yml`.

Pipeline behavior:
- On pull requests to `main`: run backend lint/tests and frontend production build
- On push to `main`: run CI, build/push ARM64 backend and frontend Docker images, then deploy on server

Required GitHub repository secrets:
- `SERVER_HOST`
- `SERVER_USER`
- `SSH_PRIVATE_KEY`
- `SSH_KEY_PASSPHRASE` (required if `SSH_PRIVATE_KEY` is encrypted)
- `SERVER_APP_PATH` (absolute path to this repo on server)
- `SERVER_PORT` (optional, defaults to `22`)
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `DOCKERHUB_BACKEND_IMAGE` (e.g. `org/newswatcher-backend`)
- `DOCKERHUB_FRONTEND_IMAGE` (e.g. `org/newswatcher-frontend`)

Deploy step runs:
- Uploads `docker-compose.prod.yml` from CI to server automatically
- Exports `BACKEND_IMAGE=<backend-image>:<commit-sha>`
- Exports `FRONTEND_IMAGE=<frontend-image>:<commit-sha>`
- `docker-compose -f docker-compose.prod.yml pull`
- `docker-compose -f docker-compose.prod.yml up -d --remove-orphans`

Server note:
- `.env` must already exist on the server (it is not managed by CI/CD)
- `docker-compose.prod.yml` expects `BACKEND_IMAGE` and `FRONTEND_IMAGE` env vars at deploy time
- Docker image builds in CI target `linux/arm64`
- Production nginx publishes host port `${BACKEND_PORT}` (e.g. `8200`) to container port `80`

## Troubleshooting

**Port conflicts:**
```bash
# Stop all containers
make down

# Check if ports are in use
lsof -i :80
lsof -i :$BACKEND_PORT
lsof -i :$FRONTEND_PORT
```

**Database connection issues:**
```bash
# Check database health
make status

# View database logs
make logs
```

**Clear everything and restart:**
```bash
make clean
make dev
```

## License

MIT
