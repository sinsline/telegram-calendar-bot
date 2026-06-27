#!/usr/bin/env python3
"""
Test runner for Telegram Calendar Bot

Provides convenient commands to run different test suites:
- Unit tests
- Integration tests  
- Performance tests
- Full test suite
"""

import argparse
import subprocess
import sys
import os
import time
from pathlib import Path

# Add src to Python path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))


def run_command(cmd, description=""):
    """Run shell command and return result"""
    if description:
        print(f"\\n🔍 {description}")
        print(f"Running: {' '.join(cmd)}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ Success ({duration:.2f}s)")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ Failed ({duration:.2f}s)")
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
    
    return result.returncode == 0


def run_unit_tests():
    """Run all unit tests"""
    return run_command([
        "pytest", 
        "tests/services/",
        "-v",
        "--tb=short",
        "--durations=10"
    ], "Running unit tests")


def run_integration_tests():
    """Run integration tests"""
    return run_command([
        "pytest",
        "tests/integration/test_full_workflow.py",
        "-v", 
        "--tb=short",
        "-m", "not slow"
    ], "Running integration tests")


def run_performance_tests():
    """Run performance tests"""
    return run_command([
        "pytest",
        "tests/integration/test_performance.py", 
        "-v",
        "--tb=short",
        "-m", "slow"
    ], "Running performance tests")


def run_quick_tests():
    """Run quick test suite (unit + fast integration)"""
    print("🚀 Quick Test Suite")
    
    success = True
    
    # Unit tests
    if not run_unit_tests():
        success = False
    
    # Fast integration tests
    if not run_command([
        "pytest",
        "tests/integration/", 
        "-v",
        "-m", "not slow",
        "--durations=5"
    ], "Running fast integration tests"):
        success = False
    
    return success


def run_full_tests():
    """Run complete test suite"""
    print("🧪 Complete Test Suite")
    
    success = True
    
    # Unit tests
    if not run_unit_tests():
        success = False
    
    # Integration tests
    if not run_integration_tests():
        success = False
    
    # Performance tests
    if not run_performance_tests():
        success = False
    
    return success


def run_coverage():
    """Run tests with coverage"""
    return run_command([
        "pytest",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml",
        "-v"
    ], "Running tests with coverage")


def lint_code():
    """Run code linting"""
    success = True
    
    # Flake8
    if not run_command([
        "flake8", "src/", "tests/",
        "--max-line-length=100",
        "--ignore=E203,W503"
    ], "Running flake8 linting"):
        success = False
    
    # Black formatting check
    if not run_command([
        "black", "--check", "src/", "tests/"
    ], "Checking code formatting with black"):
        success = False
    
    return success


def check_dependencies():
    """Check if all test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov", 
        "flake8",
        "black"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All test dependencies are installed")
    return True


def main():
    parser = argparse.ArgumentParser(description="Test runner for Telegram Calendar Bot")
    
    parser.add_argument(
        "suite",
        choices=["unit", "integration", "performance", "quick", "full", "coverage", "lint", "deps"],
        help="Test suite to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fail-fast", "-x", 
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    # Change to project root
    os.chdir(PROJECT_ROOT)
    
    print(f"Telegram Calendar Bot Test Runner")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Test suite: {args.suite}")
    
    start_time = time.time()
    
    # Run requested test suite
    if args.suite == "unit":
        success = run_unit_tests()
    elif args.suite == "integration": 
        success = run_integration_tests()
    elif args.suite == "performance":
        success = run_performance_tests()
    elif args.suite == "quick":
        success = run_quick_tests()
    elif args.suite == "full":
        success = run_full_tests()
    elif args.suite == "coverage":
        success = run_coverage()
    elif args.suite == "lint":
        success = lint_code()
    elif args.suite == "deps":
        success = check_dependencies()
    else:
        print(f"Unknown test suite: {args.suite}")
        success = False
    
    total_time = time.time() - start_time
    
    print(f"\\n{'='*50}")
    if success:
        print(f"🎉 All tests passed! ({total_time:.2f}s)")
        sys.exit(0)
    else:
        print(f"💥 Tests failed! ({total_time:.2f}s)")
        sys.exit(1)


if __name__ == "__main__":
    main()