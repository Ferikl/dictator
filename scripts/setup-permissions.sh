#!/bin/bash
# Setup script for DICTATOR permissions

echo "🔧 DICTATOR Permission Setup"
echo "============================"
echo

# Check if user is already in input group
if groups | grep -q "\binput\b"; then
    echo "✅ User is already in 'input' group - hotkeys should work!"
    exit 0
fi

echo "❌ User is not in 'input' group - global hotkeys won't work"
echo

# Check if we can run sudo
if ! sudo -n true 2>/dev/null; then
    echo "🔑 Please enter your password to add your user to the 'input' group:"
fi

# Add user to input group
echo "   Running: sudo usermod -a -G input $USER"
if sudo usermod -a -G input "$USER"; then
    echo
    echo "✅ Successfully added $USER to 'input' group!"
    echo
    echo "⚠️  IMPORTANT: You must log out and back in for changes to take effect."
    echo "   After logging back in, global hotkeys (Ctrl+Space) will work in DICTATOR."
    echo
    echo "💡 Alternative: Restart your session with:"
    echo "   newgrp input"
    echo "   dictator"
else
    echo
    echo "❌ Failed to add user to input group"
    echo "💡 You can still use DICTATOR - just use the GUI buttons instead of hotkeys."
fi