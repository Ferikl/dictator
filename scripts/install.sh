#!/bin/bash

# Dictator Translator Installation Script for Fedora 42
# This script installs the dictator-translator as a system service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root. It will prompt for sudo when needed.${NC}" 
   exit 1
fi

echo -e "${GREEN}Dictator Translator Installation Script${NC}"
echo "========================================"

# Check if on Fedora
if ! grep -q "Fedora" /etc/os-release; then
    echo -e "${YELLOW}Warning: This script is designed for Fedora. Continuing anyway...${NC}"
fi

# Install system dependencies
echo -e "${GREEN}Installing system dependencies...${NC}"
sudo dnf update -y
sudo dnf install -y python3 python3-tkinter \
                   portaudio-devel python3-devel gcc gcc-c++ \
                   pulseaudio-libs-devel alsa-lib-devel \
                   libX11-devel libXtst-devel \
                   ffmpeg ffmpeg-devel \
                   libsndfile libsndfile-devel

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo -e "${GREEN}Installing uv package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create installation directory
INSTALL_DIR="/opt/dictator-translator"
echo -e "${GREEN}Creating installation directory: $INSTALL_DIR${NC}"
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Copy application files
echo -e "${GREEN}Copying application files...${NC}"
cp -r ../src "$INSTALL_DIR/"
cp ../pyproject.toml "$INSTALL_DIR/"
cp ../README.md "$INSTALL_DIR/" 2>/dev/null || true

# Create and sync uv environment
echo -e "${GREEN}Creating uv virtual environment and installing dependencies...${NC}"
cd "$INSTALL_DIR"
uv venv
uv sync

# Create config directory
echo -e "${GREEN}Creating configuration directory...${NC}"
sudo mkdir -p /etc/dictator-translator
sudo chown $USER:$USER /etc/dictator-translator

# Create user config directory
mkdir -p ~/.config/dictator-translator

# Install systemd service
echo -e "${GREEN}Installing systemd service...${NC}"
sudo cp ../systemd/dictator-translator.service /etc/systemd/system/dictator-translator@.service

# Enable and start service
echo -e "${GREEN}Enabling systemd service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable dictator-translator@$USER.service

# Create desktop entry
echo -e "${GREEN}Creating desktop entry...${NC}"
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/dictator-translator.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Dictator Translator
Comment=Real-time speech translation with floating UI
Exec=$INSTALL_DIR/.venv/bin/python $INSTALL_DIR/src/main.py
Icon=preferences-desktop-locale
Terminal=false
Categories=Utility;Office;AudioVideo;
StartupNotify=false
EOF

# Create convenient scripts
echo -e "${GREEN}Creating control scripts...${NC}"
sudo tee /usr/local/bin/dictator-translator-start > /dev/null << EOF
#!/bin/bash
systemctl --user start dictator-translator@$USER.service
EOF

sudo tee /usr/local/bin/dictator-translator-stop > /dev/null << EOF
#!/bin/bash
systemctl --user stop dictator-translator@$USER.service
EOF

sudo tee /usr/local/bin/dictator-translator-status > /dev/null << EOF
#!/bin/bash
systemctl --user status dictator-translator@$USER.service
EOF

sudo chmod +x /usr/local/bin/dictator-translator-*

# Start the service
echo -e "${GREEN}Starting dictator-translator service...${NC}"
systemctl --user start dictator-translator@$USER.service

echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "- Press Ctrl+Space to activate speech translation"
echo "- The floating window will appear and capture your speech"
echo "- Translation history is automatically saved"
echo "- Access settings via the gear icon in the window"
echo ""
echo -e "${YELLOW}Control commands:${NC}"
echo "- Start service: dictator-translator-start"
echo "- Stop service: dictator-translator-stop"
echo "- Check status: dictator-translator-status"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "- System config: /etc/dictator-translator/config.json"
echo "- User config: ~/.config/dictator-translator/config.json"
echo ""
echo -e "${GREEN}Service should now be running. Try pressing Ctrl+Space!${NC}"