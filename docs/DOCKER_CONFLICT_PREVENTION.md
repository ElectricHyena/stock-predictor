# Docker Conflict Prevention Guide

**Version:** 1.0
**Last Updated:** January 3, 2026
**Purpose:** Prevent port conflicts and resource contention when running Stock Predictor containers with existing services

---

## Table of Contents
1. [Port Allocation & Defaults](#port-allocation--defaults)
2. [Detecting Existing Services](#detecting-existing-services)
3. [Port Remapping](#port-remapping)
4. [Service Communication](#service-communication)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## Port Allocation & Defaults

### Default Port Configuration

Stock Predictor uses the following default ports:

| Service | Port | Protocol | Exposed? | Environment Variable | Use Case |
|---------|------|----------|----------|----------------------|----------|
| PostgreSQL | 5432 | TCP | Yes | `POSTGRES_PORT` | Database |
| Redis | 6379 | TCP | Yes | `REDIS_PORT` | Cache & Message Broker |
| FastAPI | 8000 | TCP | Yes | `API_PORT` | REST API |
| Celery Worker | - | - | No | - | Internal Task Processing |
| Celery Beat | - | - | No | - | Internal Task Scheduling |

**Internal-Only Services (No Port Exposure):**
- Celery Worker processes: Communicate via Redis (port 6379)
- Celery Beat scheduler: Communicates via Redis (port 6379)
- These services do NOT need port remapping

---

## Detecting Existing Services

### Step 1: Check for Running Containers

```bash
# List all running Docker containers
docker ps

# Example output:
# CONTAINER ID   IMAGE           PORTS
# abc123def456   postgres:14     5432->5432/tcp
# xyz789abc123   redis:7         6379->6379/tcp
```

### Step 2: Check for Running Services on Ports

**macOS:**
```bash
lsof -i -P -n | grep LISTEN

# Example output:
# COMMAND    PID  USER  FD  TYPE DEVICE SIZE/OFF NODE NAME
# postgres   123  user  10u IPv6  0x1234 0t0  TCP *:5432 (LISTEN)
# redis-ser  456  user  5u  IPv6  0x5678 0t0  TCP *:6379 (LISTEN)
```

**Linux:**
```bash
netstat -tlnp | grep LISTEN

# Or:
ss -tlnp | grep LISTEN
```

### Step 3: Automated Port Check

Stock Predictor includes a port detection script:

```bash
# Check if all default ports are available
./scripts/check-ports.sh

# Example output:
# ✓ Port 5432 (PostgreSQL): Available
# ✓ Port 6379 (Redis): Available
# ✓ Port 8000 (FastAPI): Available
# Ready to start containers!

# With conflict:
# ✗ Port 5432 (PostgreSQL): In use by postgres (PID 12345)
# ✗ Port 6379 (Redis): Available
# ✗ Port 8000 (FastAPI): Available
# Suggestion: Run with POSTGRES_PORT=5433
```

---

## Port Remapping

### Option 1: Using Environment Variables (Recommended)

Set environment variables before starting containers:

```bash
# Start containers with remapped ports
POSTGRES_PORT=5433 REDIS_PORT=6380 API_PORT=8001 docker-compose up -d

# Or create a custom .env file:
cat > .env.custom << EOF
POSTGRES_PORT=5433
REDIS_PORT=6380
API_PORT=8001
POSTGRES_USER=dev
POSTGRES_PASSWORD=devpass
POSTGRES_DB=stock_predictor
NEWSAPI_KEY=your_key_here
SECRET_KEY=your_secret
EOF

# Use custom .env file
docker-compose --env-file .env.custom up -d
```

### Option 2: Using docker-compose.override.yml

Create a local override file (not tracked by git):

```bash
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  postgres:
    ports:
      - "5433:5432"
  redis:
    ports:
      - "6380:6379"
  web:
    ports:
      - "8001:8000"
EOF

# Now start normally (override file auto-loaded)
docker-compose up -d
```

### Option 3: Modify .env File Directly

```bash
# Copy the example
cp .env.example .env

# Edit .env with your preferred ports
nano .env
# Set: POSTGRES_PORT=5433
#      REDIS_PORT=6380
#      API_PORT=8001

# Start containers (reads from .env automatically)
docker-compose up -d
```

---

## Service Communication

### Internal vs. External Connections

**External Access (from your machine):**
```bash
# PostgreSQL: Connect via remapped port
psql -h localhost -p 5433 -U dev stock_predictor

# Redis: Connect via remapped port
redis-cli -p 6380

# API: Access via remapped port
curl http://localhost:8001/health
```

**Internal Service-to-Service (within Docker):**

Services communicate via **service names**, NOT localhost:

```python
# ✓ CORRECT: Use service name + internal port
DATABASE_URL = "postgresql://user:pass@postgres:5432/stock_predictor"
REDIS_URL = "redis://redis:6379/0"

# ✗ WRONG: Don't use localhost or remapped port
# DATABASE_URL = "postgresql://user:pass@localhost:5433/stock_predictor"
# (This won't work - localhost from inside container = container itself)
```

### Connection String Examples

**With Default Ports:**
```
PostgreSQL: postgresql://dev:devpass@postgres:5432/stock_predictor
Redis:      redis://redis:6379/0
```

**With Remapped Ports:**
Internally, services still use **original ports** (5432, 6379) because they're on the internal network. The port remapping only affects external access:

```
Internal (in containers):     postgresql://dev:devpass@postgres:5432/...
External (from your machine): psql -h localhost -p 5433 ...
```

**Port Mapping Details:**
```
docker-compose port mapping: "5433:5432"
↓
External:   5433 (your machine)
Internal:   5432 (inside container, used by services)
```

---

## Troubleshooting

### "Address already in use" Error

**Error message:**
```
Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

**Solution:**
```bash
# 1. Find what's using the port
lsof -i :5432

# 2. Option A: Stop the conflicting service
kill -9 <PID>

# 3. Option B: Remap to different port (RECOMMENDED)
POSTGRES_PORT=5433 docker-compose up -d
```

### "Can't connect to database" Error (Inside Container)

**Error message:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Likely cause:** Service using wrong hostname/port

**Check connection strings:**
```bash
# View current connection strings
docker-compose exec web env | grep DATABASE_URL
docker-compose exec web env | grep REDIS_URL

# Verify they use service names, not localhost
# Should be: postgres:5432, NOT localhost:5432
```

**Fix:** Update DATABASE_URL in .env to use service name:
```
DATABASE_URL=postgresql://dev:devpass@postgres:5432/stock_predictor
```

### "redis-cli: Command not found" or Can't Connect to Redis

**Verify Redis is running:**
```bash
# Check if redis container is up
docker-compose ps

# Check Redis health
docker-compose exec redis redis-cli ping
# Should return: PONG
```

**If port is remapped:**
```bash
# Determine which port Redis is on
docker-compose port redis 6379
# Output: 0.0.0.0:6380 (if remapped to 6380)

# Connect to remapped port
redis-cli -p 6380
```

### Containers Won't Start

**Cause 1: Services not healthy (dependencies)**
```bash
# Check service logs
docker-compose logs postgres
docker-compose logs redis

# Services must be healthy before dependent services start
# PostgreSQL health check: pg_isready
# Redis health check: redis-cli ping
```

**Cause 2: Volume mount issues**
```bash
# Verify volumes exist and have correct permissions
docker-compose exec postgres ls -la /var/lib/postgresql/data

# Recreate volumes if corrupted
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d
```

### Port Remapping Not Working

**Verify in docker-compose.yml:**
```yaml
# ✓ CORRECT: Uses environment variables
web:
  ports:
    - "${API_PORT}:8000"

# ✗ WRONG: Hardcoded port
web:
  ports:
    - "8000:8000"
```

**Check .env file:**
```bash
# Verify .env has port variables
grep POSTGRES_PORT .env
grep REDIS_PORT .env
grep API_PORT .env
```

**Restart with .env reload:**
```bash
# Stop containers
docker-compose down

# Ensure .env is set correctly
cat .env | grep PORT

# Restart
docker-compose up -d
```

---

## Best Practices

### 1. Always Use Environment Variables for Port Configuration

✓ **Good:**
```yaml
services:
  postgres:
    ports:
      - "${POSTGRES_PORT}:5432"
```

✗ **Avoid:**
```yaml
services:
  postgres:
    ports:
      - "5432:5432"  # Hardcoded - can't be changed
```

### 2. Document Default Ports

Add comment block at top of docker-compose.yml:

```yaml
# PORT CONFIGURATION
# This file uses environment variables for flexible port mapping.
# Default ports:
#   - PostgreSQL: 5432 (set POSTGRES_PORT to override)
#   - Redis: 6379 (set REDIS_PORT to override)
#   - FastAPI: 8000 (set API_PORT to override)
# Example: POSTGRES_PORT=5433 docker-compose up
```

### 3. Include .env.example in Version Control

**✓ Track in git:**
```bash
git add .env.example
```

**✗ Don't track:**
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

### 4. Use Service Names in Connection Strings

**Internal communication:**
```
postgres:5432    (NOT localhost:5432)
redis:6379       (NOT localhost:6379)
```

### 5. Test Port Remapping

```bash
# Test with alternative ports
POSTGRES_PORT=5433 REDIS_PORT=6380 API_PORT=8001 docker-compose up -d

# Verify services are accessible
docker-compose ps
docker-compose logs web
```

### 6. Monitor Resource Usage

```bash
# View real-time resource usage
docker stats

# View logs from all services
docker-compose logs -f
```

### 7. Keep .env Secret

**In .gitignore:**
```
.env
.env.local
.env.*.local
```

**Share only .env.example:**
```bash
# Team members copy example
cp .env.example .env
# Then edit with their own values
```

---

## Quick Reference: Port Remapping Commands

```bash
# Check for conflicts
./scripts/check-ports.sh

# Start with all default ports
docker-compose up -d

# Start with remapped PostgreSQL port
POSTGRES_PORT=5433 docker-compose up -d

# Start with all remapped ports
POSTGRES_PORT=5433 REDIS_PORT=6380 API_PORT=8001 docker-compose up -d

# Start with custom .env file
docker-compose --env-file .env.custom up -d

# View what ports are actually in use
docker-compose ps

# Connect to remapped database
psql -h localhost -p 5433 -U dev stock_predictor

# Check if services are healthy
docker-compose exec postgres pg_isready -U dev
docker-compose exec redis redis-cli ping
```

---

## Support & Troubleshooting

If you encounter port conflicts not covered here:

1. **Check docker-compose.yml** for hardcoded ports
2. **Verify .env variables** are set correctly
3. **Review service logs** for connection errors
4. **Run check-ports.sh** to identify conflicts
5. **Contact:** See project README for support channels

---

**End of Docker Conflict Prevention Guide**
