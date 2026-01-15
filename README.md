# NewsWatcher

A modern full-stack web application with authentication, built with FastAPI and React.

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Database
- **fastapi-users** - Authentication system
- **fastCRUD** - CRUD operations
- **SQLAlchemy** - ORM
- **uv** - Package manager

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
VITE_API_URL=/api
```

3. **Build and run**
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

## Project Structure

```
newswatcher/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── api/              # API routes
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
│   └── nginx.conf            # nginx reverse proxy config
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
- `GET /api/users/me` - Get current user

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
- `BACKEND_CORS_ORIGINS` - Allowed CORS origins (JSON array)
- `ENVIRONMENT` - Environment (development/production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 1440 = 24 hours)

### Frontend
- `VITE_API_URL` - Backend API URL (use `/api` for production, `http://localhost/api` for dev)

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- HTTP-only cookies (when implemented)
- CORS protection
- SQL injection protection via SQLAlchemy ORM

## Troubleshooting

**Port conflicts:**
```bash
# Stop all containers
make down

# Check if ports are in use
lsof -i :80
lsof -i :8000
lsof -i :3000
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
