#!/usr/bin/env python3
"""
GNOME-specific icon test - try workarounds for GNOME's icon bullshit
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

def create_desktop_file():
    """Create a .desktop file for better GNOME integration"""
    desktop_content = """[Desktop Entry]
Name=DICTATOR Icon Test
Comment=Test application for GNOME icon display
Exec=python3 gnome_icon_test.py
Icon=dictator
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
"""
    
    desktop_dir = Path.home() / ".local/share/applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = desktop_dir / "dictator-test.desktop"
    desktop_file.write_text(desktop_content)
    
    print(f"✅ Created desktop file: {desktop_file}")
    return str(desktop_file)

def install_icon_to_system():
    """Install icon to system icon directory"""
    # Find our icon
    base_dir = Path(__file__).parent / "src" / "icons"
    if not base_dir.exists():
        base_dir = Path(__file__).parent / "dictator" / "src" / "icons"
    
    icon_file = base_dir / "dictator-48.png"
    if not icon_file.exists():
        icon_file = base_dir / "dictator.png"
    
    if not icon_file.exists():
        print("❌ No icon file found")
        return None
    
    # Install to user icon directory
    user_icon_dir = Path.home() / ".local/share/icons/hicolor/48x48/apps"
    user_icon_dir.mkdir(parents=True, exist_ok=True)
    
    import shutil
    target_icon = user_icon_dir / "dictator.png"
    shutil.copy2(icon_file, target_icon)
    
    print(f"✅ Installed icon: {target_icon}")
    
    # Update icon cache
    try:
        import subprocess
        result = subprocess.run(["gtk-update-icon-cache", str(Path.home() / ".local/share/icons/hicolor")], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Updated icon cache")
        else:
            print(f"⚠️ Icon cache update failed: {result.stderr}")
    except:
        print("⚠️ Could not update icon cache")
    
    return str(target_icon)

class GnomeTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GNOME Icon Test - DICTATOR")
        self.setGeometry(100, 100, 500, 400)
        
        # Try setting WM_CLASS manually (GNOME uses this for icon lookup)
        self.setWindowRole("dictator-test")
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("GNOME Icon Integration Test"))
        layout.addWidget(QLabel("This window should show the DICTATOR icon in:"))
        layout.addWidget(QLabel("• Alt+Tab switcher"))  
        layout.addWidget(QLabel("• Activities overview"))
        layout.addWidget(QLabel("• Dock (if window is focused)"))
        layout.addWidget(QLabel("• System tray (not applicable here)"))
        
        # Status
        self.status_label = QLabel("Status: Testing...")
        layout.addWidget(self.status_label)
        
        # Test buttons
        btn1 = QPushButton("Test Method 1: System Icon")
        btn1.clicked.connect(self.test_system_icon)
        layout.addWidget(btn1)
        
        btn2 = QPushButton("Test Method 2: Direct File Icon")  
        btn2.clicked.connect(self.test_file_icon)
        layout.addWidget(btn2)
        
        btn3 = QPushButton("Test Method 3: Desktop Integration")
        btn3.clicked.connect(self.test_desktop_integration)
        layout.addWidget(btn3)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def test_system_icon(self):
        """Try using system icon theme"""
        # Set icon by name (if installed to system)
        icon = QIcon.fromTheme("dictator")
        if not icon.isNull():
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)
            self.status_label.setText("✅ Using system theme icon 'dictator'")
        else:
            self.status_label.setText("❌ System theme icon 'dictator' not found")
    
    def test_file_icon(self):
        """Try direct file path"""
        base_dir = Path(__file__).parent / "src" / "icons"
        if not base_dir.exists():
            base_dir = Path(__file__).parent / "dictator" / "src" / "icons"
        
        icon_file = base_dir / "dictator-48.png"
        if icon_file.exists():
            icon = QIcon(str(icon_file))
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)
            self.status_label.setText(f"✅ Using direct file: {icon_file.name}")
        else:
            self.status_label.setText("❌ Icon file not found")
    
    def test_desktop_integration(self):
        """Try full desktop integration"""
        # Install icon to system
        install_icon_to_system()
        
        # Create desktop file
        create_desktop_file()
        
        # Use system icon
        self.test_system_icon()
        
        self.status_label.setText("✅ Full desktop integration attempted")

def main():
    # Set environment variables that might help GNOME
    os.environ['QT_QPA_PLATFORM'] = 'xcb'  # Force X11
    os.environ['QT_SCALE_FACTOR'] = '1'    # Disable scaling issues
    
    print("Starting GNOME Icon Test...")
    print("Environment setup:")
    print(f"  Desktop session: {os.environ.get('DESKTOP_SESSION', 'unknown')}")
    print(f"  XDG current desktop: {os.environ.get('XDG_CURRENT_DESKTOP', 'unknown')}")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # Set application properties
    app.setApplicationName("dictator-test")
    app.setApplicationDisplayName("DICTATOR Icon Test")
    app.setOrganizationDomain("dictator.test")
    app.setDesktopFileName("dictator-test")  # Links to .desktop file
    
    window = GnomeTestWindow()
    
    # Try loading icon initially
    window.test_file_icon()
    
    window.show()
    window.raise_()
    window.activateWindow()
    
    print("\n" + "="*60)
    print("WINDOW IS NOW VISIBLE")
    print("Check these locations for the icon:")
    print("1. Press Alt+Tab - look for DICTATOR icon")
    print("2. Press Super key - look in Activities overview")
    print("3. Check dock/panel if window is focused")
    print("="*60)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()