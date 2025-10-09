#!/usr/bin/env bash
#
# Strands Chat Loop - Installation Script
#
# This script installs the chat loop globally so you can run:
#   chat_loop <agent_path>
# from anywhere in your terminal.
#
# Usage:
#   ./install.sh          # Install for current user
#   ./install.sh --help   # Show help
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="$HOME/.local/bin"
WRAPPER_NAME="chat_loop"
WRAPPER_PATH="$INSTALL_DIR/$WRAPPER_NAME"

# Get the directory where this script lives (the chat loop source)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAT_LOOP_PY="$SCRIPT_DIR/chat_loop.py"

# Help message
show_help() {
    cat << EOF
Strands Chat Loop - Installation Script

Usage:
  ./install.sh              Install chat loop command globally
  ./install.sh --uninstall  Remove chat loop command
  ./install.sh --help       Show this help message

This will:
  1. Install Python dependencies to your system or virtual environment
  2. Create a 'chat_loop' command in ~/.local/bin
  3. Add ~/.local/bin to your PATH if needed

After installation, run:
  chat_loop path/to/agent.py

EOF
}

# Print colored message
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Python 3 is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    local python_version=$(python3 --version | cut -d' ' -f2)
    print_success "Found Python $python_version"
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."

    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        # Check if pip is available
        if ! python3 -m pip --version &> /dev/null; then
            print_error "pip is not available. Please install pip for Python 3."
            exit 1
        fi

        # Ask user about installation method
        echo ""
        echo "Where would you like to install dependencies?"
        echo "  1) User install (recommended) - pip install --user"
        echo "  2) System install - pip install (may require sudo)"
        echo "  3) Skip - dependencies already installed"
        read -p "Choice [1]: " install_choice
        install_choice=${install_choice:-1}

        case $install_choice in
            1)
                python3 -m pip install --user -r "$SCRIPT_DIR/requirements.txt"
                print_success "Dependencies installed to user site-packages"
                ;;
            2)
                python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
                print_success "Dependencies installed system-wide"
                ;;
            3)
                print_info "Skipping dependency installation"
                ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac
    else
        print_warning "requirements.txt not found, skipping dependency installation"
    fi
}

# Create the wrapper script
create_wrapper() {
    print_info "Creating chat_loop wrapper script..."

    # Create ~/.local/bin if it doesn't exist
    mkdir -p "$INSTALL_DIR"

    # Create the wrapper script with actual path substitution
    cat > "$WRAPPER_PATH" << WRAPPER_EOF
#!/usr/bin/env python3
"""
Strands Chat Loop - Global Wrapper

This wrapper allows you to run the chat loop from anywhere:
  chat_loop path/to/agent.py [--config ~/.chatrc]
"""

import sys
import os
from pathlib import Path

# Get the actual chat_loop.py location (set during installation)
SCRIPT_DIR = Path("$SCRIPT_DIR")
CHAT_LOOP_PY = SCRIPT_DIR / "chat_loop.py"

# Check if chat_loop.py exists
if not CHAT_LOOP_PY.exists():
    print(f"Error: Could not find chat_loop.py at {CHAT_LOOP_PY}", file=sys.stderr)
    print("\\nThe installation may have moved. Please run install.sh again.", file=sys.stderr)
    sys.exit(1)

# Add the chat loop directory to Python path
sys.path.insert(0, str(SCRIPT_DIR))

# Import and run the main function
try:
    from chat_loop import main
    sys.exit(main())
except ImportError as e:
    print(f"Error importing chat_loop: {e}", file=sys.stderr)
    print("\\nPlease ensure dependencies are installed:", file=sys.stderr)
    print(f"  cd {SCRIPT_DIR}", file=sys.stderr)
    print("  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error running chat_loop: {e}", file=sys.stderr)
    sys.exit(1)
WRAPPER_EOF

    # Make the wrapper executable
    chmod +x "$WRAPPER_PATH"

    print_success "Wrapper created at $WRAPPER_PATH"
}

# Update PATH in shell rc files
update_path() {
    local shell_rc=""

    # Detect shell
    if [ -n "$BASH_VERSION" ]; then
        shell_rc="$HOME/.bashrc"
        [ -f "$HOME/.bash_profile" ] && shell_rc="$HOME/.bash_profile"
    elif [ -n "$ZSH_VERSION" ]; then
        shell_rc="$HOME/.zshrc"
    else
        shell_rc="$HOME/.profile"
    fi

    # Check if ~/.local/bin is already in PATH
    if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        print_success "~/.local/bin is already in PATH"
        return
    fi

    # Add to PATH in rc file
    print_info "Adding ~/.local/bin to PATH in $shell_rc..."

    if [ -f "$shell_rc" ]; then
        # Check if already added
        if grep -q "export PATH=\"\$HOME/.local/bin:\$PATH\"" "$shell_rc" 2>/dev/null; then
            print_info "PATH already configured in $shell_rc"
        else
            echo "" >> "$shell_rc"
            echo "# Added by strands_chat_loop installer" >> "$shell_rc"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$shell_rc"
            print_success "Updated $shell_rc"
            print_warning "Run 'source $shell_rc' or restart your terminal to use the command"
        fi
    else
        print_warning "Could not find shell rc file. Please add ~/.local/bin to your PATH manually:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

# Uninstall function
uninstall() {
    print_info "Uninstalling chat_loop..."

    if [ -f "$WRAPPER_PATH" ]; then
        rm "$WRAPPER_PATH"
        print_success "Removed $WRAPPER_PATH"
    else
        print_info "Wrapper not found, nothing to remove"
    fi

    print_info "Uninstallation complete"
    echo ""
    print_info "Note: Python dependencies and PATH modifications were not removed."
    print_info "To remove dependencies, run:"
    echo "  pip uninstall anthropic-bedrock pyyaml rich"
}

# Main installation function
install() {
    echo ""
    echo "╔═══════════════════════════════════════════════╗"
    echo "║   Strands Chat Loop - Installation Script    ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""

    # Pre-flight checks
    check_python

    # Install dependencies
    install_dependencies

    # Create wrapper script
    echo ""
    create_wrapper

    # Update PATH
    echo ""
    update_path

    # Success message
    echo ""
    echo "╔═══════════════════════════════════════════════╗"
    echo "║            Installation Complete!             ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    print_success "Chat loop installed successfully!"
    echo ""
    print_info "Usage:"
    echo "  chat_loop path/to/agent.py"
    echo "  chat_loop path/to/agent.py --config ~/.chatrc-custom"
    echo ""
    print_info "Example:"
    echo "  chat_loop AWS_Strands/Product_Pete/agent.py"
    echo ""

    # Check if command is available now
    if command -v chat_loop &> /dev/null; then
        print_success "Command is ready to use!"
    else
        print_warning "Command not yet available in current shell"
        print_info "Run: source ~/.bashrc  (or ~/.zshrc)"
        print_info "Or restart your terminal"
    fi

    echo ""
}

# Parse arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --uninstall)
        uninstall
        exit 0
        ;;
    "")
        install
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
