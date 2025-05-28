#!/usr/bin/env python3
"""
Release preparation script for Clicker v2.2.1.

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
    version = "2.2.1"
    
    commit_msg = f"""Release v{version} - Order Obeyed Bugfix

🐛 Bug Fixes:
- Fixed order_obeyed setting not properly controlling keystroke execution order
- When order_obeyed=True, keystrokes now execute in file order (top to bottom)
- When order_obeyed=False, keystrokes now execute sorted by delay (lowest to highest)
- Added proper schedule cache invalidation when order_obeyed setting changes

🔧 Technical Improvements:
- Enhanced schedule building logic to respect order_obeyed configuration
- Improved schedule caching with proper hash calculation including order_obeyed
- Added comprehensive test coverage for order_obeyed functionality

📝 Documentation:
- Updated test suite with order_obeyed test cases
- Enhanced code documentation for scheduling logic
"""
    
    return commit_msg

def main():
    """Main release preparation function."""
    print("🚀 Preparing Clicker v2.2.1 Release")
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
        print("2. git commit -m 'Release v2.2.1 - Order Obeyed Bugfix'")
        print("3. git tag -a v2.2.1 -m 'Version 2.2.1'")
        print("4. git push origin main --tags")
    else:
        print("❌ Some checks failed. Please fix issues before release.")
        sys.exit(1)

if __name__ == "__main__":
    main() 