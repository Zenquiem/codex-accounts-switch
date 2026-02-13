#!/usr/bin/env bash
set -euo pipefail

APP_ID="codex-accounts-switch"
WRAPPER_PATH="$HOME/.local/bin/${APP_ID}-desktop"
ALIAS_PATH="$HOME/.local/bin/cas"
DESKTOP_PATH="$HOME/.local/share/applications/${APP_ID}.desktop"
ICON_PATH="$HOME/.local/share/icons/hicolor/scalable/apps/${APP_ID}.svg"

rm -f "$WRAPPER_PATH" "$ALIAS_PATH" "$DESKTOP_PATH" "$ICON_PATH"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

echo "Removed desktop entry and wrapper for $APP_ID."
