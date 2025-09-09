import threading
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyManager(QObject):
    hotkey_pressed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.listener = None
        self.is_running = False
        self.ctrl_pressed = False
        self.space_pressed = False
        self.hotkey_active = False
    
    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()
    
    def stop(self):
        if not self.is_running:
            return
        
        self.is_running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
    
    def _on_key_press(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.space:
                self.space_pressed = True
            
            # Check if both keys are pressed and hotkey isn't already active
            if self.ctrl_pressed and self.space_pressed and not self.hotkey_active:
                self.hotkey_active = True
                self.hotkey_pressed.emit()
                
        except AttributeError:
            # Handle special keys that might not have the expected attributes
            pass
    
    def _on_key_release(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
                if self.hotkey_active:
                    self.hotkey_active = False
                    self.hotkey_pressed.emit()  # Signal to stop recording
            elif key == keyboard.Key.space:
                self.space_pressed = False
                if self.hotkey_active:
                    self.hotkey_active = False
                    self.hotkey_pressed.emit()  # Signal to stop recording
                    
        except AttributeError:
            # Handle special keys that might not have the expected attributes
            pass