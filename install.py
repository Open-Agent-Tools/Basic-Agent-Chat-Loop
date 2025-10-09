#!/usr/bin/env python3
"""
Strands Chat Loop - Cross-Platform Python Installer

This installer works on Windows, macOS, and Linux.
It provides a fallback when shell scripts are not available.

Usage:
    python install.py           # Install
    python install.py --help    # Show help
    python install.py --uninstall  # Uninstall
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


# Colors
class Colors:
    if platform.system() == "Windows":
        # Windows cmd might not support colors
        RED = YELLOW = GREEN = BLUE = NC = ""
    else:
        RED = "\033[0;31m"
        YELLOW = "\033[1;33m"
        GREEN = "\033[0;32m"
        BLUE = "\033[0;34m"
        NC = "\033[0m"


def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.NC} {msg}")


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.NC} {msg}")


def check_python():
    """Check Python version."""
    version = sys.version_info
    if version < (3, 8):
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True


def get_install_paths():
    """Get platform-specific installation paths."""
    home = Path.home()

    if platform.system() == "Windows":
        install_dir = home / ".local" / "bin"
        wrapper_name = "chat_loop.bat"
        python_wrapper = "chat_loop.py"
    else:
        install_dir = home / ".local" / "bin"
        wrapper_name = "chat_loop"
        python_wrapper = None

    return install_dir, wrapper_name, python_wrapper


def install_dependencies(script_dir):
    """Install Python dependencies."""
    print_info("Installing Python dependencies...")

    requirements = script_dir / "requirements.txt"
    if not requirements.exists():
        print_warning("requirements.txt not found, skipping")
        return True

    print()
    print("Where would you like to install dependencies?")
    print("  1) User install (recommended) - pip install --user")
    print("  2) System install - pip install")
    print("  3) Skip - dependencies already installed")

    try:
        choice = input("Choice [1]: ").strip() or "1"
    except (KeyboardInterrupt, EOFError):
        print()
        return False

    if choice == "1":
        cmd = [sys.executable, "-m", "pip", "install", "--user", "-r", str(requirements)]
    elif choice == "2":
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
    elif choice == "3":
        print_info("Skipping dependency installation")
        return True
    else:
        print_error("Invalid choice")
        return False

    try:
        subprocess.run(cmd, check=True)
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install dependencies")
        return False


def create_wrapper_unix(install_dir, wrapper_name, script_dir):
    """Create wrapper for Unix-like systems (macOS, Linux)."""
    wrapper_path = install_dir / wrapper_name

    # Use absolute path resolved at install time
    abs_script_dir = Path(script_dir).resolve()

    wrapper_content = f"""#!/usr/bin/env python3
\"\"\"Strands Chat Loop - Global Wrapper\"\"\"
import sys
from pathlib import Path

# Get the actual chat_loop.py location (set during installation)
SCRIPT_DIR = Path("{abs_script_dir}")
CHAT_LOOP_PY = SCRIPT_DIR / "chat_loop.py"

if not CHAT_LOOP_PY.exists():
    print(f"Error: Could not find chat_loop.py at {{CHAT_LOOP_PY}}", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(SCRIPT_DIR))

try:
    from chat_loop import main
    sys.exit(main())
