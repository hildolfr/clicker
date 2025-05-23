"""
Test script to verify settings file migration.

This script tests whether the application correctly migrates old settings files 
with the 'pause_time' field to the new format with 'start_time_stagger'.
"""

import os
import json
import shutil
import sys

# Test setup
ORIGINAL_SETTINGS = 'settings.json'
TEST_SETTINGS = 'test_settings.json'
OLD_SETTINGS = 'old_settings.json'

def create_test_settings():
    """Create a test settings file with the old format."""
    old_settings = {
        "toggle_key": "~",
        "pause_time": 2.0,  # Using a different value to verify it's preserved
        "order_obeyed": False
    }
    with open(TEST_SETTINGS, 'w') as f:
        json.dump(old_settings, f, indent=4)
    print(f"Created test settings file: {TEST_SETTINGS}")

def backup_original_settings():
    """Backup the original settings file."""
    if os.path.exists(ORIGINAL_SETTINGS):
        with open(ORIGINAL_SETTINGS, 'r') as f:
            print(f"Original settings: {f.read().strip()}")
        # Backup the original settings
        shutil.copy2(ORIGINAL_SETTINGS, f"{ORIGINAL_SETTINGS}.bak")
        print(f"Backed up original settings to: {ORIGINAL_SETTINGS}.bak")

def restore_original_settings():
    """Restore the original settings file."""
    if os.path.exists(f"{ORIGINAL_SETTINGS}.bak"):
        shutil.copy2(f"{ORIGINAL_SETTINGS}.bak", ORIGINAL_SETTINGS)
        os.remove(f"{ORIGINAL_SETTINGS}.bak")
        print(f"Restored original settings from: {ORIGINAL_SETTINGS}.bak")

def run_test():
    """Run the migration test."""
    # Copy our test settings to the main settings file
    if os.path.exists(TEST_SETTINGS):
        shutil.copy2(TEST_SETTINGS, ORIGINAL_SETTINGS)
        print(f"Copied test settings to: {ORIGINAL_SETTINGS}")
    else:
        print(f"Error: Test settings file not found: {TEST_SETTINGS}")
        return False
    
    # Run the main application (it should migrate the settings)
    print("Running the application to migrate settings...")
    os.system("python main.py")
    
    # Check if migration worked
    try:
        with open(ORIGINAL_SETTINGS, 'r') as f:
            new_settings = json.load(f)
            print(f"New settings: {json.dumps(new_settings, indent=2)}")
        
        # Verify migration
        if 'start_time_stagger' in new_settings and not 'pause_time' in new_settings:
            print("SUCCESS: 'pause_time' was correctly migrated to 'start_time_stagger'")
            if new_settings.get('start_time_stagger') == 2.0:
                print("SUCCESS: The value was preserved correctly")
            else:
                print(f"FAILURE: Value not preserved. Expected 2.0 but got {new_settings.get('start_time_stagger')}")
                return False
            
            if 'global_cooldown' in new_settings:
                print("SUCCESS: Missing 'global_cooldown' field was added")
            else:
                print("FAILURE: 'global_cooldown' field was not added")
                return False
            
            return True
        else:
            print("FAILURE: Migration did not occur correctly")
            if 'pause_time' in new_settings:
                print("  - 'pause_time' still exists in the settings file")
            if 'start_time_stagger' not in new_settings:
                print("  - 'start_time_stagger' was not added to the settings file")
            return False
    except Exception as e:
        print(f"Error checking migration: {e}")
        return False

def main():
    """Main test function."""
    try:
        backup_original_settings()
        create_test_settings()
        success = run_test()
        
        print("\nTest result:", "PASSED" if success else "FAILED")
        return 0 if success else 1
    finally:
        # Clean up
        restore_original_settings()
        if os.path.exists(TEST_SETTINGS):
            os.remove(TEST_SETTINGS)
            print(f"Removed test file: {TEST_SETTINGS}")

if __name__ == "__main__":
    sys.exit(main()) 