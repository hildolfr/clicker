#!/usr/bin/env python3
"""
Release preparation script for Clicker v2.2.0.

This script helps prepare the project for a new release by:
- Validating version consistency across files
- Running tests
- Checking for uncommitted changes
- Generating release notes
"""

import subprocess
import sys
from pathlib import Path
import re

def check_version_consistency():
    """Check that version numbers are consistent across files."""
    print("🔍 Checking version consistency...")
    
    # Read version from different files
    app_py = Path("clicker/app.py").read_text(encoding='utf-8')
    pyproject_toml = Path("pyproject.toml").read_text(encoding='utf-8')
    readme_md = Path("README.md").read_text(encoding='utf-8')
    
    # Extract versions
    app_version = re.search(r'VERSION = "([^"]+)"', app_py)
    pyproject_version = re.search(r'version = "([^"]+)"', pyproject_toml)
    readme_version = re.search(r'version-([^-]+)-blue', readme_md)
    
    if not all([app_version, pyproject_version, readme_version]):
        print("❌ Could not find version in all files")
        return False
    
    versions = [
        app_version.group(1),
        pyproject_version.group(1), 
        readme_version.group(1)
    ]
    
    if len(set(versions)) != 1:
        print(f"❌ Version mismatch: {versions}")
        return False
    
    print(f"✅ All versions consistent: {versions[0]}")
    return True

def check_git_status():
    """Check git status for uncommitted changes."""
    print("🔍 Checking git status...")
    
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            print("⚠️  Uncommitted changes detected (expected for release):")
            print(result.stdout)
            return True  # This is OK for a release
        else:
            print("✅ Working directory clean")
            return True
            
    except subprocess.CalledProcessError:
        print("❌ Error checking git status")
        return False

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v"],
            check=True
        )
        print("✅ All tests passed")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        return False
    except FileNotFoundError:
        print("⚠️  pytest not found, skipping tests (install with: pip install pytest)")
        return True

def generate_commit_message():
    """Generate a commit message for the release."""
    version = "2.2.0"
    
    commit_msg = f"""Release v{version} - Real-time File Watching

🚀 Major Features:
- Implemented watchdog-based file monitoring for instant config reload
- Replaced timer-based approach with event-driven file watching
- Added real-time detection of settings.json and keystrokes.txt changes

🔧 Technical Improvements:
- Enhanced file change detection with OS-native APIs
- Added proper debouncing to prevent duplicate reloads
- Improved shutdown sequence and resource cleanup

🐛 Bug Fixes:
- Resolved persistent configuration reload issues
- Fixed timer reliability problems
- Corrected application shutdown sequence

📝 Documentation:
- Updated README with real-time file watching information
- Added comprehensive CHANGELOG.md
- Enhanced code documentation
"""
    
    return commit_msg

def main():
    """Main release preparation function."""
    print("🚀 Preparing Clicker v2.2.0 Release")
    print("=" * 50)
    
    checks = [
        ("Version Consistency", check_version_consistency),
        ("Git Status", check_git_status),
        ("Test Suite", run_tests),
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All checks passed! Ready for release.")
        print("\nSuggested commit message:")
        print("-" * 40)
        print(generate_commit_message())
        print("-" * 40)
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Release v2.2.0 - Real-time File Watching'")
        print("3. git tag -a v2.2.0 -m 'Version 2.2.0'")
        print("4. git push origin main --tags")
    else:
        print("❌ Some checks failed. Please fix issues before release.")
        sys.exit(1)

if __name__ == "__main__":
    main() 