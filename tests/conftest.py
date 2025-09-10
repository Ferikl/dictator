"""
Pytest configuration and fixtures for DICTATOR tests
"""

import sys
import os
from pathlib import Path
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add src to path for testing
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_audio_devices():
    """Mock audio devices for testing"""
    devices = [
        {
            'name': 'Built-in Microphone',
            'index': 0,
            'max_input_channels': 1,
            'default_samplerate': 44100.0
        },
        {
            'name': 'USB Headset',
            'index': 1,
            'max_input_channels': 2,
            'default_samplerate': 48000.0
        }
    ]
    return devices


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice module"""
    # Create a complete mock module
    mock_sd = MagicMock()
    
    mock_sd.query_devices.return_value = [
        {
            'name': 'Built-in Microphone',
            'max_input_channels': 1,
            'default_samplerate': 44100.0
        },
        {
            'name': 'USB Headset', 
            'max_input_channels': 2,
            'default_samplerate': 48000.0
        }
    ]
    
    mock_sd.default.device = [0, 0]  # [input, output]
    
    # Mock the module import
    with patch.dict('sys.modules', {'sounddevice': mock_sd}):
        yield mock_sd


@pytest.fixture
def mock_qt_app():
    """Mock QApplication for GUI tests"""
    with patch('PyQt6.QtWidgets.QApplication') as mock_app:
        mock_instance = MagicMock()
        mock_app.return_value = mock_instance
        mock_app.instance.return_value = mock_instance
        yield mock_app


@pytest.fixture
def no_qt():
    """Disable Qt imports for non-GUI tests"""
    original_modules = {}
    qt_modules = [
        'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui'
    ]
    
    for module in qt_modules:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
            del sys.modules[module]
    
    # Mock the modules
    for module in qt_modules:
        sys.modules[module] = MagicMock()
    
    yield
    
    # Restore original modules
    for module in qt_modules:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            if module in sys.modules:
                del sys.modules[module]