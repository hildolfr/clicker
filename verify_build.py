#!/usr/bin/env python3
"""
Verification script for the built Clicker executable.
"""

import subprocess
import sys
import os
import re
from pathlib import Path

def get_source_version():
    """Extract version from clicker/__init__.py"""
    try:
        init_file = Path("clicker/__init__.py")
        if not init_file.exists():
            return None
        
        content = init_file.read_text(encoding='utf-8')
        match = re.search(r'__version__ = "([^"]+)"', content)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error reading version: {e}")
    return None

def find_versioned_executable():
    """Find the versioned executable in dist directory"""
    dist_path = Path("dist")
    if not dist_path.exists():
        return None
    
    # Look for Clicker-v*.exe files
    exe_files = list(dist_path.glob("Clicker-v*.exe"))
    if exe_files:
        return exe_files[0]  # Return the first match
    
    # Fallback to old naming
    legacy_exe = dist_path / "Clicker.exe"
    if legacy_exe.exists():
        return legacy_exe
    
    return None

def verify_executable():
    """Verify that the built executable is working correctly."""
    source_version = get_source_version()
    if not source_version:
        print("❌ ERROR: Could not extract version from source")
        return False
    
    print("=" * 60)
    print(f"VERIFYING CLICKER v{source_version} EXECUTABLE BUILD")
    print("=" * 60)
    
    # Find the executable
    exe_path = find_versioned_executable()
    if not exe_path:
        print("❌ ERROR: No Clicker executable found in dist/ directory")
        print("Expected: Clicker-v{}.exe or Clicker.exe".format(source_version))
        return False
    
    print(f"✅ Executable found: {exe_path}")
    print(f"📁 File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
    print(f"📅 Build time: {exe_path.stat().st_mtime}")
    
    # Extract version from filename if versioned
    filename_version = None
    if "Clicker-v" in exe_path.name:
        match = re.search(r'Clicker-v([^.]+)\.exe', exe_path.name)
        if match:
            filename_version = match.group(1)
            print(f"📦 Filename version: {filename_version}")
    
    # Verify source version
    try:
        import clicker
        source_version_check = clicker.__version__
        print(f"📦 Source version: {source_version_check}")
        
        if source_version_check == source_version:
            print(f"✅ Source version is correct: {source_version}")
        else:
            print(f"❌ ERROR: Version mismatch in source - expected {source_version}, got {source_version_check}")
            return False
        
        # Check filename version matches if present
        if filename_version and filename_version != source_version:
            print(f"❌ ERROR: Filename version {filename_version} doesn't match source version {source_version}")
            return False
        elif filename_version:
            print(f"✅ Filename version matches source: {filename_version}")
            
    except ImportError as e:
        print(f"❌ ERROR: Could not import clicker module: {e}")
        return False
    
    # Check that it's a Windows executable
    with open(exe_path, 'rb') as f:
        magic = f.read(2)
        if magic == b'MZ':
            print("✅ File is a valid Windows executable (PE format)")
        else:
            print("❌ ERROR: File doesn't appear to be a Windows executable")
            return False
    
    # Check for build info file
    build_info_path = exe_path.parent / "BUILD_INFO.txt"
    if build_info_path.exists():
        print("✅ Build info file found")
        try:
            build_info = build_info_path.read_text(encoding='utf-8')
            print("📄 Build Information:")
            for line in build_info.strip().split('\n'):
                print(f"   {line}")
        except Exception as e:
            print(f"⚠️  Could not read build info: {e}")
    else:
        print("⚠️  No build info file found")
    
    print("\n" + "=" * 60)
    print("🎉 BUILD VERIFICATION SUCCESSFUL!")
    print("=" * 60)
    print(f"Ready for release: Clicker v{source_version}")
    print(f"Location: {exe_path.absolute()}")
    print(f"Size: {exe_path.stat().st_size:,} bytes")
    print("\nYou can now:")
    print("1. Test the executable by running it")
    print("2. Create a GitHub release with this executable")
    print(f"3. Update download links to point to v{source_version}")
    
    return True

if __name__ == "__main__":
    success = verify_executable()
    sys.exit(0 if success else 1) 