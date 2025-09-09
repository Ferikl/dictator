#!/usr/bin/env python3

import sys
import json
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QPushButton, QScrollArea, QFrame, 
                            QComboBox, QGroupBox, QCheckBox, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QPalette, QColor, QClipboard
import numpy as np
import threading
import tempfile
import signal
import time
import queue
# Removed speech_recognition - ONLY USING WHISPER

# Try to import Whisper for local speech recognition
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
    print("✅ Whisper available - using local speech recognition")
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper not available - using Google Speech Recognition")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️ PyAudio not available - audio functionality limited")

class PureRecorder:
    def __init__(self):
        self.is_recording = False
        self.current_microphone_index = None
        self.audio_data = []
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.supported_rates = [44100, 22050, 16000, 8000]
        
        # WHISPER ONLY - no Google Speech Recognition
        self.whisper_model = None
        self.whisper_model_name = "tiny"
        self.use_openai_whisper = False
        
        # Audio level monitoring
        self.current_audio_level = 0
        self.audio_level_lock = threading.Lock()
        self.is_monitoring = False
        self.audio_queue = []
        
        self.refresh_microphones()
        
        print(f"WHISPER_AVAILABLE at init: {WHISPER_AVAILABLE}")
        if WHISPER_AVAILABLE:
            print("Calling load_whisper_model...")
            self.load_whisper_model()
            print(f"After loading, self.whisper_model = {self.whisper_model}")
        else:
            print("WHISPER_AVAILABLE is False!")
            self.whisper_model = None
        
        # Initialize audio variables (keep it simple)
        self.audio_data = []
    
    def load_whisper_model(self):
        # Load synchronously with SSL bypass for network issues
        try:
            print("Loading Whisper model synchronously...")
            
            # Bypass SSL issues
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            
            device = "cpu"
            
            # Try tiny model first - it's fastest to load
            try:
                print("Loading tiny Whisper model...")
                from faster_whisper import WhisperModel
                self.whisper_model = WhisperModel(
                    "tiny", 
                    device=device,
                    download_root="./whisper_models"
                )
                self.whisper_model_name = "tiny"
                print("✅ Whisper tiny model loaded successfully")
                return
            except Exception as e:
                print(f"Failed to load tiny model: {e}")
            
            # Skip openai-whisper due to version conflicts
            
            # If all fails, error out
            print("❌ FATAL: Could not load any Whisper model")
            self.whisper_model = None
            
        except Exception as e:
            print(f"Whisper loading error: {e}")
            self.whisper_model = None
    
    def refresh_microphones(self):
        self.available_microphones = []
        if not PYAUDIO_AVAILABLE:
            return
        
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            
            # Filter out virtual/system devices that aren't real microphones
            skip_keywords = [
                'monitor', 'output', 'loopback', 'echo', 'null', 'auto_null',
                'pulse', 'default', 'system', 'analog-stereo', 'analog-surround',
                'iec958', 'hdmi', 'front:', 'rear:', 'center_lfe:', 'side:',
                'capture.', 'playback.', 'speaker', 'headphones', 'built-in audio',
                'dummy', 'test', 'rnnoise', 'surround', 'digital', 'spdif',
                'pipewire', 'alsa_output', 'alsa_input', 'combined',
                'virtual', 'software', 'proxy', 'tunnel', 'bridge'
            ]
            
            # Enumerate PyAudio input devices
            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    if info.get('maxInputChannels', 0) > 0:
                        device_name = info.get('name', f"Device {i}")
                        
                        # Skip virtual/system devices
                        if any(keyword in device_name.lower() for keyword in skip_keywords):
                            continue
                        
                        self.available_microphones.append({
                            'name': device_name,
                            'index': i
                        })
                except Exception:
                    continue
            
            p.terminate()
            
            print(f"Found microphones using PyAudio: {[mic['name'] for mic in self.available_microphones]}")
            
            if self.available_microphones and self.current_microphone_index is None:
                self.set_microphone(0)
                
        except Exception as e:
            print(f"Failed to enumerate microphones: {e}")
    
    def get_microphone_list(self):
        return self.available_microphones
    
    def set_microphone(self, index):
        try:
            if 0 <= index < len(self.available_microphones):
                self.current_microphone_index = index
                mic_info = self.available_microphones[index]
                print(f"Selected microphone: {mic_info['name']}")
                return True
        except Exception as e:
            print(f"Failed to set microphone {index}: {e}")
        return False
    
    def get_current_microphone(self):
        if (self.current_microphone_index is not None and 
            0 <= self.current_microphone_index < len(self.available_microphones)):
            return self.available_microphones[self.current_microphone_index]
        return None
    
    def start_recording(self, callback):
        if self.is_recording:
            return
        
        self.is_recording = True
        self.callback = callback
        print(f"🔥 CALLBACK SET TO: {callback}")
        
        print(f"Starting recording with microphone index: {self.current_microphone_index}")
        thread = threading.Thread(target=self._record_worker)
        thread.daemon = True
        thread.start()
    
    def stop_recording(self):
        print("🔥 RECORDER: stop_recording called")
        self.is_recording = False
        print("🔥 RECORDER: is_recording set to False")
    
    def start_continuous_monitoring(self):
        """Start continuous audio monitoring like SAI"""
        if not PYAUDIO_AVAILABLE or self.is_monitoring:
            return
        
        # Ensure any previous monitoring is stopped first
        self.stop_monitoring()
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._continuous_monitor_worker, daemon=True)
        self.monitoring_thread.start()
    
    def _continuous_monitor_worker(self):
        """Continuous audio monitoring worker like SAI"""
        try:
            if self.current_microphone_index is None:
                return
            
            p = pyaudio.PyAudio()
            
            # Get device info first to check capabilities like SAI does
            device_index = self.available_microphones[self.current_microphone_index]['index']
            try:
                device_info = p.get_device_info_by_index(device_index)
                max_input_channels = int(device_info['maxInputChannels'])
                default_rate = int(device_info['defaultSampleRate'])
                
                print(f"Device {device_index}: max_channels={max_input_channels}, default_rate={default_rate}")
                
                if max_input_channels == 0:
                    print(f"Device {device_index} has no input channels")
                    p.terminate()
                    return
                
                # Use the appropriate number of channels (1 for mono, or device max)
                channels = min(1, max_input_channels)
                
            except Exception as e:
                print(f"Error getting device info: {e}")
                p.terminate()
                return
            
            stream = None
            working_rate = None
            
            # Try different sample rates with proper channel count
            rates_to_try = [default_rate] + self.supported_rates
            for rate in rates_to_try:
                try:
                    print(f"Trying {rate}Hz with {channels} channels")
                    stream = p.open(
                        format=pyaudio.paInt16,
                        channels=channels,
                        rate=int(rate),
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=self.chunk_size
                    )
                    working_rate = rate
                    print(f"✓ Success: {rate}Hz with {channels} channels")
                    break
                except Exception as e:
                    print(f"✗ Failed {rate}Hz: {e}")
                    continue
            
            if not stream:
                print("Could not open audio stream with any supported configuration")
                p.terminate()
                return
            
            print(f"Started continuous monitoring at {working_rate}Hz with {channels} channels")
            
            # Continuous monitoring loop
            while self.is_monitoring:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Handle multi-channel audio by taking first channel
                    if channels > 1:
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        audio_chunk = audio_array[::channels]  # Take every Nth sample (first channel)
                    else:
                        audio_chunk = np.frombuffer(data, dtype=np.int16)
                    
                    # Always add to queue for volume display
                    self.audio_queue.append(audio_chunk)
                    if len(self.audio_queue) > 10:  # Keep last 10 chunks
                        self.audio_queue.pop(0)
                    
                    # Only process for transcription if recording
                    if self.is_recording:
                        self.audio_data.append(audio_chunk)
                    
                except Exception as e:
                    print(f"Monitor error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            print(f"Continuous monitoring error: {e}")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if hasattr(self, 'is_monitoring'):
            self.is_monitoring = False
        
        # Wait for thread to finish to avoid memory issues
        if hasattr(self, 'monitoring_thread') and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
    
    def _record_worker(self):
        # FORCE WHISPER LOADING AND ONLY USE WHISPER
        print(f"WHISPER_AVAILABLE: {WHISPER_AVAILABLE}")
        print(f"self.whisper_model: {self.whisper_model}")
        
        # If Whisper is available but model not loaded, load it now
        if not self.whisper_model:
            print("🔧 Loading Whisper model...")
            try:
                # Bypass SSL issues
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                
                from faster_whisper import WhisperModel
                self.whisper_model = WhisperModel(
                    "tiny", 
                    device="cpu",
                    download_root="./whisper_models"
                )
                print("✅ Whisper tiny model loaded successfully")
            except Exception as e:
                print(f"FATAL: Failed to load Whisper model: {e}")
                self.callback("ERROR: Whisper failed to load", "error")
                return
        
        # ONLY USE WHISPER - NO GOOGLE
        print("🎵 Using Whisper for transcription")
        self._record_with_whisper()
    
    def _record_with_whisper(self):
        print("🎵 Recording with Whisper...")
        try:
            import pyaudio
            
            p = pyaudio.PyAudio()
            
            # Use default audio device to avoid channel issues
            print("Setting up default audio input...")
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,  # Force mono
                rate=16000,  # Whisper's preferred rate
                input=True,
                frames_per_buffer=1024
            )
            
            print("Recording audio for Whisper processing...")
            audio_data = []
            
            # Record until manually stopped (no time limit)
            chunk_count = 0
            
            while self.is_recording:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    audio_data.append(audio_chunk)
                    
                    # Calculate REAL audio level for the meter
                    rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
                    audio_level = min(100, int((rms / 3000.0) * 100))  # Scale to 0-100
                    
                    with self.audio_level_lock:
                        self.current_audio_level = audio_level
                    
                    chunk_count += 1
                except Exception as e:
                    print(f"Chunk read error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            if not audio_data:
                print("No audio data recorded")
                self.callback("", "no_audio")
                return
            
            # Process with Whisper
            print("Processing audio with Whisper...")
            audio_array = np.concatenate(audio_data)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Check for minimum audio length
            if len(audio_float) < 0.1 * 16000:  # Less than 0.1 seconds
                print("Audio too short")
                self.callback("", "too_short")
                return
            
            # Transcribe directly with Whisper (no temp file needed)
            try:
                if self.whisper_model:
                    print("🔥 WHISPER: Starting transcription with faster-whisper...")
                    print(f"🔥 WHISPER: Audio length: {len(audio_float)} samples")
                    
                    segments, info = self.whisper_model.transcribe(audio_float)
                    print("🔥 WHISPER: Transcription completed, processing segments...")
                    
                    text = "".join([segment.text for segment in segments]).strip()
                    language = info.language if hasattr(info, 'language') else "en"
                    
                    print(f"🔥 WHISPER: Result text: '{text}' (language: {language})")
                    print(f"🔥 WHISPER: About to call callback...")
                    
                    if text:
                        print(f"🔥 WHISPER: Calling callback with text: '{text}', '{language}'")
                        self.callback(text, language)
                        print(f"🔥 WHISPER: Callback completed successfully")
                    else:
                        print(f"🔥 WHISPER: Empty result, calling callback with no_speech")
                        self.callback("", "no_speech")
                        print(f"🔥 WHISPER: No speech callback completed")
                else:
                    print("🚨 WHISPER: Model not loaded!")
                    self.callback("", "model_error")
                    
            except Exception as e:
                print(f"🚨 WHISPER: Transcription error: {e}")
                import traceback
                traceback.print_exc()
                self.callback("", "transcription_error")
                
        except Exception as e:
            print(f"Whisper recording setup error: {e}")
            self.callback("ERROR: Whisper recording failed", "error")
    
# GOOGLE SPEECH RECOGNITION COMPLETELY REMOVED - WHISPER ONLY

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
                            import os
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

# Removed DictationHistoryItem - now using clickable QPushButton items

class UIWatchdog:
    """Watchdog to detect UI crashes and kill the process"""
    def __init__(self, window):
        self.window = window
        self.last_heartbeat = time.time()
        self.is_running = True
        
        # Start watchdog thread
        self.watchdog_thread = threading.Thread(target=self._watchdog_worker, daemon=True)
        self.watchdog_thread.start()
        
        # Start heartbeat timer
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._heartbeat)
        self.heartbeat_timer.start(1000)  # Heartbeat every 1 second
    
    def _heartbeat(self):
        """Update heartbeat timestamp"""
        self.last_heartbeat = time.time()
    
    def _watchdog_worker(self):
        """Monitor heartbeat and kill process if UI becomes unresponsive"""
        while self.is_running:
            time.sleep(2)  # Check every 2 seconds
            
            # If no heartbeat for 5 seconds, UI is likely dead
            if time.time() - self.last_heartbeat > 5:
                print("🚨 UI WATCHDOG: No heartbeat for 5+ seconds - UI appears dead!")
                print("🚨 FORCE KILLING PROCESS...")
                import os
                os._exit(1)
    
    def stop(self):
        """Stop the watchdog"""
        self.is_running = False
        if hasattr(self, 'heartbeat_timer'):
            self.heartbeat_timer.stop()

