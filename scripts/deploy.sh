#!/bin/bash
# StockPredictor Deployment Script
# Usage: ./scripts/deploy.sh [environment] [action]
# Examples:
#   ./scripts/deploy.sh staging deploy
#   ./scripts/deploy.sh production deploy
#   ./scripts/deploy.sh staging rollback

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
ACTION=${2:-deploy}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"ghcr.io/electrichyena"}
IMAGE_NAME="stock-predictor"
COMPOSE_FILE="docker-compose.yml"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check environment file
    if [ ! -f ".env.${ENVIRONMENT}" ] && [ ! -f ".env" ]; then
        log_warn "No .env.${ENVIRONMENT} or .env file found"
    fi

    log_info "Prerequisites check passed"
}

run_tests() {
    log_info "Running tests before deployment..."

    cd backend
    if python -m pytest -v --tb=short -q; then
        log_info "All tests passed"
    else
        log_error "Tests failed! Aborting deployment."
        exit 1
    fi
    cd ..
}

build_images() {
    log_info "Building Docker images..."

    # Build backend
    docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}-backend:latest \
        -t ${DOCKER_REGISTRY}/${IMAGE_NAME}-backend:$(git rev-parse --short HEAD) \
        -f backend/Dockerfile backend/

    # Build frontend
    docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend:latest \
        -t ${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend:$(git rev-parse --short HEAD) \
        -f frontend/Dockerfile frontend/

    log_info "Docker images built successfully"
}

push_images() {
    log_info "Pushing images to registry..."

    docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}-backend:latest
    docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}-backend:$(git rev-parse --short HEAD)
    docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend:latest
    docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend:$(git rev-parse --short HEAD)

    log_info "Images pushed successfully"
}

run_migrations() {
    log_info "Running database migrations..."

    docker-compose exec -T backend alembic upgrade head

    log_info "Migrations completed"
}

health_check() {
    log_info "Running health checks..."

    local max_attempts=30
    local attempt=1
    local health_url="http://localhost:8000/health"

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            log_info "Health check passed"
            return 0
        fi

        log_warn "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "Health check failed after $max_attempts attempts"
    return 1
}

deploy() {
    log_info "Starting deployment to ${ENVIRONMENT}..."

    check_prerequisites

    if [ "$ENVIRONMENT" == "production" ]; then
        run_tests
    fi

    # Pull latest images or build
    if [ "$ENVIRONMENT" == "production" ]; then
        log_info "Pulling latest images..."
        docker-compose pull
    else
        build_images
    fi

    # Stop existing containers gracefully
    log_info "Stopping existing containers..."
    docker-compose down --remove-orphans || true

    # Start new containers
    log_info "Starting new containers..."
    docker-compose up -d

    # Wait for services to start
    sleep 5

    # Run migrations
    run_migrations

    # Health check
    if health_check; then
        log_info "Deployment to ${ENVIRONMENT} completed successfully!"

        # Show running containers
        docker-compose ps
    else
        log_error "Deployment failed! Rolling back..."
        rollback
        exit 1
    fi
}

rollback() {
    log_info "Rolling back deployment..."

    # Get previous image tag from git
    local previous_commit=$(git rev-parse --short HEAD~1)

    log_info "Rolling back to commit: ${previous_commit}"

    # Update images to previous version
    docker-compose down --remove-orphans

    # Pull previous images
    docker pull ${DOCKER_REGISTRY}/${IMAGE_NAME}-backend:${previous_commit} || true
    docker pull ${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend:${previous_commit} || true

    # Tag as latest
    docker tag ${DOCKER_REGISTRY}/${IMAGE_NAME}-backend:${previous_commit} \
        ${DOCKER_REGISTRY}/${IMAGE_NAME}-backend:latest || true
    docker tag ${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend:${previous_commit} \
        ${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend:latest || true

    # Start containers
    docker-compose up -d

    # Health check
    sleep 5
    if health_check; then
        log_info "Rollback completed successfully"
    else
        log_error "Rollback failed! Manual intervention required."
        exit 1
    fi
}

smoke_test() {
    log_info "Running smoke tests..."

    local base_url="http://localhost:8000"
    local frontend_url="http://localhost:3000"

    # Test backend endpoints
    local endpoints=("/health" "/health/live" "/health/ready" "/" "/docs")

    for endpoint in "${endpoints[@]}"; do
        if curl -s -f "${base_url}${endpoint}" > /dev/null 2>&1; then
            log_info "✓ ${endpoint} - OK"
        else
            log_error "✗ ${endpoint} - FAILED"
            return 1
        fi
    done

    # Test frontend
    if curl -s -f "$frontend_url" > /dev/null 2>&1; then
        log_info "✓ Frontend - OK"
    else
        log_warn "✗ Frontend - Not responding (may be expected if not deployed)"
    fi

    log_info "Smoke tests passed"
}

status() {
    log_info "Deployment status for ${ENVIRONMENT}:"
    docker-compose ps

    echo ""
    log_info "Container health:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    log_info "Recent logs:"
    docker-compose logs --tail=20
}

cleanup() {
    log_info "Cleaning up old images and containers..."

    # Remove stopped containers
    docker container prune -f

    # Remove unused images
    docker image prune -f

    # Remove unused volumes (be careful with this!)
    # docker volume prune -f

    log_info "Cleanup completed"
}

# Main script
case "$ACTION" in
    deploy)
        deploy
        smoke_test
        ;;
    rollback)
        rollback
        ;;
    build)
        build_images
        ;;
    push)
        push_images
        ;;
    test)
        run_tests
        ;;
    health)
        health_check
        ;;
    smoke)
        smoke_test
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 [environment] [action]"
        echo ""
        echo "Environments:"
        echo "  staging     - Staging environment (default)"
        echo "  production  - Production environment"
        echo ""
        echo "Actions:"
        echo "  deploy      - Deploy the application (default)"
        echo "  rollback    - Rollback to previous version"
        echo "  build       - Build Docker images"
        echo "  push        - Push images to registry"
        echo "  test        - Run tests"
        echo "  health      - Run health check"
        echo "  smoke       - Run smoke tests"
        echo "  status      - Show deployment status"
        echo "  cleanup     - Clean up old images/containers"
        exit 1
        ;;
esac
