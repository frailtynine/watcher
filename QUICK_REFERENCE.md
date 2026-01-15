# Quick Reference Guide

## Starting the Application

```bash
# Development (with hot-reload and auto-migrations)
make dev

# Production
docker-compose -f docker-compose.prod.yml up --build -d
```

## Make Commands

```bash
# Development
make dev              # Start all services
make up               # Alias for dev
make down             # Stop all services
make restart          # Restart services
make rebuild          # Clean and rebuild everything
make clean            # Remove all containers and volumes
make status           # Show service status
make ps               # Alias for status

# Logs
make logs             # View all logs
make logs-backend     # Backend logs only
make logs-frontend    # Frontend logs only

# Migrations
make migrate-create MSG="description"  # Create new migration
make migrate-upgrade                    # Apply migrations
make migrate-downgrade                  # Rollback last migration
make migrate-history                    # Show migration history
make migrate-current                    # Show current revision

# Database
make db-shell         # Access PostgreSQL shell
make backend-shell    # Access backend container shell

# Utilities
make test-user        # Create test user (test@example.com / password123)
make help             # Show all commands
```

## Accessing the Application

- **Frontend:** http://localhost
- **API Documentation:** http://localhost/docs
- **Backend API:** http://localhost/api/*

## Common Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
```

### Stop Services
```bash
docker-compose -f docker-compose.dev.yml down

# Remove volumes too
docker-compose -f docker-compose.dev.yml down -v
```

### Rebuild After Changes
```bash
# Just restart (for code changes - hot-reload will pick up)
docker-compose -f docker-compose.dev.yml restart backend

# Full rebuild (for dependency changes)
docker-compose -f docker-compose.dev.yml up --build
```

### Database Access
```bash
# PostgreSQL CLI
docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d newswatcher
```

### Backend Shell
```bash
docker-compose -f docker-compose.dev.yml exec backend sh
```

## API Endpoints

### Authentication
```bash
# Register user
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost/api/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"

# Get current user (requires token)
curl http://localhost/api/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Environment Variables

All environment variables are in the root `.env` file:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=newswatcher
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/newswatcher

# Backend
SECRET_KEY=dev-secret-key-change-in-production
BACKEND_CORS_ORIGINS=["http://localhost"]
ENVIRONMENT=development
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Frontend
VITE_API_URL=http://localhost/api
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 80
lsof -i :80

# Stop all containers
docker-compose -f docker-compose.dev.yml down
```

### Database Connection Issues
```bash
# Check database health
docker-compose -f docker-compose.dev.yml ps db

# View database logs
docker-compose -f docker-compose.dev.yml logs db
```

### Clean Slate
```bash
# Remove everything and start fresh
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up --build
```

## Project Structure

```
backend/app/
  ├── api/          # API routes
  ├── core/         # Configuration, auth
  ├── db/           # Database setup
  ├── models/       # SQLAlchemy models
  └── schemas/      # Pydantic schemas

frontend/src/
  ├── components/   # Reusable components
  ├── features/     # Feature modules
  ├── services/     # API services (RTK Query)
  └── App.tsx       # Main app component
```

## Testing the Setup

```bash
# 1. Check all services are running
docker-compose -f docker-compose.dev.yml ps

# 2. Test frontend
curl http://localhost | grep NewsWatcher

# 3. Test backend
curl http://localhost/docs | grep Swagger

# 4. Test health endpoint
curl http://localhost:8000/health
```

## What's Hot-Reloaded

✅ **Backend Python files** - Auto-reload on save  
✅ **Frontend React/TS files** - Hot Module Replacement (HMR)  
❌ **Docker configuration** - Requires rebuild  
❌ **Package dependencies** - Requires rebuild  
❌ **nginx configuration** - Requires nginx restart
