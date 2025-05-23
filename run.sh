#!/bin/bash

# Railway Ticket Reservation System Runner Script
# This script builds and runs the application using Docker

echo "==============================================="
echo "Railway Ticket Reservation System Runner"
echo "==============================================="

# Check if Docker is available
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker and/or Docker Compose are not installed"
    echo "Please install Docker and Docker Compose before running this script"
    exit 1
fi

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message"
    echo "  -d, --dev       Run in development mode"
    echo "  -p, --prod      Run in production mode"
    echo "  -r, --rebuild   Rebuild the Docker containers"
    echo "  -s, --stop      Stop the running containers"
    echo ""
}

# Default options
MODE="development"
REBUILD=false
STOP=false

# Parse command-line options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            MODE="development"
            shift
            ;;
        -p|--prod)
            MODE="production"
            shift
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        -s|--stop)
            STOP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Handle stop option
if [ "$STOP" = true ]; then
    echo "Stopping running containers..."
    docker-compose down
    echo "✅ Containers stopped"
    exit 0
fi

# Set environment variables based on mode
if [ "$MODE" = "production" ]; then
    export FLASK_ENV=production
    export PORT=5000
    echo "Running in production mode"
    # Use Docker Compose production configuration
    COMPOSE_FILE="docker-compose.yml -f docker-compose.prod.yml"
else
    export FLASK_ENV=development
    export PORT=5000
    echo "Running in development mode"
    COMPOSE_FILE="docker-compose.yml"
fi

# Build and run the application
if [ "$REBUILD" = true ]; then
    echo "Rebuilding and starting containers..."
    docker-compose -f $COMPOSE_FILE up -d --build
else
    echo "Starting containers..."
    docker-compose -f $COMPOSE_FILE up -d
fi

# Check if containers started successfully
if [ $? -eq 0 ]; then
    echo "✅ Application started successfully"
    echo ""
    echo "The application is now running at:"
    echo "  - API: http://localhost:5000"
    echo "  - Swagger Documentation: http://localhost:5000/api/docs"
    echo ""
    echo "To stop the application, run: $0 --stop"
else
    echo "❌ Failed to start the application"
    exit 1
fi

exit 0
