#!/bin/bash

################################################################################
# Port Conflict Detection Script for StockPredictor
#
# Purpose: Check if required ports are available before docker-compose startup
# Usage:   ./scripts/check-ports.sh
#          ./scripts/check-ports.sh [postgres_port] [redis_port] [api_port]
#
# This script helps prevent port binding failures by detecting conflicts
# with running services and suggesting alternatives.
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get port values from environment or arguments
POSTGRES_PORT="${1:-${POSTGRES_PORT:-5432}}"
REDIS_PORT="${2:-${REDIS_PORT:-6379}}"
API_PORT="${3:-${API_PORT:-8000}}"

# Flags
VERBOSE=false
ALL_AVAILABLE=true
CONFLICTS=()

# Parse script arguments
parse_args() {
    for arg in "$@"; do
        case "$arg" in
            -v|--verbose)
                VERBOSE=true
                ;;
        esac
    done
}

# Check if a port is in use
check_port() {
    local port=$1
    local service_name=$2

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0  # Port is in use
        fi
    else
        # Linux
        if netstat -tuln 2>/dev/null | grep -q ":$port " || \
           ss -tuln 2>/dev/null | grep -q ":$port "; then
            return 0  # Port is in use
        fi
    fi
    return 1  # Port is available
}

# Get process using a port
get_process_info() {
    local port=$1

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use lsof
        lsof -i :$port 2>/dev/null | tail -n 1 | awk '{print $1, "(" $2 ")"}' || echo "Unknown"
    else
        # Linux - try lsof first, then fuser
        if command -v lsof &> /dev/null; then
            lsof -i :$port 2>/dev/null | tail -n 1 | awk '{print $1, "(" $2 ")"}' || echo "Unknown"
        elif command -v fuser &> /dev/null; then
            fuser $port/tcp 2>/dev/null && echo "(PID shown above)" || echo "Unknown"
        else
            echo "Unknown"
        fi
    fi
}

# Find an available alternative port
find_available_port() {
    local start_port=$1
    local base_port=$start_port

    for port in $(seq $start_port $((start_port + 100))); do
        if ! check_port $port ""; then
            echo $port
            return 0
        fi
    done

    return 1
}

# Print header
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         StockPredictor Port Availability Check                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Print port check result
check_and_report() {
    local port=$1
    local service=$2
    local default_port=$3

    echo -n "Checking ${service}... "

    if check_port $port ""; then
        echo -e "${RED}✗ CONFLICT${NC}"
        echo "  Port $port is already in use"

        # Find process using the port
        process_info=$(get_process_info $port)
        if [ "$process_info" != "Unknown" ]; then
            echo "  Process: $process_info"
        fi

        # Suggest alternative
        alt_port=$(find_available_port $((port + 1)))
        if [ ! -z "$alt_port" ]; then
            echo -e "  ${YELLOW}Suggestion: Use port $alt_port instead${NC}"
            echo "  Update .env: ${service}_PORT=$alt_port"
        fi

        CONFLICTS+=("$service (port $port)")
        ALL_AVAILABLE=false
    else
        echo -e "${GREEN}✓ Available${NC} (port $port)"
    fi
    echo ""
}

# Main execution
main() {
    parse_args "$@"

    print_header

    # Show current configuration
    echo -e "${BLUE}Configuration:${NC}"
    echo "  PostgreSQL Port: $POSTGRES_PORT"
    echo "  Redis Port:      $REDIS_PORT"
    echo "  API Port:        $API_PORT"
    echo ""

    # Show required commands
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}Required Tools:${NC}"
        if command -v lsof &> /dev/null; then
            echo "  ✓ lsof found (will be used for port checking)"
        elif command -v netstat &> /dev/null; then
            echo "  ✓ netstat found (will be used for port checking)"
        elif command -v ss &> /dev/null; then
            echo "  ✓ ss found (will be used for port checking)"
        else
            echo "  ⚠ No port checking tool found (lsof, netstat, or ss)"
        fi
        echo ""
    fi

    # Check each port
    echo -e "${BLUE}Port Availability:${NC}"
    check_and_report "$POSTGRES_PORT" "PostgreSQL" "5432"
    check_and_report "$REDIS_PORT" "Redis" "6379"
    check_and_report "$API_PORT" "FastAPI" "8000"

    # Summary
    echo -e "${BLUE}─────────────────────────────────────────────────────────────${NC}"
    if [[ "$ALL_AVAILABLE" == true ]]; then
        echo -e "${GREEN}✓ All ports are available!${NC}"
        echo ""
        echo "You can now start the services:"
        echo "  docker-compose up -d"
        echo ""
        exit 0
    else
        echo -e "${RED}✗ Port conflicts detected:${NC}"
        for conflict in "${CONFLICTS[@]}"; do
            echo "  - $conflict"
        done
        echo ""
        echo "Options to resolve:"
        echo "  1. Update .env file with available ports"
        echo "  2. Stop the conflicting service(s)"
        echo "  3. Run this script again to verify"
        echo ""
        echo "Example .env configuration:"
        echo "  POSTGRES_PORT=$(find_available_port 5432)"
        echo "  REDIS_PORT=$(find_available_port 6379)"
        echo "  API_PORT=$(find_available_port 8000)"
        echo ""
        exit 1
    fi
}

# Run main function
main "$@"
