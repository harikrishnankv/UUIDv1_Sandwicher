#!/bin/bash

# UUIDv1 SANDWICHER - Installation Script
# This script handles Python virtual environment setup and dependency installation

set -e  # Exit on error

echo "=========================================="
echo "UUIDv1 SANDWICHER - Installation Script"
echo "=========================================="
echo ""

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

# Step 1: Detect Python
echo "Step 1: Detecting Python installation..."
PYTHON_CMD=""
PIP_CMD=""

# Check for python3 first
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 7 ]; then
        PYTHON_CMD="python3"
        print_success "Found Python $PYTHON_VERSION (python3)"
    else
        print_error "Python 3.7+ required. Found Python $PYTHON_VERSION"
        exit 1
    fi
# Check for python (might be Python 3)
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 7 ]; then
        PYTHON_CMD="python"
        print_success "Found Python $PYTHON_VERSION (python)"
    else
        print_error "Python 3.7+ required. Found Python $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python not found. Please install Python 3.7 or higher."
    exit 1
fi

echo ""

# Step 2: Detect pip
echo "Step 2: Detecting pip installation..."
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    print_success "Found pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    print_success "Found pip"
else
    print_warning "pip not found. Attempting to install pip..."
    $PYTHON_CMD -m ensurepip --upgrade || {
        print_error "Failed to install pip. Please install pip manually."
        exit 1
    }
    PIP_CMD="$PYTHON_CMD -m pip"
    print_success "pip installed successfully"
fi

echo ""

# Step 3: Upgrade pip
echo "Step 3: Upgrading pip to latest version..."
$PIP_CMD install --upgrade pip --quiet
print_success "pip upgraded successfully"

echo ""

# Step 4: Check venv module availability
echo "Step 4: Checking virtual environment module..."
VENV_CMD=""
if $PYTHON_CMD -m venv --help &> /dev/null; then
    print_success "venv module is available"
    VENV_CMD="$PYTHON_CMD -m venv"
else
    print_warning "venv module is not available in Python installation"
    
    # Try alternative: virtualenv
    if command -v virtualenv &> /dev/null; then
        print_warning "Using virtualenv as alternative..."
        VENV_CMD="virtualenv"
    elif $PYTHON_CMD -m virtualenv --help &> /dev/null 2>&1; then
        print_warning "Using virtualenv module as alternative..."
        VENV_CMD="$PYTHON_CMD -m virtualenv"
    else
        print_error "Neither venv nor virtualenv is available."
        print_info "Installation instructions:"
        if command -v apt-get &> /dev/null; then
            print_info "  sudo apt-get install python3-venv"
        elif command -v yum &> /dev/null; then
            print_info "  sudo yum install python3-venv"
        elif command -v brew &> /dev/null; then
            print_info "  brew install python3 (venv should be included)"
        else
            print_info "  Install python3-venv package for your system"
            print_info "  Or install virtualenv: pip install virtualenv"
        fi
        exit 1
    fi
fi

echo ""

# Step 5: Create virtual environment
echo "Step 5: Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment 'venv' already exists."
    read -p "Do you want to remove and recreate it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        print_success "Removed existing virtual environment"
    else
        print_warning "Using existing virtual environment"
    fi
fi

if [ ! -d "venv" ]; then
    $VENV_CMD venv
    print_success "Virtual environment created successfully"
fi

echo ""

# Step 6: Activate virtual environment and install dependencies
echo "Step 6: Installing dependencies..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip in venv
venv/bin/pip install --upgrade pip --quiet

# Install dependencies
print_success "Installing packages from requirements.txt..."
venv/bin/pip install -r requirements.txt --quiet

print_success "All dependencies installed successfully"

echo ""
echo "=========================================="
print_success "Installation completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run './start.sh' to start the application"
echo "  2. Or manually: source venv/bin/activate && python3 app.py"
echo ""

