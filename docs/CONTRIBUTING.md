# Contributing to ClusterCloud

Thank you for your interest in contributing to ClusterCloud!

## Development Setup

See README.md for initial setup instructions.

## Code Style

### Python
- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for non-obvious functions
- Run `black` for formatting
- Run `pylint` for linting

### TypeScript
- Follow Airbnb style guide
- Use explicit types, avoid `any`
- Prefer functional components with hooks
- Run `prettier` for formatting
- Run `eslint` for linting

## Commit Messages

Use imperative mood, present tense:

✅ Good:
- `Add heartbeat monitoring for node agents`
- `Fix task reassignment race condition`
- `Update README with setup instructions`

❌ Bad:
- `Added feature`
- `Fixed bug`
- `Updates`

## Git Workflow

1. **Branch naming**
   - `feature/short-description`
   - `fix/issue-description`
   - `docs/update-description`

2. **Commit frequency**
   - Make small, logical commits
   - One concern per commit
   - Commit working code that passes tests

3. **Before committing**
   - Run relevant tests
   - Check code formatting
   - Update documentation if needed

4. **Pull requests**
   - Reference related issues
   - Describe what changed and why
   - Include screenshots for UI changes

## Testing

### Backend Tests
```bash
cd apps/api
pytest tests/
pytest tests/test_scheduler.py -v  # Specific test
```

### Frontend Tests
```bash
cd apps/web
npm test
npm test -- --coverage
```

### Integration Tests
```bash
cd tests
pytest integration/
```

## Architecture Guidelines

### Backend Domain Modules

Each domain should have:
- `models.py`: SQLAlchemy models
- `schemas.py`: Pydantic request/response models
- `service.py`: Business logic
- `router.py`: FastAPI endpoints

Example structure:
```
apps/api/domains/jobs/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
```

### Adding New Workload Types

1. Define workload in `domains/workloads/registry.py`
2. Add AI analysis prompt in `domains/ai/prompts.py`
3. Create validation rules in `domains/scheduling/constraints.py`
4. Add UI form in `apps/web/components/workloads/`
5. Document in `docs/WORKLOAD_TYPES.md`

### Adding New Features

1. **Start with the domain model**
   - What data needs to be stored?
   - What are the state transitions?
   - What are the invariants?

2. **Write the service layer**
   - Business logic
   - Validation
   - State management

3. **Add API endpoints**
   - RESTful design
   - Proper error handling
   - Request/response validation

4. **Update the frontend**
   - New components as needed
   - Real-time updates via WebSocket
   - User-friendly error messages

5. **Write tests**
   - Unit tests for business logic
   - Integration tests for workflows
   - E2E tests for critical paths

6. **Document**
   - Update relevant docs
   - Add inline comments for complex logic
   - Update API documentation

## Common Tasks

### Adding a New Database Table

1. Create SQLAlchemy model in appropriate domain
2. Generate migration: `alembic revision --autogenerate -m "Add table_name"`
3. Review migration file
4. Apply: `alembic upgrade head`

### Adding a New API Endpoint

1. Define Pydantic schemas for request/response
2. Implement service function
3. Add router endpoint with proper decorators
4. Include in main API router
5. Test with curl/Postman
6. Add integration test

### Adding a New WebSocket Event

1. Define event type in `apps/api/domains/events/types.py`
2. Emit event from service layer
3. Handle in `apps/web/hooks/useWebSocket.ts`
4. Update UI component to display

## Debugging

### Backend
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

### View logs
```bash
# API logs
tail -f apps/api/logs/app.log

# Node agent logs
tail -f apps/node-agent/logs/agent.log

# Docker logs
docker-compose logs -f
```

### Database inspection
```bash
# Connect to PostgreSQL
docker exec -it clustercloud_postgres psql -U clustercloud

# View tables
\dt

# Query jobs
SELECT job_id, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;
```

## Questions?

Open an issue or discussion on GitHub.
