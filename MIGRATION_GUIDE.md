# Database Migration Guide

## Overview

The project uses Alembic for database migrations. Migrations are automatically applied when the development or production environment starts via the `migrate` service in Docker Compose.

## Automatic Migrations (CI/CD Ready)

When you start the environment with `make dev` or `docker-compose up`, the following happens:

1. **Database starts** - PostgreSQL container starts and waits until healthy
2. **Migrate service runs** - Executes `alembic upgrade head` to apply all pending migrations
3. **Backend starts** - Only starts after migrations complete successfully
4. **Frontend starts** - Loads the UI

This ensures:
- ✅ Database schema is always up-to-date
- ✅ Migrations run before the application starts
- ✅ Safe for CI/CD pipelines
- ✅ No manual intervention required

## Migration Workflow

### Creating a New Migration

When you add or modify models:

```bash
# Create a new migration with autogenerate
make migrate-create MSG="add user profile table"

# This generates a file like: alembic/versions/xxxxx_add_user_profile_table.py
```

**Review the generated migration file** before applying it! Alembic's autogenerate is smart but not perfect.

### Applying Migrations

```bash
# Apply all pending migrations
make migrate-upgrade

# Or directly:
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

### Rolling Back Migrations

```bash
# Rollback the last migration
make migrate-downgrade

# Rollback to a specific revision
docker-compose -f docker-compose.dev.yml exec backend alembic downgrade <revision_id>

# Rollback all migrations
docker-compose -f docker-compose.dev.yml exec backend alembic downgrade base
```

### Viewing Migration Status

```bash
# Show current migration version
make migrate-current

# Show migration history
make migrate-history

# Show pending migrations
docker-compose -f docker-compose.dev.yml exec backend alembic current
docker-compose -f docker-compose.dev.yml exec backend alembic heads
```

## Migration Best Practices

### 1. Always Review Generated Migrations

```python
# Generated migration file
def upgrade() -> None:
    # Review these carefully!
    op.create_table('user_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        # ...
    )
```

### 2. Test Migrations Both Ways

```bash
# Apply migration
make migrate-upgrade

# Test your changes...

# Rollback to ensure downgrade works
make migrate-downgrade

# Apply again
make migrate-upgrade
```

### 3. Never Modify Applied Migrations

Once a migration is applied and committed to version control:
- ❌ Don't edit it
- ✅ Create a new migration to fix issues

### 4. Keep Migrations Small and Focused

```bash
# Good - single responsibility
make migrate-create MSG="add email column to users"

# Bad - too many changes
make migrate-create MSG="add email, phone, address, and refactor entire schema"
```

## Production Deployment

### Option 1: Automatic (Recommended)

The `migrate` service in `docker-compose.prod.yml` automatically runs migrations on deployment:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

The backend won't start until migrations complete successfully.

### Option 2: Manual

Run migrations manually before starting the backend:

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml run --rm migrate

# Then start the application
docker-compose -f docker-compose.prod.yml up -d backend frontend nginx
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Database Migrations
  run: |
    docker-compose -f docker-compose.prod.yml up -d db
    docker-compose -f docker-compose.prod.yml run --rm migrate
    
- name: Start Application
  run: |
    docker-compose -f docker-compose.prod.yml up -d
```

### Docker Compose Service Order

```yaml
migrate:
  # Runs migrations
  depends_on:
    db:
      condition: service_healthy
  command: alembic upgrade head

backend:
  # Only starts after migrations complete
  depends_on:
    db:
      condition: service_healthy
    migrate:
      condition: service_completed_successfully
```

## Troubleshooting

### Migration Failed

```bash
# Check migration logs
docker-compose -f docker-compose.dev.yml logs migrate

# Check current state
make migrate-current

# Check what went wrong
make backend-shell
alembic history
alembic current
```

### Migrations Out of Sync

```bash
# Mark current database state without running migrations
docker-compose -f docker-compose.dev.yml exec backend alembic stamp head

# Or mark a specific revision
docker-compose -f docker-compose.dev.yml exec backend alembic stamp <revision_id>
```

### Multiple Heads (Branched Migrations)

```bash
# View heads
docker-compose -f docker-compose.dev.yml exec backend alembic heads

# Merge branches
docker-compose -f docker-compose.dev.yml exec backend alembic merge -m "merge branches" <rev1> <rev2>
```

### Clean Slate

```bash
# Warning: This deletes all data!
make clean  # Stops and removes all containers and volumes
make dev    # Starts fresh with migrations applied
```

## File Structure

```
backend/
├── alembic/
│   ├── versions/          # Migration files
│   │   └── xxxxx_initial_migration.py
│   ├── env.py             # Alembic environment (configured for async)
│   ├── script.py.mako     # Migration template
│   └── README
├── alembic.ini            # Alembic configuration
├── app/
│   ├── models/            # SQLAlchemy models (used by autogenerate)
│   └── ...
└── ...
```

## Advanced Usage

### Creating Empty Migration

```bash
# Create migration without autogenerate
docker-compose -f docker-compose.dev.yml exec backend alembic revision -m "custom migration"
```

### Data Migrations

```python
# In migration file
from alembic import op

def upgrade() -> None:
    # Add column
    op.add_column('users', sa.Column('status', sa.String(20)))
    
    # Migrate data
    op.execute("""
        UPDATE users 
        SET status = 'active' 
        WHERE is_active = true
    """)

def downgrade() -> None:
    op.drop_column('users', 'status')
```

### Offline Migrations (SQL Generation)

```bash
# Generate SQL without applying
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head --sql > migration.sql
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Users](https://fastapi-users.github.io/fastapi-users/)
