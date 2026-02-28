#!/bin/bash

set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_NAME="Expense App Desktop"
DESKTOP_FILE_PATH="$HOME/.local/share/applications/expense-app-desktop.desktop"
ICON_SOURCE_PATH="$PROJECT_DIR/assets/expense-app-desktop.svg"
ICON_DIR_PATH="$HOME/.local/share/icons/hicolor/scalable/apps"
ICON_TARGET_PATH="$ICON_DIR_PATH/expense-app-desktop.svg"

mkdir -p "$HOME/.local/share/applications"
mkdir -p "$ICON_DIR_PATH"
chmod +x "$PROJECT_DIR/start_expense_app.sh"

if [ -f "$ICON_SOURCE_PATH" ]; then
    cp "$ICON_SOURCE_PATH" "$ICON_TARGET_PATH"
fi

cat > "$DESKTOP_FILE_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Manage and categorize expenses
Exec=$PROJECT_DIR/start_expense_app.sh
Icon=expense-app-desktop
Path=$PROJECT_DIR
Terminal=false
Categories=Office;Finance;
StartupNotify=true
EOF

chmod 644 "$DESKTOP_FILE_PATH"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Installed '$APP_NAME' in your Applications menu."
echo "You can now launch it by searching for: $APP_NAME"
