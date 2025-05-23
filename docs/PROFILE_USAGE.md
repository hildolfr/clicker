# Clicker Profile Management Guide

The Clicker application now supports configuration profiles, allowing you to save, load, and switch between different configurations for different use cases.

## What are Profiles?

Profiles are saved configurations that include:
- All keystroke definitions
- Application settings (timing, indicators, etc.)
- Metadata (author, description, tags, timestamps)

This allows you to easily switch between different setups, such as:
- Gaming profiles with specific key combinations
- Work profiles with productivity shortcuts
- Testing profiles for different configurations

## Using the Profile CLI

The profile management is handled through a command-line interface. You can run it using:

```bash
python -m clicker.cli.profile_manager [command]
```

### Available Commands

#### List All Profiles
```bash
python -m clicker.cli.profile_manager list
```
Shows all available profiles with their metadata.

#### Create a New Profile
```bash
# Create a basic profile from current configuration
python -m clicker.cli.profile_manager create "My Gaming Setup"

# Create with description and metadata
python -m clicker.cli.profile_manager create "Work Profile" \
    -d "Productivity shortcuts for office work" \
    -a "John Doe" \
    -t "work,productivity,office"
```

#### Load a Profile
```bash
python -m clicker.cli.profile_manager load "My Gaming Setup"
```
This will:
1. Backup your current configuration
2. Load the profile's settings and keystrokes
3. Save them as your active configuration

**Note:** Restart the Clicker application after loading a profile to apply the changes.

#### Show Profile Details
```bash
python -m clicker.cli.profile_manager show "My Gaming Setup"
```
Displays detailed information about a profile including settings and keystrokes.

#### Delete a Profile
```bash
# Delete with confirmation
python -m clicker.cli.profile_manager delete "Old Profile"

# Force delete without confirmation
python -m clicker.cli.profile_manager delete "Old Profile" -f
```

#### Export a Profile
```bash
python -m clicker.cli.profile_manager export "My Gaming Setup" gaming_setup.json
```
Exports a profile to a JSON file for sharing or backup.

#### Import a Profile
```bash
# Import with original name
python -m clicker.cli.profile_manager import gaming_setup.json

# Import with a new name
python -m clicker.cli.profile_manager import gaming_setup.json -n "Imported Gaming Profile"
```

## Profile File Structure

Profiles are stored in the `profiles/` directory as JSON files. Each profile contains:

```json
{
    "name": "My Gaming Setup",
    "description": "MMO gaming configuration",
    "author": "John Doe",
    "version": "1.0",
    "tags": ["gaming", "mmo"],
    "created_at": "2025-05-22T18:30:00Z",
    "modified_at": "2025-05-22T18:30:00Z",
    "settings": {
        "toggle_key": "~",
        "global_cooldown": 1.5,
        "indicator_type": "gdi",
        // ... all other settings
    },
    "keystrokes": [
        "1 2.0 Cast spell 1",
        "2 1.5 Cast spell 2",
        // ... keystroke definitions
    ]
}
```

## Workflow Examples

### Creating a Gaming Profile
1. Configure your keystrokes and settings for gaming
2. Test the configuration to make sure it works
3. Create a profile: `python -m clicker.cli.profile_manager create "Gaming Setup" -d "For MMO gaming" -t "gaming,mmo"`

### Switching Between Work and Gaming
1. Load work profile: `python -m clicker.cli.profile_manager load "Work Profile"`
2. Restart Clicker application
3. Use work configuration...
4. Later, load gaming profile: `python -m clicker.cli.profile_manager load "Gaming Setup"`
5. Restart Clicker application

### Sharing Profiles
1. Export your profile: `python -m clicker.cli.profile_manager export "My Setup" my_setup.json`
2. Share the JSON file with others
3. They can import it: `python -m clicker.cli.profile_manager import my_setup.json`

## Best Practices

1. **Name Profiles Clearly**: Use descriptive names like "MMO Gaming", "Office Work", "Development Setup"

2. **Add Descriptions**: Include descriptions to help remember what each profile is for

3. **Use Tags**: Tag profiles for easy organization ("gaming", "work", "testing")

4. **Regular Backups**: Export important profiles for backup

5. **Test Before Saving**: Always test your configuration before saving it as a profile

6. **Version Control**: Keep track of profile versions if you make frequent changes

## Security Notes

- Profile files are validated for security when loaded
- Filename sanitization prevents directory traversal attacks
- File size limits prevent DoS attacks
- Invalid configurations are rejected with detailed error messages

## Troubleshooting

**Profile not found**: Use `list` command to see available profiles

**Import failed**: Check that the JSON file is valid and not corrupted

**Load failed**: Ensure the profile contains valid configuration data

**Permission errors**: Make sure you have write permissions to the configuration directory

For more help, check the application logs or run commands with verbose output.

## Integration with Main Application

The profile system is fully integrated with the main Clicker application:
- Configuration changes are automatically detected
- Backup files are created before profile switches  
- All validation and security checks are applied
- Progress feedback is provided for long operations

The CLI is designed to be user-friendly while providing powerful profile management capabilities for advanced users. 