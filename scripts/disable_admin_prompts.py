#!/usr/bin/env python3
"""
Disable Admin Prompts - Clicker Configuration Utility

This script helps users disable the admin privilege prompts that can make
the app appear to "crash" on first run.
"""

import json
import sys
from pathlib import Path


def disable_admin_prompts():
    """Disable admin privilege prompts in Clicker settings."""
    settings_file = Path("settings.json")
    
    print("Clicker - Disable Admin Prompts Utility")
    print("=" * 40)
    
    # Check if settings file exists
    if not settings_file.exists():
        print("❌ Error: settings.json not found!")
        print("   Please run Clicker at least once to create the settings file.")
        return False
    
    try:
        # Load current settings
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Show current status
        current_value = settings.get('prompt_for_admin_privileges', True)
        print(f"Current setting: prompt_for_admin_privileges = {current_value}")
        
        if not current_value:
            print("✅ Admin prompts are already disabled!")
            return True
        
        # Confirm change
        print("\nThis will disable the admin privilege dialog that appears on startup.")
        print("Pros: App won't appear to 'crash' when requesting admin privileges")
        print("Cons: Keystrokes may not work with elevated applications")
        
        response = input("\nDisable admin prompts? (y/N): ").strip().lower()
        
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            return False
        
        # Update setting
        settings['prompt_for_admin_privileges'] = False
        
        # Save settings
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, sort_keys=True)
        
        print("✅ Admin prompts disabled successfully!")
        print("   Clicker will no longer show admin privilege dialogs on startup.")
        print("   To re-enable, set 'prompt_for_admin_privileges': true in settings.json")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in settings.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def enable_admin_prompts():
    """Enable admin privilege prompts in Clicker settings."""
    settings_file = Path("settings.json")
    
    if not settings_file.exists():
        print("❌ Error: settings.json not found!")
        return False
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        settings['prompt_for_admin_privileges'] = True
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, sort_keys=True)
        
        print("✅ Admin prompts enabled successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--enable":
            enable_admin_prompts()
        elif sys.argv[1] == "--disable":
            disable_admin_prompts()
        else:
            print("Usage: python disable_admin_prompts.py [--disable | --enable]")
    else:
        disable_admin_prompts()


if __name__ == "__main__":
    main() 