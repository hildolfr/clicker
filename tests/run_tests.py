#!/usr/bin/env python3
"""
Test runner script for the Clicker application.

Provides options to run different test suites with coverage reporting
and performance benchmarks.
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Make sure pytest and coverage are installed:")
        print("pip install pytest pytest-cov")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Clicker application tests")
    
    # Test selection options
    parser.add_argument(
        '--unit', action='store_true',
        help='Run unit tests only'
    )
    parser.add_argument(
        '--integration', action='store_true', 
        help='Run integration tests only'
    )
    parser.add_argument(
        '--all', action='store_true',
        help='Run all tests (default)'
    )
    
    # Test filtering options
    parser.add_argument(
        '--fast', action='store_true',
        help='Skip slow tests'
    )
    parser.add_argument(
        '--windows-only', action='store_true',
        help='Run only Windows-specific tests'
    )
    parser.add_argument(
        '--no-windows', action='store_true',
        help='Skip Windows-specific tests'
    )
    
    # Coverage options
    parser.add_argument(
        '--coverage', action='store_true',
        help='Generate coverage report'
    )
    parser.add_argument(
        '--coverage-html', action='store_true',
        help='Generate HTML coverage report'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Quiet output'
    )
    parser.add_argument(
        '--junit-xml', metavar='FILE',
        help='Generate JUnit XML report'
    )
    
    # Performance options
    parser.add_argument(
        '--benchmark', action='store_true',
        help='Run performance benchmarks'
    )
    
    # Specific test options
    parser.add_argument(
        '--test', '-k', metavar='PATTERN',
        help='Run tests matching pattern'
    )
    parser.add_argument(
        '--file', metavar='FILE',
        help='Run specific test file'
    )
    
    args = parser.parse_args()
    
    # Determine test directory
    script_dir = Path(__file__).parent
    test_dir = script_dir
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add test directory/file
    if args.file:
        cmd.append(args.file)
    elif args.unit:
        cmd.append(str(test_dir / 'unit'))
    elif args.integration:
        cmd.append(str(test_dir / 'integration'))
    else:
        cmd.append(str(test_dir))
    
    # Add test filtering
    if args.test:
        cmd.extend(['-k', args.test])
    
    # Add marker-based filtering
    markers = []
    if args.fast:
        markers.append('not slow')
    if args.windows_only:
        markers.append('windows_only')
    if args.no_windows:
        markers.append('not windows_only')
    
    if markers:
        cmd.extend(['-m', ' and '.join(markers)])
    
    # Add output options
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    if args.junit_xml:
        cmd.extend(['--junit-xml', args.junit_xml])
    
    # Add coverage options
    if args.coverage or args.coverage_html:
        cmd.extend([
            '--cov=clicker',
            '--cov-report=term'
        ])
        
        if args.coverage_html:
            cmd.extend(['--cov-report=html'])
    
    # Run the tests
    success = run_command(cmd, "Test Suite")
    
    # Run benchmarks if requested
    if args.benchmark and success:
        benchmark_cmd = [
            'python', '-m', 'pytest', 
            str(test_dir / 'integration'),
            '-k', 'performance or benchmark',
            '-v'
        ]
        run_command(benchmark_cmd, "Performance Benchmarks")
    
    # Show coverage summary if generated
    if args.coverage and success:
        print(f"\n{'='*60}")
        print("Coverage Summary")
        print('='*60)
        print("Detailed coverage report available above.")
        
        if args.coverage_html:
            html_dir = Path.cwd() / 'htmlcov'
            if html_dir.exists():
                print(f"HTML coverage report: {html_dir / 'index.html'}")
    
    # Final summary
    print(f"\n{'='*60}")
    if success:
        print("✅ All tests completed successfully!")
        print("\nNext steps:")
        print("- Review any test failures or warnings")
        print("- Check coverage reports if generated")
        print("- Run integration tests on target environment")
    else:
        print("❌ Some tests failed!")
        print("\nTroubleshooting:")
        print("- Check test output for specific failure details")
        print("- Ensure all dependencies are installed")
        print("- Verify test environment setup")
        sys.exit(1)


def install_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    
    dependencies = [
        'pytest>=7.0',
        'pytest-cov>=4.0',
        'pytest-mock>=3.0',
        'pytest-benchmark>=4.0'
    ]
    
    cmd = [sys.executable, '-m', 'pip', 'install'] + dependencies
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Try running manually:")
        print(f"pip install {' '.join(dependencies)}")


if __name__ == '__main__':
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("pytest not found. Installing dependencies...")
        install_dependencies()
        try:
            import pytest
        except ImportError:
            print("❌ Failed to install pytest. Please install manually:")
            print("pip install pytest pytest-cov")
            sys.exit(1)
    
    main() 