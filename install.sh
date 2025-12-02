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

# Step 4: Check venv module availability and functionality
echo "Step 4: Checking virtual environment module..."
VENV_CMD=""
VENV_AVAILABLE=false

# First check if venv module exists
if $PYTHON_CMD -m venv --help &> /dev/null; then
    # Test if venv can actually create a virtual environment
    TEST_VENV_DIR=$(mktemp -d)
    if $PYTHON_CMD -m venv "$TEST_VENV_DIR" &> /dev/null 2>&1; then
        rm -rf "$TEST_VENV_DIR"
        VENV_AVAILABLE=true
        VENV_CMD="$PYTHON_CMD -m venv"
        print_success "venv module is available and functional"
    else
        rm -rf "$TEST_VENV_DIR" 2>/dev/null || true
        print_warning "venv module exists but ensurepip is not available"
        
        # Try to install python3-venv if on Debian/Ubuntu
        if command -v apt-get &> /dev/null; then
            PYTHON_VERSION_SHORT=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
            print_info "Attempting to install python${PYTHON_VERSION_SHORT}-venv..."
            
            # Check if running as root or can use sudo
            if [ "$EUID" -eq 0 ]; then
                apt-get update -qq && apt-get install -y -qq "python${PYTHON_VERSION_SHORT}-venv" 2>/dev/null
                if [ $? -eq 0 ]; then
                    print_success "python${PYTHON_VERSION_SHORT}-venv installed successfully"
                    # Test again
                    TEST_VENV_DIR2=$(mktemp -d)
                    if $PYTHON_CMD -m venv "$TEST_VENV_DIR2" &> /dev/null 2>&1; then
                        rm -rf "$TEST_VENV_DIR2"
                        VENV_AVAILABLE=true
                        VENV_CMD="$PYTHON_CMD -m venv"
                        print_success "venv is now functional"
                    else
                        rm -rf "$TEST_VENV_DIR2" 2>/dev/null || true
                    fi
                else
                    print_error "Failed to install python${PYTHON_VERSION_SHORT}-venv"
                fi
            else
                print_info "Please run: sudo apt-get install python${PYTHON_VERSION_SHORT}-venv"
            fi
        fi
    fi
fi

# If venv still not available, try virtualenv
if [ "$VENV_AVAILABLE" = false ]; then
    print_warning "Trying virtualenv as alternative..."
    
    if command -v virtualenv &> /dev/null; then
        VENV_CMD="virtualenv"
        VENV_AVAILABLE=true
        print_success "Found virtualenv command"
    elif $PYTHON_CMD -m virtualenv --help &> /dev/null 2>&1; then
        VENV_CMD="$PYTHON_CMD -m virtualenv"
        VENV_AVAILABLE=true
        print_success "Found virtualenv module"
    else
        # Try installing virtualenv
        print_info "Attempting to install virtualenv..."
        if $PIP_CMD install --quiet virtualenv 2>/dev/null; then
            if command -v virtualenv &> /dev/null; then
                VENV_CMD="virtualenv"
                VENV_AVAILABLE=true
                print_success "virtualenv installed successfully"
            elif $PYTHON_CMD -m virtualenv --help &> /dev/null 2>&1; then
                VENV_CMD="$PYTHON_CMD -m virtualenv"
                VENV_AVAILABLE=true
                print_success "virtualenv module installed successfully"
            fi
        fi
    fi
    
    if [ "$VENV_AVAILABLE" = false ]; then
        print_error "Cannot create virtual environment. Neither venv nor virtualenv is working."
        print_info "Installation instructions:"
        if command -v apt-get &> /dev/null; then
            PYTHON_VERSION_SHORT=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
            print_info "  sudo apt-get install python${PYTHON_VERSION_SHORT}-venv"
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
    print_info "Creating virtual environment..."
    VENV_OUTPUT=$($VENV_CMD venv 2>&1)
    VENV_EXIT_CODE=$?
    
    if [ $VENV_EXIT_CODE -eq 0 ] && [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        print_success "Virtual environment created successfully"
    else
        print_error "Failed to create virtual environment"
        if [ -n "$VENV_OUTPUT" ]; then
            echo "$VENV_OUTPUT" | head -5
        fi
        
        # Provide specific instructions based on error
        if echo "$VENV_OUTPUT" | grep -qi "ensurepip"; then
            PYTHON_VERSION_SHORT=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
            print_error "ensurepip is not available. This is required for venv."
            if command -v apt-get &> /dev/null; then
                if [ "$EUID" -eq 0 ]; then
                    print_info "Installing python${PYTHON_VERSION_SHORT}-venv..."
                    apt-get update -qq && apt-get install -y -qq "python${PYTHON_VERSION_SHORT}-venv" 2>&1 | grep -v "^$"
                    if [ $? -eq 0 ]; then
                        print_success "python${PYTHON_VERSION_SHORT}-venv installed. Retrying venv creation..."
                        if $VENV_CMD venv 2>/dev/null && [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
                            print_success "Virtual environment created successfully"
                        else
                            print_error "Still failed after installing python${PYTHON_VERSION_SHORT}-venv"
                            exit 1
                        fi
                    else
                        print_error "Failed to install python${PYTHON_VERSION_SHORT}-venv"
                        print_info "Please run manually: sudo apt-get install python${PYTHON_VERSION_SHORT}-venv"
                        exit 1
                    fi
                else
                    print_info "Please run: sudo apt-get install python${PYTHON_VERSION_SHORT}-venv"
                    print_info "Then run this script again."
                    exit 1
                fi
            else
                print_info "Please install python3-venv package for your system"
                exit 1
            fi
        else
            print_info "Please check the error message above and install required packages."
            exit 1
        fi
    fi
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

