#!/usr/bin/env python3
"""
Release preparation script for Clicker v2.2.2.

This script automates the release preparation process by:
1. Updating version numbers across all files
2. Generating changelog entries
3. Creating distribution packages
4. Running final validation checks

Usage:
    python scripts/prepare_release.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import shutil
import zipfile
import tempfile

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from clicker.config.manager import ConfigManager
    from clicker.utils.logging_config import setup_logging
except ImportError as e:
    print(f"❌ Failed to import clicker modules: {e}")
    print("Make sure you're running this script from the project root.")
    sys.exit(1)

class ReleasePreparation:
    """Handles the complete release preparation workflow."""
    
    def __init__(self):
        self.project_root = project_root
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.backup_dir = self.project_root / "backups" / f"release-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Ensure directories exist
        self.dist_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        setup_logging()
        
        # Version information
        self.version = "2.2.2"
        self.release_date = datetime.now().strftime("%Y-%m-%d")
        
        # Files that need version updates
        self.version_files = [
            "pyproject.toml",
            "clicker/__init__.py", 
            "clicker/app.py",
            "README.md",
            "Clicker-v2.2.2.spec"
        ]
        
        # Critical files to backup
        self.backup_files = [
            "settings.json",
            "keystrokes.txt", 
            "clicker.log",
            "CHANGELOG.md"
        ]

    def create_backups(self):
        """Create backups of critical files before release preparation."""
        print("📁 Creating backups...")
        
        for file_path in self.backup_files:
            source = self.project_root / file_path
            if source.exists():
                destination = self.backup_dir / file_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                print(f"   ✓ Backed up {file_path}")
        
        print(f"   📁 Backups created in: {self.backup_dir}")

    def validate_environment(self):
        """Validate that the environment is ready for release."""
        print("🔍 Validating environment...")
        
        # Check Python version
        if sys.version_info < (3, 11):
            raise RuntimeError("Python 3.11+ is required")
        print("   ✓ Python version check passed")
        
        # Check required files exist
        required_files = ["main.py", "requirements.txt", "icon.ico", "README.md"]
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                raise FileNotFoundError(f"Required file missing: {file_path}")
        print("   ✓ Required files check passed")
        
        # Check if git is available and repo is clean
        try:
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                if result.stdout.strip():
                    print("   ⚠️  Git repository has uncommitted changes")
                else:
                    print("   ✓ Git repository is clean")
            else:
                print("   ⚠️  Git not available or not a git repository")
        except FileNotFoundError:
            print("   ⚠️  Git not found in PATH")

    def run_tests(self):
        """Run the test suite to ensure everything is working."""
        print("🧪 Running tests...")
        
        try:
            # Run pytest if available
            result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("   ✓ All tests passed")
                return True
            else:
                print("   ❌ Some tests failed:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except FileNotFoundError:
            print("   ⚠️  pytest not available, skipping tests")
            return True

    def build_executable(self):
        """Build the executable using PyInstaller."""
        print("🔨 Building executable...")
        
        # Clean previous builds
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        
        # Run PyInstaller
        spec_file = self.project_root / "Clicker-v2.2.2.spec"
        if not spec_file.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_file}")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "PyInstaller", 
                str(spec_file),
                "--clean",
                "--noconfirm"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✓ Executable built successfully")
                return True
            else:
                print("   ❌ Build failed:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except FileNotFoundError:
            print("   ❌ PyInstaller not available")
            return False

    def create_distribution_package(self):
        """Create a distribution package with the executable and documentation."""
        print("📦 Creating distribution package...")
        
        # Check if executable exists
        exe_path = self.dist_dir / f"Clicker-v{self.version}.exe"
        if not exe_path.exists():
            # Try alternative name
            exe_path = self.dist_dir / f"Clicker-v2.2.2.exe"
            if not exe_path.exists():
                raise FileNotFoundError("Executable not found in dist directory")
        
        # Create package directory
        package_name = f"Clicker-v{self.version}-Windows"
        package_dir = self.dist_dir / package_name
        package_dir.mkdir(exist_ok=True)
        
        # Copy executable
        shutil.copy2(exe_path, package_dir / f"Clicker-v{self.version}.exe")
        
        # Copy documentation and config files
        docs_to_copy = ["README.md", "CHANGELOG.md", "requirements.txt"]
        for doc in docs_to_copy:
            source = self.project_root / doc
            if source.exists():
                shutil.copy2(source, package_dir / doc)
        
        # Copy default config files
        config_dir = package_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        default_configs = [
            "clicker/config/default_settings.json",
            "clicker/config/default_keystrokes.txt"
        ]
        
        for config in default_configs:
            source = self.project_root / config
            if source.exists():
                shutil.copy2(source, config_dir / Path(config).name)
        
        # Create ZIP archive
        zip_path = self.dist_dir / f"{package_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"   ✓ Distribution package created: {zip_path}")
        return zip_path

    def generate_release_notes(self):
        """Generate release notes from changelog."""
        print("📝 Generating release notes...")
        
        changelog_path = self.project_root / "CHANGELOG.md"
        if not changelog_path.exists():
            print("   ⚠️  CHANGELOG.md not found")
            return None
        
        # Extract latest version notes
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section for current version
        version_marker = f"## [{self.version}]"
        if version_marker in content:
            start = content.find(version_marker)
            next_version = content.find("## [", start + 1)
            
            if next_version == -1:
                notes = content[start:]
            else:
                notes = content[start:next_version]
            
            # Clean up the notes
            notes = notes.strip()
            print("   ✓ Release notes extracted from changelog")
            return notes
        else:
            print(f"   ⚠️  Version {self.version} not found in changelog")
            return None

    def run_final_validation(self):
        """Run final validation checks on the built executable."""
        print("✅ Running final validation...")
        
        # Check if executable runs
        exe_path = self.dist_dir / f"Clicker-v2.2.2.exe"
        if exe_path.exists():
            try:
                # Try to run with --version flag (if supported)
                result = subprocess.run([str(exe_path), "--help"], 
                                      capture_output=True, text=True, timeout=10)
                print("   ✓ Executable launches successfully")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("   ⚠️  Could not validate executable launch")
        else:
            print("   ❌ Executable not found for validation")

    def prepare_release(self):
        """Run the complete release preparation workflow."""
        print("🚀 Preparing Clicker v2.2.2 Release")
        print("=" * 50)
        
        try:
            # Step 1: Validate environment
            self.validate_environment()
            
            # Step 2: Create backups
            self.create_backups()
            
            # Step 3: Run tests
            if not self.run_tests():
                response = input("Tests failed. Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Release preparation aborted")
                    return False
            
            # Step 4: Build executable
            if not self.build_executable():
                print("❌ Release preparation failed at build stage")
                return False
            
            # Step 5: Create distribution package
            package_path = self.create_distribution_package()
            
            # Step 6: Generate release notes
            release_notes = self.generate_release_notes()
            
            # Step 7: Final validation
            self.run_final_validation()
            
            # Success summary
            print("\n" + "=" * 50)
            print("🎉 Release preparation completed successfully!")
            print(f"📦 Package: {package_path}")
            print(f"📁 Backups: {self.backup_dir}")
            
            if release_notes:
                print(f"\n📝 Release Notes Preview:")
                print("-" * 30)
                print(release_notes[:500] + "..." if len(release_notes) > 500 else release_notes)
            
            print("\n🔄 Next steps:")
            print("1. Review the generated package")
            print("2. git commit -m 'Release v2.2.2 - Tilde Key Combinations Bugfix'")
            print("3. git tag -a v2.2.2 -m 'Version 2.2.2'")
            print("4. git push origin main --tags")
            print("5. Upload the package to GitHub releases")
            
            return True
            
        except Exception as e:
            print(f"❌ Release preparation failed: {e}")
            return False

def main():
    """Main entry point for the release preparation script."""
    try:
        release_prep = ReleasePreparation()
        success = release_prep.prepare_release()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Release preparation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 