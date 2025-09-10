#!/usr/bin/env python3
"""
Build script for DICTATOR releases
"""

import sys
import subprocess
import shutil
from pathlib import Path

def build_release(version_type="patch", clean=True):
    """
    Build a release with version bump
    
    Args:
        version_type: "major", "minor", or "patch" (default)
        clean: Clean dist folder first (default True)
    """
    project_root = Path(__file__).parent.parent
    
    print(f"🚀 Building DICTATOR release (bump: {version_type})")
    
    # Change to project directory
    import os
    os.chdir(project_root)
    
    # Clean dist folder if requested
    if clean:
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            print("🧹 Cleaning dist folder...")
            shutil.rmtree(dist_dir)
    
    # Bump version
    print(f"📈 Bumping {version_type} version...")
    result = subprocess.run([
        sys.executable, "scripts/bump_version.py", version_type
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Version bump failed: {result.stderr}")
        return False
    
    print(result.stdout.strip())
    
    # Build package
    print("🔨 Building package...")
    result = subprocess.run(["uv", "build"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        return False
    
    print(result.stdout.strip())
    
    # List built files
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        print("\n📦 Built packages:")
        for file in dist_dir.glob("*"):
            print(f"  - {file.name}")
    
    print("\n✅ Release build complete!")
    print("\nNext steps:")
    print("1. Test the package: pip install dist/the_dictator-*.whl")
    print("2. Upload to PyPI: twine upload dist/*")
    
    return True

if __name__ == "__main__":
    version_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    clean = "--no-clean" not in sys.argv
    
    if version_type not in ["major", "minor", "patch"]:
        print("Usage: python build_release.py [major|minor|patch] [--no-clean]")
        print("Default is 'patch'")
        sys.exit(1)
    
    success = build_release(version_type, clean)
    sys.exit(0 if success else 1)