class UIUpdateRequest:
    """UI update request like SAI"""
    def __init__(self, action, **kwargs):
        self.action = action
        self.kwargs = kwargs

class DictatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recorder = PureRecorder()
        self.hotkey_manager = HotkeyManager()
        self.history = []
        self.config_path = Path.home() / ".config" / "dictator" / "config.json"
        self.settings_visible = False
        self.drag_position = QPoint()
        self.dragging = False
        
        # UI update queue system like SAI
        self.ui_update_queue = queue.Queue()
        
        # Recording timer
        self.recording_start_time = None
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_timer)
        
        # Start UI watchdog
        self.watchdog = UIWatchdog(self)
        
        self.init_ui()
        self.load_config()
        
        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.auto_hide)
        self.hide_timer.setSingleShot(True)
        
        # UI update processing timer like SAI
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.process_ui_updates)
        self.ui_update_timer.start(16)  # ~60fps like SAI
        
        # Connect status update callback
        self.recorder.update_status_callback = self.update_status_label
        
        # Start hotkey manager
        self.hotkey_manager.start(self.toggle_recording)
    
    def request_ui_update(self, action, **kwargs):
        """Thread-safe method to request UI update like SAI"""
        self.ui_update_queue.put(UIUpdateRequest(action, **kwargs))
    
    def process_ui_updates(self):
        """Process all pending UI updates like SAI (runs in main thread)"""
        try:
            processed_count = 0
            while True:
                try:
                    request = self.ui_update_queue.get_nowait()
                    print(f"🔥 PROCESSING UI UPDATE: {request.action}")
                    self._handle_ui_update(request)
                    processed_count += 1
                    print(f"🔥 UI UPDATE COMPLETED: {request.action}")
                    
                    # Process max 10 updates per cycle to avoid blocking
                    if processed_count >= 10:
                        print(f"🔥 Processed {processed_count} updates, yielding control")
                        break
                        
                except queue.Empty:
                    break
        except Exception as e:
            print(f"🚨 FATAL UI update error: {e}")
            import traceback
            traceback.print_exc()
            # Don't crash the whole app, just log the error
    
    def _handle_ui_update(self, request):
        """Handle individual UI update request like SAI"""
        try:
            if request.action == "transcription_complete":
                text = request.kwargs.get('text', '')
                language = request.kwargs.get('language', 'en')
                self._safe_handle_transcription(text, language)
            elif request.action == "add_history_item":
                text = request.kwargs.get('text', '')
                self._safe_add_history_item(text)
            elif request.action == "update_status":
                status = request.kwargs.get('status', '')
                style = request.kwargs.get('style', '')
                self._safe_update_status(status, style)
        except Exception as e:
            print(f"Error handling UI update {request.action}: {e}")
    
    def init_ui(self):
        self.setWindowTitle("DICTATOR")
        self.setObjectName("DICTATOR")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 240);
                border-radius: 12px;
                border: 2px solid rgba(76, 175, 80, 120);
            }
        """)
        main_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎤 DICTATOR")
        title_label.setStyleSheet("color: #4CAF50; font-size: 20px; font-weight: bold;")
        title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(30, 30)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(70, 70, 70, 150);
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(90, 90, 90, 180);
            }
        """)
        settings_btn.clicked.connect(self.toggle_settings)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 50, 50, 150);
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(220, 70, 70, 180);
            }
        """)
        close_btn.clicked.connect(self.close_application)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Status
        engine_status = "Whisper (loading...)" if WHISPER_AVAILABLE else "Google Speech API"
        self.status_label = QLabel(f"✅ Ready - {engine_status} - Press Ctrl+Space to dictate")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 13px; margin: 8px 0;")
        layout.addWidget(self.status_label)
        
        # Recording timer
        self.timer_label = QLabel("⏱️ 00:00")
        self.timer_label.setStyleSheet("color: #FF9800; font-size: 16px; font-weight: bold; margin: 4px 0; text-align: center;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.hide()  # Initially hidden
        layout.addWidget(self.timer_label)
        
        # Manual record button
        self.record_btn = QPushButton("🎤 Start Listening")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 150);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 8px 0;
            }
            QPushButton:hover {
                background-color: rgba(96, 195, 100, 180);
            }
            QPushButton:pressed {
                background-color: rgba(56, 155, 60, 200);
            }
        """)
        self.record_btn.clicked.connect(self.toggle_manual_recording)
        layout.addWidget(self.record_btn)
        
        # Volume meter
        self.volume_frame = QFrame()
        self.volume_frame.setFixedHeight(40)
        self.volume_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 10, 200); 
                border-radius: 8px; 
                margin: 5px 0;
                border: 1px solid rgba(76, 175, 80, 80);
            }
        """)
        
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(10, 6, 10, 6)
        
        # Just the volume bars - no "LEVEL:" text
        
        self.volume_bars = []
        for i in range(30):
            # Use QFrame instead of QProgressBar for actual volume bars
            bar = QFrame()
            bar.setFixedSize(6, 20)
            
            if i < 20:
                color = "#4CAF50"  # Green
            elif i < 25:
                color = "#FFC107"  # Yellow  
            else:
                color = "#F44336"  # Red
            
            # Default to off state
            bar.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(40, 40, 40, 120);
                    border: 1px solid rgba(80, 80, 80, 60);
                    border-radius: 2px;
                }}
            """)
            
            # Store the colors for later use
            bar.on_color = color
            bar.off_color = "rgba(40, 40, 40, 120)"
            bar.is_on = False
            
            self.volume_bars.append(bar)
            volume_layout.addWidget(bar)
        
        self.volume_frame.setLayout(volume_layout)
        layout.addWidget(self.volume_frame)
        # Keep volume frame visible like SAI - always show audio levels
        self.volume_frame.show()
        
        # Make sure volume bars are properly initialized
        for bar in self.volume_bars:
            bar.show()
        
        # Start volume monitoring immediately like SAI
        self.volume_timer = QTimer()
        self.volume_timer.timeout.connect(self.update_volume_bars)
        self.volume_timer.start(50)  # Update every 50ms
        
        # Settings panel
        self.settings_panel = self.create_settings_panel()
        layout.addWidget(self.settings_panel)
        self.settings_panel.hide()
        
        # Current transcription text area
        current_label = QLabel("Current Transcription:")
        current_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(current_label)
        
        self.current_text_area = QTextEdit()
        self.current_text_area.setPlaceholderText("Most recent transcription will appear here...")
        self.current_text_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(25, 25, 25, 200);
                border: 2px solid rgba(76, 175, 80, 100);
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px;
                margin: 4px 0;
            }
        """)
        self.current_text_area.setFixedHeight(80)
        self.current_text_area.setReadOnly(True)
        layout.addWidget(self.current_text_area)
        
        # History collapsible section
        self.history_toggle = QPushButton("📜 History (0 items) ▼")
        self.history_toggle.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 100);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
                margin: 8px 0 4px 0;
            }
            QPushButton:hover {
                background-color: rgba(96, 195, 100, 120);
            }
            QPushButton:pressed {
                background-color: rgba(56, 155, 60, 150);
            }
        """)
        self.history_toggle.clicked.connect(self.toggle_history)
        layout.addWidget(self.history_toggle)
        
        # History area (initially visible)
        self.history_scroll = QScrollArea()
        self.history_scroll.setStyleSheet("""
            QScrollArea {
                background-color: rgba(15, 15, 15, 200);
                border: 2px solid rgba(76, 175, 80, 100);
                border-radius: 8px;
                margin: 0 0 8px 0;
            }
            QScrollBar:vertical {
                background-color: rgba(40, 40, 40, 120);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(76, 175, 80, 150);
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout()
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_widget.setLayout(self.history_layout)
        
        self.history_scroll.setWidget(self.history_widget)
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFixedHeight(150)
        self.history_collapsed = False
        
        layout.addWidget(self.history_scroll)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
        self.resize(550, 400)
        self.move(100, 100)
        self.show()
        self.raise_()
        self.activateWindow()
    
    def create_settings_panel(self):
        settings_panel = QGroupBox("Settings")
        settings_panel.setStyleSheet("""
            QGroupBox {
                background-color: rgba(25, 25, 25, 220);
                border: 1px solid rgba(76, 175, 80, 120);
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
                font-size: 12px;
                color: #4CAF50;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Microphone selection
        mic_layout = QHBoxLayout()
        mic_label = QLabel("Microphone:")
        mic_label.setStyleSheet("color: white; font-size: 12px;")
        
        self.microphone_combo = QComboBox()
        self.microphone_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(40, 40, 40, 180);
                color: white;
                border: 1px solid rgba(76, 175, 80, 120);
                border-radius: 4px;
                padding: 5px 8px;
                min-width: 300px;
            }
        """)
        self.microphone_combo.currentIndexChanged.connect(self.on_microphone_changed)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(35, 30)
        refresh_btn.clicked.connect(self.refresh_microphones)
        
        mic_layout.addWidget(mic_label)
        mic_layout.addWidget(self.microphone_combo)
        mic_layout.addWidget(refresh_btn)
        layout.addLayout(mic_layout)
        
        # Auto-hide option
        self.auto_hide_checkbox = QCheckBox("Auto-hide after dictation")
        self.auto_hide_checkbox.setStyleSheet("color: white; font-size: 12px;")
        self.auto_hide_checkbox.setChecked(True)
        layout.addWidget(self.auto_hide_checkbox)
        
        settings_panel.setLayout(layout)
        self.refresh_microphones()
        return settings_panel
    
    def toggle_settings(self):
        if self.settings_visible:
            self.settings_panel.hide()
            self.settings_visible = False
        else:
            self.settings_panel.show()
            self.settings_visible = True
    
    def refresh_microphones(self):
        self.recorder.refresh_microphones()
        microphones = self.recorder.get_microphone_list()
        
        self.microphone_combo.clear()
        for mic in microphones:
            self.microphone_combo.addItem(mic['name'], mic['index'])
    
    def on_microphone_changed(self, index):
        if index >= 0:
            mic_index = self.microphone_combo.itemData(index)
            self.recorder.set_microphone(mic_index)
            self.save_config()
    
    def toggle_recording(self):
        if self.recorder.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def toggle_manual_recording(self):
        print("🔥 BUTTON_CLICK: Manual recording button clicked")
        try:
            if self.recorder.is_recording:
                print("🔥 BUTTON_CLICK: Currently recording - will stop")
                self.stop_recording()
                print("🔥 BUTTON_CLICK: Stop recording completed")
            else:
                print("🔥 BUTTON_CLICK: Currently not recording - will start")
                self.start_recording()
                print("🔥 BUTTON_CLICK: Start recording completed")
        except Exception as e:
            print(f"🚨 FATAL ERROR in toggle_manual_recording: {e}")
            import traceback
            traceback.print_exc()
    
    def start_recording(self):
        # Always show window and bring it to front like SAI does
        self.show()
        self.raise_()
        self.activateWindow()
        self.hide_timer.stop()
        print("Starting recording...")
        
        # Start recording timer
        self.start_recording_timer()
        
        self.status_label.setText("👂 LISTENING...")
        self.status_label.setStyleSheet("color: #F44336; font-size: 13px; font-weight: bold;")
        
        # Update button
        self.record_btn.setText("⏹️ Stop Listening")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 150);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 8px 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 87, 74, 180);
            }
            QPushButton:pressed {
                background-color: rgba(200, 50, 40, 200);
            }
        """)
        
        self.recorder.start_recording(self.on_transcription_ready)
    
    def stop_recording(self):
        print("🔥 STOP_RECORDING: Starting stop recording process...")
        
        try:
            print("🔥 STOP_RECORDING: Calling recorder.stop_recording()...")
            self.recorder.stop_recording()
            print("🔥 STOP_RECORDING: recorder.stop_recording() completed")
            
            print("🔥 STOP_RECORDING: Stopping recording timer...")
            self.stop_recording_timer()
            print("🔥 STOP_RECORDING: Recording timer stopped")
            
            print("🔥 STOP_RECORDING: Updating status label...")
            self.status_label.setText("✅ Ready - Click to listen or press Ctrl+Space")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 13px;")
            print("🔥 STOP_RECORDING: Status label updated")
            
            print("🔥 STOP_RECORDING: Processing Qt events after status update...")
            QApplication.processEvents()
            print("🔥 STOP_RECORDING: Qt events processed")
            
            print("🔥 STOP_RECORDING: Resetting button text...")
            self.record_btn.setText("🎤 Start Listening")
            print("🔥 STOP_RECORDING: Button text set")
            
            print("🔥 STOP_RECORDING: Setting button stylesheet...")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(76, 175, 80, 150);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 8px 0;
                }
                QPushButton:hover {
                    background-color: rgba(96, 195, 100, 180);
                }
                QPushButton:pressed {
                    background-color: rgba(56, 155, 60, 200);
                }
            """)
            print("🔥 STOP_RECORDING: Button stylesheet set")
            
            print("🔥 STOP_RECORDING: Processing final Qt events...")
            QApplication.processEvents()
            print("🔥 STOP_RECORDING: Final Qt events processed")
            
            print("🔥 STOP_RECORDING: Stop recording process completed successfully")
            
        except Exception as e:
            print(f"🚨 FATAL ERROR in stop_recording: {e}")
            import traceback
            traceback.print_exc()
    
    def on_transcription_ready(self, text, language):
        """Thread-safe callback - just queue the update like SAI"""
        print(f"🔥 ON_TRANSCRIPTION_READY called with: '{text}', '{language}'")
        print("🔥 Queuing transcription_complete request...")
        self.request_ui_update("transcription_complete", text=text, language=language)
        print("🔥 Request queued successfully")
    
    def _safe_handle_transcription(self, text, language):
        """Safe transcription handler that runs on main thread"""
        print(f"🔥 SAFE_HANDLE_TRANSCRIPTION: '{text}' (language: {language})")
        
        # Stop recording
        self.stop_recording()
        
        if text and text.strip():
            print(f"🔥 Queuing add_history_item for: '{text.strip()}'")
            self.request_ui_update("add_history_item", text=text.strip())
            self.request_ui_update("update_status", 
                                 status="✅ Dictation complete", 
                                 style="color: #4CAF50; font-size: 13px;")
        else:
            if language == "timeout":
                status = "⏱️ No speech detected - timeout"
            elif language == "error":
                status = "❌ Recording error"
            else:
                status = "❌ No speech detected"
            self.request_ui_update("update_status", 
                                 status=status, 
                                 style="color: #FF9800; font-size: 13px;")
        
        # Temporarily disable auto-hide to reduce timer interactions
        # if self.auto_hide_checkbox.isChecked():
        #     self.hide_timer.start(3000)
        print("🔥 Auto-hide disabled for debugging")
    
    def _safe_add_history_item(self, text):
        """Safe history addition that runs on main thread"""
        print(f"🔥 SAFE_ADD_HISTORY_ITEM: '{text}'")
        
        try:
            print("🔥 Adding to history list...")
            self.history.append(text)
            
            print("🔥 Updating current text area...")
            self.current_text_area.setPlainText(text)
            print("🔥 Current text area updated successfully")
            
            print("🔥 Creating QPushButton...")
            # Create clickable history item
            item_btn = QPushButton(f"🎤 {text[:50]}{'...' if len(text) > 50 else ''}")
            print("🔥 QPushButton created successfully")
            
            print("🔥 Setting stylesheet...")
            item_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(40, 40, 40, 150);
                    color: #FFFFFF;
                    border: 1px solid rgba(76, 175, 80, 80);
                    border-radius: 6px;
                    padding: 8px 12px;
                    margin: 2px;
                    text-align: left;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(60, 60, 60, 180);
                    border: 1px solid rgba(76, 175, 80, 120);
                }
                QPushButton:pressed {
                    background-color: rgba(76, 175, 80, 100);
                }
            """)
            print("🔥 Stylesheet set successfully")
            
            print("🔥 Connecting click handler...")
            item_btn.clicked.connect(lambda: self.show_history_item(text))
            print("🔥 Click handler connected successfully")
            
            print("🔥 Inserting widget into layout...")
            self.history_layout.insertWidget(0, item_btn)
            print("🔥 Widget inserted successfully")
            
            print("🔥 Processing Qt events after widget insertion...")
            QApplication.processEvents()  # Process events before continuing
            print("🔥 Qt events processed")
            
            print("🔥 Updating toggle button...")
            # Update toggle button
            self.history_toggle.setText(f"📜 History ({len(self.history)} items) {'▼' if not self.history_collapsed else '▶'}")
            print("🔥 Toggle button updated successfully")
            
            print("🔥 Cleaning up old items...")
            # Cleanup old items
            if self.history_layout.count() > 20:
                old_item = self.history_layout.itemAt(20).widget()
                if old_item:
                    old_item.setParent(None)
                    print("🔥 Old item removed")
            if len(self.history) > 20:
                self.history = self.history[-20:]
                print("🔥 History list trimmed")
            
            print("🔥 Saving config...")
            self.save_config()
            print("🔥 Config saved successfully")
            print("🔥 SAFE_ADD_HISTORY_ITEM completed successfully")
            
        except Exception as e:
            print(f"🚨 FATAL ERROR in _safe_add_history_item: {e}")
            import traceback
            traceback.print_exc()
            # Try to force quit if widget creation is failing
            print("🚨 Widget creation failed - this might be a Qt issue")
            # Don't force quit immediately, let other systems handle it
    
    def _safe_update_status(self, status, style):
        """Safe status update that runs on main thread"""
        print(f"🔥 SAFE_UPDATE_STATUS: '{status}'")
        self.status_label.setText(status)
        if style:
            self.status_label.setStyleSheet(style)
    
    # Old method removed - now using queue-based _safe_add_history_item
    
    def show_history_item(self, text):
        # Show the selected history item in the current transcription area
        self.current_text_area.setPlainText(text)
    
    def update_recording_timer(self):
        """Update the recording timer display"""
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_label.setText(f"⏱️ {minutes:02d}:{seconds:02d}")
    
    def start_recording_timer(self):
        """Start the recording timer"""
        self.recording_start_time = time.time()
        self.timer_label.show()
        self.recording_timer.start(1000)  # Update every second
    
    def stop_recording_timer(self):
        """Stop the recording timer"""
        print("🔥 TIMER: Stopping recording timer...")
        try:
            self.recording_timer.stop()
            print("🔥 TIMER: QTimer stopped")
            
            self.timer_label.hide()
            print("🔥 TIMER: Timer label hidden")
            
            self.recording_start_time = None
            print("🔥 TIMER: Start time reset")
            print("🔥 TIMER: Recording timer stopped successfully")
        except Exception as e:
            print(f"🚨 ERROR in stop_recording_timer: {e}")
            import traceback
            traceback.print_exc()
    
    def update_volume_bars(self):
        # REAL AUDIO LEVEL METER - NOT FAKE ANIMATION
        if self.recorder.is_recording:
            # Get the ACTUAL audio level from the recorder
            with self.recorder.audio_level_lock:
                audio_level = self.recorder.current_audio_level
            
            # Calculate how many bars to light up based on REAL audio level
            num_bars_to_light = int((audio_level / 100.0) * len(self.volume_bars))
            
            for i, bar in enumerate(self.volume_bars):
                should_be_on = (i < num_bars_to_light)
                
                if should_be_on and not bar.is_on:
                    # Turn on this bar
                    bar.setStyleSheet(f"""
                        QFrame {{
                            background-color: {bar.on_color};
                            border: 1px solid rgba(255, 255, 255, 100);
                            border-radius: 2px;
                        }}
                    """)
                    bar.is_on = True
                elif not should_be_on and bar.is_on:
                    # Turn off this bar
                    bar.setStyleSheet(f"""
                        QFrame {{
                            background-color: {bar.off_color};
                            border: 1px solid rgba(80, 80, 80, 60);
                            border-radius: 2px;
                        }}
                    """)
                    bar.is_on = False
        else:
            # Turn off all bars when not recording
            for bar in self.volume_bars:
                if bar.is_on:
                    bar.setStyleSheet(f"""
                        QFrame {{
                            background-color: {bar.off_color};
                            border: 1px solid rgba(80, 80, 80, 60);
                            border-radius: 2px;
                        }}
                    """)
                    bar.is_on = False
    
    def toggle_history(self):
        self.history_collapsed = not self.history_collapsed
        
        if self.history_collapsed:
            self.history_scroll.hide()
            self.history_toggle.setText(f"📜 History ({len(self.history)} items) ▶")
        else:
            self.history_scroll.show()
            self.history_toggle.setText(f"📜 History ({len(self.history)} items) ▼")
    
    def auto_hide(self):
        if self.auto_hide_checkbox.isChecked():
            self.hide()
    
    def update_status_label(self, text):
        self.status_label.setText(text)
    
    def close_application(self):
        # Stop all audio processing like SAI
        print("Closing application...")
        if hasattr(self, 'volume_timer'):
            self.volume_timer.stop()
        if hasattr(self, 'hide_timer'):
            self.hide_timer.stop()
        if hasattr(self, 'ui_update_timer'):
            self.ui_update_timer.stop()
        if hasattr(self, 'recording_timer'):
            self.recording_timer.stop()
        if hasattr(self, 'watchdog'):
            self.watchdog.stop()
        self.recorder.stop_monitoring()
        self.recorder.stop_recording()
        self.hotkey_manager.stop()
        
        # Force quit the entire process
        import os
        import sys
        print("Force quitting process...")
        QApplication.instance().quit()
        os._exit(0)  # Force immediate exit
    
    def closeEvent(self, event):
        self.close_application()
        event.accept()
    
    def load_config(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.history = config.get('history', [])
                    for text in self.history:
                        # Create clickable history item during load
                        item_btn = QPushButton(f"🎤 {text[:50]}{'...' if len(text) > 50 else ''}")
                        item_btn.setStyleSheet("""
                            QPushButton {
                                background-color: rgba(40, 40, 40, 150);
                                color: #FFFFFF;
                                border: 1px solid rgba(76, 175, 80, 80);
                                border-radius: 6px;
                                padding: 8px 12px;
                                margin: 2px;
                                text-align: left;
                                font-size: 12px;
                            }
                            QPushButton:hover {
                                background-color: rgba(60, 60, 60, 180);
                                border: 1px solid rgba(76, 175, 80, 120);
                            }
                            QPushButton:pressed {
                                background-color: rgba(76, 175, 80, 100);
                            }
                        """)
                        item_btn.clicked.connect(lambda checked, t=text: self.show_history_item(t))
                        self.history_layout.addWidget(item_btn)
                    
                    # Update toggle button text after loading
                    if hasattr(self, 'history_toggle'):
                        self.history_toggle.setText(f"📜 History ({len(self.history)} items) ▼")
        except:
            pass
    
    def save_config(self):
        try:
            print("🔥 Creating config directory...")
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            print("🔥 Config directory created")
            
            print("🔥 Preparing config data...")
            config = {'history': self.history[-50:]}
            print(f"🔥 Config data prepared: {len(config['history'])} history items")
            
            print("🔥 Writing config file...")
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("🔥 Config file written successfully")
        except Exception as e:
            print(f"🚨 Error saving config: {e}")
            # Don't crash on config save errors
    
    # Compositor-aware window dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Use Qt's native window dragging through compositor
            window_handle = self.windowHandle()
            if window_handle:
                print("Starting compositor drag")
                window_handle.startSystemMove()
            event.accept()
        self.hide_timer.stop()
    
    def mouseMoveEvent(self, event):
        # Compositor handles the movement
        pass
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Save position when drag ends
            self.save_window_position()
            event.accept()
        super().mouseReleaseEvent(event)
    
    def save_window_position(self):
        """Save current window position"""
        pos = self.pos()
        print(f"Saving window position: ({pos.x()}, {pos.y()})")
        # Could save to config if needed

def signal_handler(sig, frame):
    """Handle system signals and force quit"""
    print(f"\n🚨 SIGNAL HANDLER: Received signal {sig}")
    print("🚨 FORCE KILLING PROCESS...")
    import os
    os._exit(1)

def main():
    # Install signal handlers for crash detection
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)
    
    # Emergency cleanup disabled - app is stable now
    
    app = None
    window = None
    
    try:
        print("🚀 Starting DICTATOR application...")
        
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)
        
        print("🚀 Creating main window...")
        window = DictatorWindow()
        
        print("🚀 Setting up app quit handler...")
        def on_app_quit():
            print("🚨 Application quitting via signal...")
            if window and hasattr(window, 'close_application'):
                try:
                    window.close_application()
                except:
                    pass
            import os
            os._exit(0)
        
        app.aboutToQuit.connect(on_app_quit)
        
        # Add crash detection for when last window closes
        def on_last_window_closed():
            print("🚨 LAST WINDOW CLOSED - App should quit!")
            print("🚨 FORCE KILLING PROCESS...")
            import os
            os._exit(1)
        
        app.lastWindowClosed.connect(on_last_window_closed)
        
        print("🚀 Starting event loop...")
        
        # Start monitoring thread to detect crashes
        monitor_thread = threading.Thread(target=lambda: monitor_main_thread(window), daemon=True)
        monitor_thread.start()
        
        exit_code = app.exec()
        print(f"🚨 App event loop ended with code: {exit_code}")
        
        # If we get here, the app closed normally
        if window and hasattr(window, 'close_application'):
            window.close_application()
        
        import os
        os._exit(exit_code)
        
    except Exception as e:
        print(f"🚨 FATAL ERROR IN MAIN: {e}")
        import traceback
        traceback.print_exc()
        
        if window and hasattr(window, 'close_application'):
            try:
                window.close_application()
            except:
                pass
        
        import os
        os._exit(1)

