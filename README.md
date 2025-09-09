# Dictator Translator

A real-time speech translation application with a floating, transparent PyQt6 interface. Designed specifically for Fedora 42 as a system service.

## Features

- 🎤 **Global Hotkey Activation**: Press `Ctrl+Space` to start recording
- 🧠 **Local AI Models**: Uses OpenAI Whisper for speech recognition and Helsinki-NLP models for translation
- 🪟 **Floating Transparent UI**: Unobtrusive overlay that stays on top
- 📋 **Translation History**: View and copy previous translations
- ⚙️ **Microphone Selection**: Choose your preferred audio input device
- 🔧 **Whisper Model Selection**: Choose from tiny, base, small, medium, or large models
- 💾 **Persistent Settings**: System-wide configuration storage
- 🔄 **Systemd Service**: Runs automatically at system startup
- 🎯 **Auto-hide**: Window automatically hides after translation (configurable)
- 🔒 **Privacy-First**: All processing happens locally - no data sent to external servers

## System Requirements

- Fedora 42 (may work on other Linux distributions)
- Python 3.8+
- uv package manager
- Audio input device (microphone)
- **GPU recommended** (CUDA) for faster model inference
- ~3-8GB free disk space (for AI models)
- **No internet required** after initial model download

## Installation

1. Clone or download this repository
2. Navigate to the `scripts` directory
3. Run the installation script:

```bash
cd scripts/
./install.sh
```

The installer will:
- Install system dependencies (audio libraries, FFmpeg, development tools)
- Install uv package manager (if not present)
- Create a uv virtual environment
- Install Python dependencies (PyTorch, Whisper, Transformers) using uv
- Download initial AI models (Whisper base model and translation models)
- Set up systemd service
- Create desktop entry and control scripts

## Usage

### Basic Operation

1. **Start Recording**: Press and hold `Ctrl+Space`
2. **Speak**: The floating window will appear with recording status
3. **Release**: Let go of `Ctrl+Space` to stop recording
4. **View Translation**: The translated text appears in the history

### Settings

- Click the **⚙** (gear) icon in the floating window to access settings
- **Microphone Selection**: Choose from available audio input devices
- **Whisper Model**: Select model size (tiny=fastest, large=most accurate)
- **Language Selection**: Set source and target languages
- **Auto-hide**: Toggle automatic window hiding after translation

### Model Information

**Whisper Models** (Speech Recognition):
- `tiny`: ~39MB, fastest, basic accuracy
- `base`: ~74MB, good balance of speed/accuracy (default)
- `small`: ~244MB, better accuracy
- `medium`: ~769MB, high accuracy
- `large`: ~1550MB, best accuracy but slower

**Translation Models** (Helsinki-NLP):
- Automatically downloaded on first use for each language pair
- ~300MB each, cached locally after download

### Service Control

Use these commands to control the service:

```bash
# Start the service
dictator-translator-start

# Stop the service
dictator-translator-stop

# Check service status
dictator-translator-status
```

### Manual Service Control

```bash
# Start service
systemctl --user start dictator-translator@$USER.service

# Stop service
systemctl --user stop dictator-translator@$USER.service

# Check status
systemctl --user status dictator-translator@$USER.service

# View logs
journalctl --user -u dictator-translator@$USER.service -f
```

## Configuration

Configuration is stored in JSON format:

- **System-wide**: `/etc/dictator-translator/config.json` (preferred)
- **User-specific**: `~/.config/dictator-translator/config.json` (fallback)

### Configuration Options

```json
{
  "source_lang": "auto",
  "target_lang": "en", 
  "microphone_index": 0,
  "auto_hide": true,
  "history": []
}
```

## Supported Languages

Common language codes:
- `auto` - Auto-detect (source only)
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean

## Troubleshooting

### Service Won't Start
```bash
# Check service logs
journalctl --user -u dictator-translator@$USER.service -f

# Check if dependencies are installed
uv pip list | grep -E "(PyQt6|speech-recognition|googletrans)"
```

### Audio Issues
```bash
# List audio devices
arecord -l

# Test microphone
arecord -d 3 -f cd test.wav && aplay test.wav
```

### Permission Issues
```bash
# Check if user is in audio group
groups $USER | grep audio

# Add user to audio group if needed
sudo usermod -a -G audio $USER
```

### Translation Errors
- Check if models are downloaded (first run takes time)
- Try switching to a smaller Whisper model if memory issues
- Check disk space for model downloads
- GPU memory issues: try switching to CPU-only mode

## Uninstallation

To completely remove the application:

```bash
cd scripts/
./uninstall.sh
```

This will:
- Stop and disable the systemd service
- Remove installation files
- Remove systemd service file
- Optionally remove configuration directories

## Development

### Project Structure
```
dictator-translator/
├── src/
│   ├── main.py              # Main application
│   ├── translator.py        # Translation service
│   ├── speech_recorder.py   # Speech recognition
│   └── hotkey_manager.py    # Global hotkey handling
├── systemd/
│   └── dictator-translator.service  # Systemd service file
├── scripts/
│   ├── install.sh          # Installation script
│   └── uninstall.sh        # Uninstallation script
├── pyproject.toml           # Project configuration and dependencies
└── README.md               # Documentation
```

### Running in Development Mode

```bash
# Create uv virtual environment and install dependencies
uv sync

# Run application
uv run python src/main.py

# Or activate the virtual environment
source .venv/bin/activate
python src/main.py
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and feature requests, please create an issue in the project repository.