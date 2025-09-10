#!/usr/bin/env python3
"""
Test runner script for DICTATOR
"""

import sys
import subprocess
import os
from pathlib import Path


def run_tests(test_type="all", coverage=True, verbose=True):
    """
    Run tests with various options
    
    Args:
        test_type: "all", "unit", "integration", "cli", "gui"
        coverage: Whether to include coverage reporting
        verbose: Whether to run in verbose mode
    """
    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add test selection based on type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration": 
        cmd.extend(["-m", "integration"])
    elif test_type == "cli":
        cmd.append("tests/test_cli.py")
    elif test_type == "gui":
        cmd.extend(["-m", "gui"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    
    print(f"🧪 Running tests: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Install test dependencies with: pip install -e .[test]")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_linting():
    """Run code linting"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🔍 Running linting...")
    
    # Try different linting tools
    linters = [
        (["python", "-m", "flake8", "src", "tests"], "flake8"),
        (["python", "-m", "pylint", "src"], "pylint"), 
        (["python", "-m", "mypy", "src"], "mypy")
    ]
    
    success = True
    for cmd, name in linters:
        try:
            print(f"Running {name}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {name}: passed")
            else:
                print(f"⚠️ {name}: found issues")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                success = False
        except FileNotFoundError:
            print(f"⚠️ {name}: not installed")
    
    return 0 if success else 1


def run_quick_check():
    """Run a quick check of critical functionality"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("⚡ Running quick checks...")
    
    checks = [
        # Import tests
        (["python", "-c", "import src.cli; print('✅ CLI imports OK')"], "CLI import"),
        (["python", "-c", "import src.version; print('✅ Version imports OK')"], "Version import"),
        (["python", "-c", "import src.__main__; print('✅ Main imports OK')"], "Main import"),
        
        # CLI functionality
        (["python", "-m", "src.cli", "--version"], "CLI version"),
        (["python", "-m", "src.cli", "--help"], "CLI help"),
        
        # Quick unit tests
        (["python", "-m", "pytest", "tests/test_version.py", "-v"], "Version tests"),
    ]
    
    success = True
    for cmd, name in checks:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: FAILED")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
                success = False
        except subprocess.TimeoutExpired:
            print(f"⏰ {name}: TIMEOUT")
            success = False
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            success = False
    
    return 0 if success else 1


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DICTATOR Test Runner")
    parser.add_argument(
        "command",
        choices=["test", "lint", "quick", "all"],
        help="What to run"
    )
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "cli", "gui", "fast"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    parser.add_argument(
        "--quiet",
        action="store_true", 
        help="Run in quiet mode"
    )
    
    args = parser.parse_args()
    
    if args.command == "test":
        exit_code = run_tests(
            test_type=args.type,
            coverage=not args.no_coverage,
            verbose=not args.quiet
        )
    elif args.command == "lint":
        exit_code = run_linting()
    elif args.command == "quick":
        exit_code = run_quick_check()
    elif args.command == "all":
        print("🚀 Running full test suite...")
        
        # Quick check first
        exit_code = run_quick_check()
        if exit_code != 0:
            print("❌ Quick check failed, skipping other tests")
            sys.exit(exit_code)
        
        # Full tests
        exit_code = run_tests(
            test_type=args.type,
            coverage=not args.no_coverage,
            verbose=not args.quiet
        )
        
        # Linting
        lint_code = run_linting()
        if lint_code != 0:
            print("⚠️ Linting found issues")
            exit_code = max(exit_code, lint_code)
    
    if exit_code == 0:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()