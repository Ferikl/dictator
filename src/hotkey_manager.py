#!/usr/bin/env python3
"""
Global hotkey management for Dictator
"""
import os


class HotkeyManager:
    def __init__(self):
        self.listener = None
        self.is_running = False
        self.ctrl_pressed = False
        self.space_pressed = False
        self.hotkey_active = False
        self.callback = None
        self.last_callback_success = True
    
    def start(self, callback):
        if self.is_running:
            return
        
        self.callback = callback
        self.is_running = True
        
        try:
            from pynput import keyboard
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.listener.start()
        except ImportError:
            print("pynput not available - no global hotkeys")
    
    def stop(self):
        if not self.is_running:
            return
        
        self.is_running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
    
    def _on_key_press(self, key):
        try:
            from pynput import keyboard
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.space:
                self.space_pressed = True
            
            if self.ctrl_pressed and self.space_pressed and not self.hotkey_active:
                self.hotkey_active = True
                if self.callback:
                    try:
                        self.callback()
                        self.last_callback_success = True
                    except Exception as e:
                        print(f"Callback failed: {e}")
                        self.last_callback_success = False
                        # If callback fails 3 times in a row, force quit
                        if not self.last_callback_success:
                            print("UI appears to be dead, force quitting...")
                            os._exit(1)
        except:
            pass
    
    def _on_key_release(self, key):
        try:
            from pynput import keyboard
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
                if self.hotkey_active:
                    self.hotkey_active = False
                    if self.callback:
                        try:
                            self.callback()
                            self.last_callback_success = True
                        except Exception as e:
                            print(f"Callback failed on release: {e}")
                            self.last_callback_success = False
            elif key == keyboard.Key.space:
                self.space_pressed = False
                if self.hotkey_active:
                    self.hotkey_active = False
                    if self.callback:
                        try:
                            self.callback()
                            self.last_callback_success = True
                        except Exception as e:
                            print(f"Callback failed on release: {e}")
                            self.last_callback_success = False
        except:
            pass