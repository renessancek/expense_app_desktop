#!/bin/bash

set -e

DESKTOP_FILE_PATH="$HOME/.local/share/applications/expense-app-desktop.desktop"
ICON_PATH="$HOME/.local/share/icons/hicolor/scalable/apps/expense-app-desktop.svg"

if [ -f "$DESKTOP_FILE_PATH" ]; then
    rm -f "$DESKTOP_FILE_PATH"
    echo "Removed desktop launcher."
else
    echo "Desktop launcher was not installed."
fi

if [ -f "$ICON_PATH" ]; then
    rm -f "$ICON_PATH"
    echo "Removed app icon."
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi
