#!/usr/bin/env python3
"""
Version bumping utility for DICTATOR
"""

import sys
import re
from pathlib import Path

def bump_version(version_type="patch"):
    """
    Bump version in src/version.py
    
    Args:
        version_type: "major", "minor", or "patch" (default)
    """
    version_file = Path(__file__).parent.parent / "src" / "version.py"
    
    if not version_file.exists():
        print(f"Error: {version_file} not found")
        return False
    
    # Read current version
    content = version_file.read_text()
    version_match = re.search(r'__version__ = "(\d+)\.(\d+)\.(\d+)"', content)
    
    if not version_match:
        print("Error: Could not find version string in version.py")
        return False
    
    major, minor, patch = map(int, version_match.groups())
    
    # Bump version based on type
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Replace version in content
    new_content = re.sub(
        r'__version__ = "\d+\.\d+\.\d+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    # Write back to file
    version_file.write_text(new_content)
    
    print(f"✅ Version bumped to {new_version}")
    return new_version

if __name__ == "__main__":
    version_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    
    if version_type not in ["major", "minor", "patch"]:
        print("Usage: python bump_version.py [major|minor|patch]")
        print("Default is 'patch'")
        sys.exit(1)
    
    new_version = bump_version(version_type)
    if new_version:
        print(f"New version: {new_version}")
        print("Run 'uv build' to build with new version")