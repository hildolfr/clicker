"""
Command-line interface for profile management.

This module provides a simple CLI for managing configuration profiles,
allowing users to create, load, save, and manage profiles from the command line.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from clicker.config.manager import ConfigManager
from clicker.config.models import ProfileConfig
from clicker.utils.exceptions import ConfigurationError


class ProfileManagerCLI:
    """Command-line interface for profile management."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the profile manager CLI."""
        self.config_manager = ConfigManager(config_dir)
        
    def list_profiles(self) -> None:
        """List all available profiles."""
        try:
            self.config_manager.load()
            profiles = self.config_manager.get_profiles()
            
            if not profiles:
                print("No profiles found.")
                return
            
            print(f"Available profiles ({len(profiles)}):")
            print("-" * 40)
            
            for name, profile in profiles.items():
                print(f"Name: {name}")
                if profile.description:
                    print(f"  Description: {profile.description}")
                if profile.author:
                    print(f"  Author: {profile.author}")
                if profile.tags:
                    print(f"  Tags: {', '.join(profile.tags)}")
                print(f"  Keystrokes: {len(profile.keystrokes)}")
                print(f"  Created: {profile.created_at or 'Unknown'}")
                print(f"  Modified: {profile.modified_at or 'Unknown'}")
                print()
                
        except Exception as e:
            print(f"Error listing profiles: {e}")
            sys.exit(1)
    
    def create_profile(self, name: str, description: str = "", author: str = "", tags: Optional[str] = None) -> None:
        """Create a new profile from current configuration."""
        try:
            self.config_manager.load()
            
            # Parse tags
            tag_list = []
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Save current configuration as profile
            success = self.config_manager.save_current_as_profile(
                name=name,
                description=description,
                author=author,
                tags=tag_list
            )
            
            if success:
                print(f"Profile '{name}' created successfully.")
            else:
                print(f"Failed to create profile '{name}'.")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error creating profile: {e}")
            sys.exit(1)
    
    def load_profile(self, name: str) -> None:
        """Load a profile as the current configuration."""
        try:
            self.config_manager.load()
            
            # Check if profile exists
            if name not in self.config_manager.list_profiles():
                print(f"Profile '{name}' not found.")
                available = self.config_manager.list_profiles()
                if available:
                    print(f"Available profiles: {', '.join(available)}")
                sys.exit(1)
            
            # Load the profile
            success = self.config_manager.load_profile(name)
            
            if success:
                print(f"Profile '{name}' loaded successfully.")
                print("Configuration has been updated. Restart the application to apply changes.")
            else:
                print(f"Failed to load profile '{name}'.")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error loading profile: {e}")
            sys.exit(1)
    
    def delete_profile(self, name: str, force: bool = False) -> None:
        """Delete a profile."""
        try:
            self.config_manager.load()
            
            # Check if profile exists
            if name not in self.config_manager.list_profiles():
                print(f"Profile '{name}' not found.")
                sys.exit(1)
            
            # Confirm deletion unless forced
            if not force:
                response = input(f"Are you sure you want to delete profile '{name}'? [y/N]: ")
                if response.lower() not in ('y', 'yes'):
                    print("Deletion cancelled.")
                    return
            
            # Delete the profile
            success = self.config_manager.delete_profile(name)
            
            if success:
                print(f"Profile '{name}' deleted successfully.")
            else:
                print(f"Failed to delete profile '{name}'.")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error deleting profile: {e}")
            sys.exit(1)
    
    def show_profile(self, name: str) -> None:
        """Show detailed information about a profile."""
        try:
            self.config_manager.load()
            profile = self.config_manager.get_profile(name)
            
            if not profile:
                print(f"Profile '{name}' not found.")
                sys.exit(1)
            
            print(f"Profile: {profile.name}")
            print("=" * 50)
            print(f"Description: {profile.description or 'None'}")
            print(f"Author: {profile.author or 'Unknown'}")
            print(f"Version: {profile.version}")
            print(f"Tags: {', '.join(profile.tags) if profile.tags else 'None'}")
            print(f"Created: {profile.created_at or 'Unknown'}")
            print(f"Modified: {profile.modified_at or 'Unknown'}")
            print(f"Keystrokes: {len(profile.keystrokes)}")
            
            # Show settings summary
            settings = profile.settings
            print("\nSettings:")
            print(f"  Toggle Key: {settings.toggle_key}")
            print(f"  Global Cooldown: {settings.global_cooldown}s")
            print(f"  Start Time Stagger: {settings.start_time_stagger}s")
            print(f"  Indicator Type: {settings.indicator_type.value}")
            print(f"  Keystroke Method: {settings.keystroke_method.value}")
            print(f"  High Performance: {settings.high_performance_mode}")
            
            # Show keystrokes summary
            if profile.keystrokes:
                print(f"\nKeystrokes ({len(profile.keystrokes)}):")
                for i, ks in enumerate(profile.keystrokes[:10], 1):  # Show first 10
                    status = "✓" if ks.enabled else "✗"
                    print(f"  {status} {ks.key} - {ks.delay}s - {ks.description}")
                
                if len(profile.keystrokes) > 10:
                    print(f"  ... and {len(profile.keystrokes) - 10} more")
            
        except Exception as e:
            print(f"Error showing profile: {e}")
            sys.exit(1)
    
    def export_profile(self, name: str, output_path: str) -> None:
        """Export a profile to a file."""
        try:
            self.config_manager.load()
            
            if name not in self.config_manager.list_profiles():
                print(f"Profile '{name}' not found.")
                sys.exit(1)
            
            export_path = Path(output_path)
            success = self.config_manager.export_profile(name, export_path)
            
            if success:
                print(f"Profile '{name}' exported to {export_path}")
            else:
                print(f"Failed to export profile '{name}'.")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error exporting profile: {e}")
            sys.exit(1)
    
    def import_profile(self, input_path: str, new_name: Optional[str] = None) -> None:
        """Import a profile from a file."""
        try:
            import_path = Path(input_path)
            
            if not import_path.exists():
                print(f"File not found: {input_path}")
                sys.exit(1)
            
            self.config_manager.load()
            success = self.config_manager.import_profile(import_path, new_name)
            
            if success:
                print(f"Profile imported successfully from {import_path}")
                if new_name:
                    print(f"Imported as: {new_name}")
            else:
                print(f"Failed to import profile from {input_path}")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error importing profile: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Clicker Profile Manager - Manage configuration profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  clicker-profiles list                              # List all profiles
  clicker-profiles create "Gaming Setup"             # Create profile from current config
  clicker-profiles create "Work" -d "Office setup"   # Create with description
  clicker-profiles load "Gaming Setup"               # Load a profile
  clicker-profiles show "Gaming Setup"               # Show profile details
  clicker-profiles delete "Old Profile"              # Delete a profile
  clicker-profiles export "Gaming Setup" game.json  # Export profile
  clicker-profiles import game.json                  # Import profile
        """
    )
    
    parser.add_argument(
        '--config-dir', 
        type=Path,
        help='Configuration directory (default: current directory)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List all profiles')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new profile from current configuration')
    create_parser.add_argument('name', help='Profile name')
    create_parser.add_argument('-d', '--description', default='', help='Profile description')
    create_parser.add_argument('-a', '--author', default='', help='Profile author')
    create_parser.add_argument('-t', '--tags', help='Profile tags (comma-separated)')
    
    # Load command
    load_parser = subparsers.add_parser('load', help='Load a profile as current configuration')
    load_parser.add_argument('name', help='Profile name to load')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show detailed profile information')
    show_parser.add_argument('name', help='Profile name to show')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a profile')
    delete_parser.add_argument('name', help='Profile name to delete')
    delete_parser.add_argument('-f', '--force', action='store_true', help='Force deletion without confirmation')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export a profile to file')
    export_parser.add_argument('name', help='Profile name to export')
    export_parser.add_argument('output', help='Output file path')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import a profile from file')
    import_parser.add_argument('input', help='Input file path')
    import_parser.add_argument('-n', '--name', help='New name for imported profile')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI manager
    cli = ProfileManagerCLI(args.config_dir)
    
    # Execute command
    try:
        if args.command == 'list':
            cli.list_profiles()
        elif args.command == 'create':
            cli.create_profile(args.name, args.description, args.author, args.tags)
        elif args.command == 'load':
            cli.load_profile(args.name)
        elif args.command == 'show':
            cli.show_profile(args.name)
        elif args.command == 'delete':
            cli.delete_profile(args.name, args.force)
        elif args.command == 'export':
            cli.export_profile(args.name, args.output)
        elif args.command == 'import':
            cli.import_profile(args.input, args.name)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 