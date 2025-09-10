#!/usr/bin/env python3
"""
Simple icon test for GNOME - figure out what the fuck works
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

class IconTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICON TEST - DICTATOR")
        self.setGeometry(100, 100, 400, 300)
        
        # Try different window flags
        self.test_flags = [
            Qt.WindowType.Window,
            Qt.WindowType.Tool,
            Qt.WindowType.Dialog,
        ]
        self.current_flag_index = 0
        
        self.setup_ui()
        self.try_load_icons()
    
    def setup_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Testing icon loading...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Button to cycle through window types
        self.flag_button = QPushButton("Current: Window type")
        self.flag_button.clicked.connect(self.cycle_window_flags)
        layout.addWidget(self.flag_button)
        
        # Button to reload icons
        reload_button = QPushButton("Reload Icons")
        reload_button.clicked.connect(self.try_load_icons)
        layout.addWidget(reload_button)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def cycle_window_flags(self):
        """Cycle through different window flag types"""
        self.current_flag_index = (self.current_flag_index + 1) % len(self.test_flags)
        flag = self.test_flags[self.current_flag_index]
        
        # Get current position and size
        pos = self.pos()
        size = self.size()
        
        self.setWindowFlags(flag)
        
        # Restore position and size, then show
        self.resize(size)
        self.move(pos)
        self.show()
        
        flag_names = ["Window", "Tool", "Dialog"]
        self.flag_button.setText(f"Current: {flag_names[self.current_flag_index]}")
        self.update_status(f"Changed to window type: {flag_names[self.current_flag_index]}")
    
    def try_load_icons(self):
        """Try loading icons with different methods"""
        status_text = "Icon loading attempts:\n\n"
        
        # Find icon files
        base_dir = Path(__file__).parent / "src" / "icons"
        if not base_dir.exists():
            base_dir = Path(__file__).parent / "dictator" / "src" / "icons"
        
        icon_files = []
        if base_dir.exists():
            for icon_file in base_dir.glob("dictator*.png"):
                icon_files.append(str(icon_file))
        
        status_text += f"Found {len(icon_files)} icon files:\n"
        for f in icon_files[:3]:  # Show first 3
            status_text += f"  {Path(f).name}\n"
        
        if not icon_files:
            status_text += "❌ NO ICON FILES FOUND!\n"
            self.update_status(status_text)
            return
        
        # Method 1: Single icon file
        single_icon = QIcon(icon_files[0])
        if not single_icon.isNull():
            self.setWindowIcon(single_icon)
            QApplication.instance().setWindowIcon(single_icon)
            status_text += f"✅ Method 1: Single icon loaded ({Path(icon_files[0]).name})\n"
        else:
            status_text += "❌ Method 1: Single icon FAILED\n"
        
        # Method 2: Multi-size icon
        multi_icon = QIcon()
        sizes_added = 0
        for icon_file in icon_files:
            filename = Path(icon_file).name
            if '-' in filename:
                try:
                    size_str = filename.split('-')[1].split('.')[0]
                    if size_str.isdigit():
                        size = int(size_str)
                        multi_icon.addFile(icon_file, QSize(size, size))
                        sizes_added += 1
                except:
                    multi_icon.addFile(icon_file)
                    sizes_added += 1
            else:
                multi_icon.addFile(icon_file)
                sizes_added += 1
        
        if sizes_added > 0:
            self.setWindowIcon(multi_icon)
            QApplication.instance().setWindowIcon(multi_icon)
            status_text += f"✅ Method 2: Multi-size icon with {sizes_added} sizes\n"
        else:
            status_text += "❌ Method 2: Multi-size icon FAILED\n"
        
        # Method 3: Set application metadata
        try:
            app = QApplication.instance()
            app.setApplicationName("DICTATOR_TEST")
            app.setApplicationDisplayName("DICTATOR Icon Test")
            app.setOrganizationName("TEST")
            status_text += "✅ Method 3: App metadata set\n"
        except Exception as e:
            status_text += f"❌ Method 3: App metadata FAILED: {e}\n"
        
        # Method 4: Check what Qt thinks about the icon
        current_icon = self.windowIcon()
        app_icon = QApplication.instance().windowIcon()
        
        status_text += f"\nIcon status check:\n"
        status_text += f"  Window icon null: {current_icon.isNull()}\n"
        status_text += f"  App icon null: {app_icon.isNull()}\n"
        
        if not current_icon.isNull():
            sizes = current_icon.availableSizes()
            status_text += f"  Available sizes: {[f'{s.width()}x{s.height()}' for s in sizes]}\n"
        
        self.update_status(status_text)
    
    def update_status(self, text):
        self.status_label.setText(text)
        print("=" * 50)
        print(text)
        print("=" * 50)

def main():
    print("Starting GNOME Icon Test...")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # Set some basic app properties
    app.setApplicationName("DICTATOR_ICON_TEST")
    app.setApplicationDisplayName("DICTATOR Icon Test")
    
    window = IconTestWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    
    print("Window should be visible now.")
    print("Check if icon appears in:")
    print("1. Window title bar (if any)")
    print("2. Alt+Tab switcher")
    print("3. Activities overview") 
    print("4. Dock/panel")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()