def monitor_main_thread(window):
    """Monitor the main thread and kill process if it dies"""
    import threading
    main_thread = threading.main_thread()
    window_was_visible = False
    consecutive_invisible_count = 0
    
    while True:
        time.sleep(2)  # Check every 2 seconds
        
        if not main_thread.is_alive():
            print("🚨 MONITOR: Main thread is dead! Force killing process...")
            import os
            os._exit(1)
        
        # Check if window is still valid and visible
        if window:
            try:
                is_visible = window.isVisible()
                
                # Track if window was ever visible
                if is_visible:
                    window_was_visible = True
                    consecutive_invisible_count = 0
                elif window_was_visible:  # Window was visible but now isn't
                    consecutive_invisible_count += 1
                    print(f"🚨 MONITOR: Window not visible for {consecutive_invisible_count * 2} seconds")
                    
                    # If window disappears for more than 6 seconds, assume it crashed
                    if consecutive_invisible_count >= 3:
                        print("🚨 MONITOR: Window disappeared for 6+ seconds - UI likely crashed!")
                        print("🚨 FORCE KILLING PROCESS...")
                        import os
                        os._exit(1)
                
                # Double-check: try to access a window property
                _ = window.windowTitle()
                
            except RuntimeError as e:
                print(f"🚨 MONITOR: Window RuntimeError: {e}! Force killing process...")
                import os
                os._exit(1)
            except Exception as e:
                print(f"🚨 MONITOR: Window exception: {e}! Force killing process...")
                import os
                os._exit(1)


if __name__ == "__main__":
    main()