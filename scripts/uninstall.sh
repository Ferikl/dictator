#!/bin/bash

# Dictator Translator Uninstallation Script
# This script removes the dictator-translator service and files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Dictator Translator Uninstallation Script${NC}"
echo "========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root. It will prompt for sudo when needed.${NC}" 
   exit 1
fi

# Stop and disable service
echo -e "${GREEN}Stopping and disabling service...${NC}"
systemctl --user stop dictator-translator@$USER.service 2>/dev/null || true
sudo systemctl disable dictator-translator@$USER.service 2>/dev/null || true

# Remove systemd service file
echo -e "${GREEN}Removing systemd service file...${NC}"
sudo rm -f /etc/systemd/system/dictator-translator@.service

# Reload systemd
sudo systemctl daemon-reload

# Remove installation directory
echo -e "${GREEN}Removing installation directory...${NC}"
sudo rm -rf /opt/dictator-translator

# Remove config directory (ask user)
read -p "Remove system configuration directory /etc/dictator-translator? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo rm -rf /etc/dictator-translator
    echo -e "${GREEN}System config directory removed.${NC}"
fi

# Remove user config directory (ask user)
read -p "Remove user configuration directory ~/.config/dictator-translator? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.config/dictator-translator
    echo -e "${GREEN}User config directory removed.${NC}"
fi

# Remove desktop entry
echo -e "${GREEN}Removing desktop entry...${NC}"
rm -f ~/.local/share/applications/dictator-translator.desktop

# Remove control scripts
echo -e "${GREEN}Removing control scripts...${NC}"
sudo rm -f /usr/local/bin/dictator-translator-start
sudo rm -f /usr/local/bin/dictator-translator-stop
sudo rm -f /usr/local/bin/dictator-translator-status

echo -e "${GREEN}Uninstallation completed successfully!${NC}"
echo -e "${YELLOW}Note: System dependencies (Python packages, audio libraries) were not removed.${NC}"