except ImportError as e:
    print(f"Error importing chat_loop: {{e}}", file=sys.stderr)
    print(f"\\nInstall dependencies: cd {{SCRIPT_DIR}} && pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)
"""

    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)

    return wrapper_path


def create_wrapper_windows(install_dir, wrapper_name, python_wrapper, script_dir):
    """Create wrapper for Windows."""
    # Use absolute path resolved at install time
    abs_script_dir = Path(script_dir).resolve()

    # Python wrapper
    py_path = install_dir / python_wrapper
    py_content = f"""import sys
from pathlib import Path

# Get the actual chat_loop.py location (set during installation)
SCRIPT_DIR = Path(r"{abs_script_dir}")
CHAT_LOOP_PY = SCRIPT_DIR / "chat_loop.py"

if not CHAT_LOOP_PY.exists():
    print(f"Error: Could not find chat_loop.py at {{CHAT_LOOP_PY}}", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(SCRIPT_DIR))

try:
    from chat_loop import main
    sys.exit(main())
except ImportError as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
    py_path.write_text(py_content)

    # Batch wrapper
    bat_path = install_dir / wrapper_name
    bat_content = f'@echo off\npython "{py_path}" %*\n'
    bat_path.write_text(bat_content)

    return bat_path


def update_path_unix(install_dir):
    """Update PATH for Unix-like systems."""
    # Check if already in PATH
    path_env = os.environ.get("PATH", "")
    if str(install_dir) in path_env:
        print_success(f"{install_dir} already in PATH")
        return True

    # Detect shell
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc_file = Path.home() / ".zshrc"
    elif "bash" in shell:
        rc_file = Path.home() / ".bashrc"
        if not rc_file.exists():
            rc_file = Path.home() / ".bash_profile"
    else:
        rc_file = Path.home() / ".profile"

    # Add to rc file
    path_line = f'\nexport PATH="$HOME/.local/bin:$PATH"  # Added by strands_chat_loop\n'

    if rc_file.exists():
        content = rc_file.read_text()
        if "strands_chat_loop" in content or str(install_dir) in content:
            print_info(f"PATH already configured in {rc_file}")
            return True

        with open(rc_file, "a") as f:
            f.write(path_line)

        print_success(f"Updated {rc_file}")
        print_warning(f"Run: source {rc_file}")
        return True
    else:
        print_warning(f"Could not find {rc_file}")
        print_info(f"Add manually: export PATH=\"$HOME/.local/bin:$PATH\"")
        return True


def update_path_windows(install_dir):
    """Update PATH for Windows."""
    # Check if already in PATH
    path_env = os.environ.get("PATH", "")
    if str(install_dir) in path_env:
        print_success(f"{install_dir} already in PATH")
        return True

    print_info("Attempting to update user PATH...")

    try:
        # Use setx to update user PATH
        new_path = f"{path_env};{install_dir}"
        result = subprocess.run(
            ["setx", "PATH", new_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success("PATH updated successfully")
            print_warning("Restart your terminal for changes to take effect")
            return True
        else:
            raise subprocess.CalledProcessError(result.returncode, "setx")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("Could not automatically update PATH")
        print_info("Add manually through System Properties:")
        print(f"  1. Search for 'Environment Variables'")
        print(f"  2. Edit user PATH variable")
        print(f"  3. Add: {install_dir}")
        return True


def install(script_dir):
    """Main installation function."""
    print()
    print("╔═══════════════════════════════════════════════╗")
    print("║   Strands Chat Loop - Installation Script    ║")
    print("╚═══════════════════════════════════════════════╝")
    print()

    # Check Python
    if not check_python():
        return False

    # Install dependencies
    if not install_dependencies(script_dir):
        return False

    # Get paths
    install_dir, wrapper_name, python_wrapper = get_install_paths()

    # Create install directory
    print()
    print_info(f"Creating {install_dir}...")
    install_dir.mkdir(parents=True, exist_ok=True)

    # Create wrapper
    print_info("Creating wrapper script...")
    try:
        if platform.system() == "Windows":
            wrapper_path = create_wrapper_windows(install_dir, wrapper_name, python_wrapper, script_dir)
        else:
            wrapper_path = create_wrapper_unix(install_dir, wrapper_name, script_dir)

        print_success(f"Wrapper created at {wrapper_path}")
    except Exception as e:
        print_error(f"Failed to create wrapper: {e}")
        return False

    # Update PATH
    print()
    if platform.system() == "Windows":
        update_path_windows(install_dir)
    else:
        update_path_unix(install_dir)

    # Success
    print()
    print("╔═══════════════════════════════════════════════╗")
    print("║            Installation Complete!             ║")
    print("╚═══════════════════════════════════════════════╝")
    print()
    print_success("Chat loop installed successfully!")
    print()
    print_info("Usage:")
    print("  chat_loop path/to/agent.py")
    print("  chat_loop path/to/agent.py --config ~/.chatrc-custom")
    print()

    return True


def uninstall():
    """Uninstall the chat loop command."""
    print()
    print_info("Uninstalling chat_loop...")

    install_dir, wrapper_name, python_wrapper = get_install_paths()

    removed = False

    # Remove wrapper
    wrapper_path = install_dir / wrapper_name
    if wrapper_path.exists():
        wrapper_path.unlink()
        print_success(f"Removed {wrapper_path}")
        removed = True

    # Remove Python wrapper (Windows)
    if python_wrapper:
        py_path = install_dir / python_wrapper
        if py_path.exists():
            py_path.unlink()
            print_success(f"Removed {py_path}")
            removed = True

    if not removed:
        print_info("Nothing to remove")

    print()
    print_info("Note: Dependencies and PATH not modified")
    print_info("To remove dependencies:")
    print("  pip uninstall anthropic-bedrock pyyaml rich")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Strands Chat Loop Installer"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall the chat loop command"
    )

    args = parser.parse_args()

    # Get script directory
    script_dir = Path(__file__).parent.resolve()

    if args.uninstall:
        uninstall()
    else:
        success = install(script_dir)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
