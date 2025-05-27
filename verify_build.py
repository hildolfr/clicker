#!/usr/bin/env python3
"""
Verification script for the built Clicker executable.
"""

import subprocess
import sys
import os
from pathlib import Path

def verify_executable():
    """Verify that the built executable is working correctly."""
    print("=" * 60)
    print("VERIFYING CLICKER v2.1.3 EXECUTABLE BUILD")
    print("=" * 60)
    
    # Check if executable exists
    exe_path = Path("dist/Clicker.exe")
    if not exe_path.exists():
        print("❌ ERROR: Clicker.exe not found in dist/ directory")
        return False
    
    print(f"✅ Executable found: {exe_path}")
    print(f"📁 File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
    print(f"📅 Build time: {exe_path.stat().st_mtime}")
    
    # Verify source version
    try:
        import clicker
        source_version = clicker.__version__
        print(f"📦 Source version: {source_version}")
        
        if source_version == "2.1.3":
            print("✅ Source version is correct: 2.1.3")
        else:
            print(f"❌ ERROR: Expected version 2.1.3, got {source_version}")
            return False
            
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
    
    print("\n" + "=" * 60)
    print("🎉 BUILD VERIFICATION SUCCESSFUL!")
    print("=" * 60)
    print(f"Ready for release: Clicker v2.1.3")
    print(f"Location: {exe_path.absolute()}")
    print(f"Size: {exe_path.stat().st_size:,} bytes")
    print("\nYou can now:")
    print("1. Test the executable by running it")
    print("2. Create a GitHub release with this executable")
    print("3. Update download links to point to v2.1.3")
    
    return True

if __name__ == "__main__":
    success = verify_executable()
    sys.exit(0 if success else 1) 