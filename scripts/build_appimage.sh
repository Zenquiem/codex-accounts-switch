#!/usr/bin/env bash
set -euo pipefail

# Minimal AppImage build flow:
# 1) create local venv with project deps
# 2) build one-folder binary with PyInstaller
# 3) wrap into AppDir and produce AppImage via appimagetool

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_ROOT="$PROJECT_ROOT/.build/appimage"
VENV_PATH="$BUILD_ROOT/venv"
DIST_DIR="$BUILD_ROOT/dist"
PYI_DIST_DIR="$BUILD_ROOT/pyinstaller-dist"
PYI_WORK_DIR="$BUILD_ROOT/pyinstaller-work"
APPDIR="$BUILD_ROOT/CodexAccountsSwitch.AppDir"
APP_ID="codex-accounts-switch"

require_bin() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required binary: $1" >&2
    exit 1
  fi
}

require_bin python3
require_bin appimagetool

mkdir -p "$BUILD_ROOT"
python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

python3 -m pip install --upgrade pip
python3 -m pip install -r "$PROJECT_ROOT/requirements.txt" pyinstaller

rm -rf "$DIST_DIR" "$APPDIR" "$PYI_DIST_DIR" "$PYI_WORK_DIR"
mkdir -p "$DIST_DIR"

cd "$PROJECT_ROOT"
pyinstaller \
  --noconfirm \
  --clean \
  --name "$APP_ID" \
  --onedir \
  --distpath "$PYI_DIST_DIR" \
  --workpath "$PYI_WORK_DIR" \
  --specpath "$BUILD_ROOT" \
  --add-data "$PROJECT_ROOT/codex_accounts_switch/templates:codex_accounts_switch/templates" \
  --add-data "$PROJECT_ROOT/codex_accounts_switch/static:codex_accounts_switch/static" \
  "$PROJECT_ROOT/run.py"

mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp -r "$PYI_DIST_DIR/$APP_ID/"* "$APPDIR/usr/bin/"
cp "$PROJECT_ROOT/assets/icons/$APP_ID.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/$APP_ID.svg"

cat >"$APPDIR/usr/share/applications/$APP_ID.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Codex Accounts Switch
Comment=Switch Codex OAuth accounts and open project sessions
Exec=$APP_ID --mode desktop
Icon=$APP_ID
Terminal=false
Categories=Development;Utility;
StartupNotify=true
EOF

cat >"$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "$HERE/usr/bin/codex-accounts-switch" --mode desktop "$@"
EOF
chmod +x "$APPDIR/AppRun"

cp "$APPDIR/usr/share/applications/$APP_ID.desktop" "$APPDIR/$APP_ID.desktop"
cp "$APPDIR/usr/share/icons/hicolor/scalable/apps/$APP_ID.svg" "$APPDIR/$APP_ID.svg"

appimagetool "$APPDIR" "$DIST_DIR/${APP_ID}.AppImage"

echo "AppImage built at: $DIST_DIR/${APP_ID}.AppImage"
