#!/bin/bash

# UUIDv1 SANDWICHER - Start Script
# This script handles port checking and application startup

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Default port
DEFAULT_PORT=5001
PORT=$DEFAULT_PORT

echo "=========================================="
echo "UUIDv1 SANDWICHER - Start Script"
echo "=========================================="
echo ""

# Step 1: Check if virtual environment exists
echo "Step 1: Checking virtual environment..."
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    echo ""
    read -p "Do you want to run the installation script now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ ! -f "install.sh" ]; then
            print_error "install.sh not found!"
            exit 1
        fi
        chmod +x install.sh
        ./install.sh
    else
        print_error "Please run './install.sh' first to set up the virtual environment."
        exit 1
    fi
fi

if [ ! -f "venv/bin/activate" ]; then
    print_error "Virtual environment is corrupted. Please run './install.sh' again."
    exit 1
fi

print_success "Virtual environment found"

echo ""

# Step 2: Check if port is in use
echo "Step 2: Checking port availability..."
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

if check_port $DEFAULT_PORT; then
    print_warning "Port $DEFAULT_PORT is already in use"
    echo ""
    echo "Options:"
    echo "  1. Kill the process using port $DEFAULT_PORT"
    echo "  2. Use a different port"
    echo "  3. Exit"
    echo ""
    read -p "Choose an option (1/2/3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            PID=$(lsof -ti:$DEFAULT_PORT)
            if [ ! -z "$PID" ]; then
                print_info "Killing process $PID on port $DEFAULT_PORT..."
                kill -9 $PID 2>/dev/null || true
                sleep 1
                if check_port $DEFAULT_PORT; then
                    print_error "Failed to free port $DEFAULT_PORT"
                    exit 1
                else
                    print_success "Port $DEFAULT_PORT is now available"
                    PORT=$DEFAULT_PORT
                fi
            else
                print_error "Could not find process using port $DEFAULT_PORT"
                exit 1
            fi
            ;;
        2)
            while true; do
                read -p "Enter port number (1024-65535): " PORT
                if [[ "$PORT" =~ ^[0-9]+$ ]] && [ "$PORT" -ge 1024 ] && [ "$PORT" -le 65535 ]; then
                    if check_port $PORT; then
                        print_warning "Port $PORT is also in use. Please choose another port."
                    else
                        print_success "Port $PORT is available"
                        break
                    fi
                else
                    print_error "Invalid port number. Please enter a number between 1024 and 65535."
                fi
            done
            ;;
        3)
            print_info "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid option. Exiting..."
            exit 1
            ;;
    esac
else
    print_success "Port $DEFAULT_PORT is available"
    PORT=$DEFAULT_PORT
fi

echo ""

# Step 3: Activate virtual environment and start application
echo "Step 3: Starting application..."
print_info "Activating virtual environment..."

# Activate virtual environment
source venv/bin/activate

# Check if app.py exists
if [ ! -f "app.py" ]; then
    print_error "app.py not found!"
    exit 1
fi

# Check Python in venv
if [ ! -f "venv/bin/python3" ] && [ ! -f "venv/bin/python" ]; then
    print_error "Python not found in virtual environment. Please run './install.sh' again."
    exit 1
fi

# Determine Python command
if [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="venv/bin/python3"
else
    PYTHON_CMD="venv/bin/python"
fi

print_success "Starting Flask application on port $PORT..."
echo ""
echo "=========================================="
print_success "Application starting..."
echo "=========================================="
echo ""
print_info "Access the application at: http://localhost:$PORT"
print_info "Press Ctrl+C to stop the server"
echo ""

# Export PORT as environment variable for app.py to use
export PORT=$PORT

# Start the application
$PYTHON_CMD app.py

