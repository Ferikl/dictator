#!/usr/bin/env python3
"""
Desktop integration utilities for Dictator
"""
import os
import shutil
import subprocess
from pathlib import Path


def install_desktop_files():
    """Install desktop entry files for GNOME/KDE menu integration"""
    try:
        # Get user directories
        home = Path.home()
        
        # Desktop entry directory
        applications_dir = home / ".local" / "share" / "applications"
        applications_dir.mkdir(parents=True, exist_ok=True)
        
        # Icons directory
        icons_dir = home / ".local" / "share" / "pixmaps"
        icons_dir.mkdir(parents=True, exist_ok=True)
        
        # Find package installation directory
        import dictator_main
        package_dir = Path(dictator_main.__file__).parent.parent
        desktop_dir = package_dir / "desktop"
        
        # Copy desktop entry
        desktop_file = desktop_dir / "dictator.desktop"
        if desktop_file.exists():
            target_desktop = applications_dir / "dictator.desktop"
            shutil.copy2(desktop_file, target_desktop)
            target_desktop.chmod(0o755)
            print(f"✅ Desktop entry installed: {target_desktop}")
        
        # Copy icon if it exists
        icon_file = desktop_dir / "dictator.png"
        if icon_file.exists():
            target_icon = icons_dir / "dictator.png"
            shutil.copy2(icon_file, target_icon)
            print(f"✅ Icon installed: {target_icon}")
        
        # Update desktop database
        try:
            subprocess.run(["update-desktop-database", str(applications_dir)], 
                         check=False, capture_output=True)
            print("✅ Desktop database updated")
        except (FileNotFoundError, subprocess.SubprocessError):
            print("⚠️ Could not update desktop database (update-desktop-database not found)")
        
        return True
        
    except Exception as e:
        print(f"❌ Desktop integration failed: {e}")
        return False


def uninstall_desktop_files():
    """Remove desktop entry files"""
    try:
        home = Path.home()
        
        # Remove desktop entry
        desktop_file = home / ".local" / "share" / "applications" / "dictator.desktop"
        if desktop_file.exists():
            desktop_file.unlink()
            print(f"✅ Desktop entry removed: {desktop_file}")
        
        # Remove icon
        icon_file = home / ".local" / "share" / "pixmaps" / "dictator.png"
        if icon_file.exists():
            icon_file.unlink()
            print(f"✅ Icon removed: {icon_file}")
        
        # Update desktop database
        try:
            applications_dir = home / ".local" / "share" / "applications"
            subprocess.run(["update-desktop-database", str(applications_dir)], 
                         check=False, capture_output=True)
            print("✅ Desktop database updated")
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Desktop uninstall failed: {e}")
        return False


if __name__ == "__main__":
    # Called during pip install
    install_desktop_files()