<p align="left">
    English | <a href="README_zh.md">中文</a>
</p>

# FastAPI Backend Project

This is a FastAPI-based backend project using MongoDB as the database, managed by Docker and docker-compose, with Traefik acting as a reverse proxy and load balancer. The project structure includes API, data models, CRUD operations, dependency management, user authentication, and security settings, designed for both development and production environments.

## Project Structure
```
.
├── README.md                   # Project description
├── backend                     # Backend app code and configurations
│   ├── Dockerfile              # Dockerfile for backend image
│   ├── app                     # FastAPI application directory
│   │   ├── api                 # API routes and dependencies
│   │   │   ├── endpoints       # API endpoint definitions
│   │   ├── core                # Core configurations and security settings
│   │   ├── crud                # CRUD operations for the database
│   │   ├── models              # Database models
│   │   ├── schemas             # Data transfer schemas
│   │   ├── utils               # Utility modules
│   │   └── main.py             # Main entry for FastAPI application
│   ├── gunicorn_conf.py        # Gunicorn configuration
│   └── scripts                 # Startup scripts
├── docker-compose.yml          # Docker Compose configuration
├── docker-compose.traefik.yml  # Docker Compose config with Traefik
├── poetry.lock                 # Poetry lock file
├── pyproject.toml              # Poetry project config file
├── run.sh                      # Application startup script
├── run.traefik.sh              # Traefik-enabled startup script
└── tests                       # Test code directory
```

## Features

- **API Endpoints**: Provides user registration, login, and profile retrieval.
- **API v2**: Adds a response envelope (`data`, `meta`, `error`) and cursor-based pagination for high-concurrency read paths.
- **User Authentication**: JWT-based authentication and authorization.
- **CRUD Operations**: Encapsulated data manipulation functions.
- **Runtime Resilience**: Lifespan-managed Mongo/Redis clients, request timeout guard, rate limiting, and graceful dependency degradation.
- **Health and Metrics**: `/health/live`, `/health/ready`, `/metrics` endpoints for readiness probes and Prometheus scraping.
- **Reverse Proxy**: Traefik-enabled dynamic routing and load balancing.
- **Configuration Management**: Gunicorn setup for production deployments.
- **Testing Support**: Ready for extended automated testing.

## Deployment and Running

### Local Run (without Traefik)

```bash
# Start Docker service
./run.sh
```

### Deployment with Traefik

```bash
# Start Docker service with Traefik support
./run.traefik.sh
```

### Configuration Guide

### Docker Environment Variables

Configured in the .env file, including:

- **SECRET_KEY**: Secret key for JWT encryption
- **ACCESS_TOKEN_EXPIRE_MINUTES**: Expiration time for access tokens (minutes)
- **MONGO_DB_URI**: Replica set URI, e.g. `mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0`
- **MONGO_DB_DATABASE**: Mongo database name
- **MONGO_DB_USER_COLLECTION**: User collection name
- **MONGO_DB_ITEM_COLLECTION**: Item collection name
- **MONGO_MAX_POOL_SIZE / MONGO_MIN_POOL_SIZE**: Mongo connection pool limits
- **MONGO_SERVER_SELECTION_TIMEOUT_MS**: Mongo selection timeout
- **MONGO_MAX_IDLE_TIME_MS**: Mongo max idle connection time
- **REDIS_URL**: Redis connection URL, e.g. `redis://redis:6379/0`
- **CACHE_TTL_SECONDS**: Redis cache TTL
- **RATE_LIMIT_PER_MINUTE**: Generic read rate limit
- **LOGIN_RATE_LIMIT_PER_MINUTE**: Login rate limit
- **REQUEST_TIMEOUT_MS**: Request timeout guard

### Traefik Reverse Proxy

Use the docker-compose.traefik.yml configuration file for Traefik, managing dynamic routing within the Docker network to ensure container accessibility across services.

### New Runtime Endpoints

- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `POST /api/v2/users/access-token`
- `POST /api/v2/users/register`
- `GET /api/v2/users/me`
- `GET /api/v2/items/list?cursor=<id>&limit=<n>`

### Performance and Rollout Assets

- Baseline load test script: `tests/load/k6_baseline.js`
- Baseline template and SLO gate: `docs/perf/baseline.md`
- Gray-release playbook: `docs/rollout/gray-release.md`



