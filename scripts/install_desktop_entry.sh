#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

APP_ID="codex-accounts-switch"
APP_NAME="Codex Accounts Switch"
WRAPPER_DIR="$HOME/.local/bin"
WRAPPER_PATH="$WRAPPER_DIR/${APP_ID}-desktop"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_PATH="$DESKTOP_DIR/${APP_ID}.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
ICON_PATH="$ICON_DIR/${APP_ID}.svg"
DEFAULT_HTTP_PROXY="${HTTP_PROXY:-${http_proxy:-}}"
DEFAULT_HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}"
DEFAULT_ALL_PROXY="${ALL_PROXY:-${all_proxy:-}}"
DEFAULT_NO_PROXY="${NO_PROXY:-${no_proxy:-}}"

mkdir -p "$WRAPPER_DIR" "$DESKTOP_DIR" "$ICON_DIR"

cat >"$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$PROJECT_ROOT"
LAUNCH_BIN="\$PROJECT_ROOT/codex-accounts-switch"
DEFAULT_HTTP_PROXY="$DEFAULT_HTTP_PROXY"
DEFAULT_HTTPS_PROXY="$DEFAULT_HTTPS_PROXY"
DEFAULT_ALL_PROXY="$DEFAULT_ALL_PROXY"
DEFAULT_NO_PROXY="$DEFAULT_NO_PROXY"
ENV_FILE="\$HOME/.config/codex-accounts-switch/env"

if [[ ! -x "\$LAUNCH_BIN" ]]; then
  echo "Launcher not found: \$LAUNCH_BIN" >&2
  exit 1
fi

# Optional user overrides (KEY=VALUE exports).
if [[ -f "\$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "\$ENV_FILE"
fi

# Fallback to installer-time proxy values when desktop session lacks them.
if [[ -z "\${HTTP_PROXY:-}" ]] && [[ -n "\$DEFAULT_HTTP_PROXY" ]]; then
  export HTTP_PROXY="\$DEFAULT_HTTP_PROXY"
fi
if [[ -z "\${HTTPS_PROXY:-}" ]] && [[ -n "\$DEFAULT_HTTPS_PROXY" ]]; then
  export HTTPS_PROXY="\$DEFAULT_HTTPS_PROXY"
fi
if [[ -z "\${ALL_PROXY:-}" ]] && [[ -n "\$DEFAULT_ALL_PROXY" ]]; then
  export ALL_PROXY="\$DEFAULT_ALL_PROXY"
fi
if [[ -z "\${NO_PROXY:-}" ]] && [[ -n "\$DEFAULT_NO_PROXY" ]]; then
  export NO_PROXY="\$DEFAULT_NO_PROXY"
fi
if [[ -z "\${http_proxy:-}" ]] && [[ -n "\${HTTP_PROXY:-}" ]]; then
  export http_proxy="\$HTTP_PROXY"
fi
if [[ -z "\${https_proxy:-}" ]] && [[ -n "\${HTTPS_PROXY:-}" ]]; then
  export https_proxy="\$HTTPS_PROXY"
fi
if [[ -z "\${all_proxy:-}" ]] && [[ -n "\${ALL_PROXY:-}" ]]; then
  export all_proxy="\$ALL_PROXY"
fi
if [[ -z "\${no_proxy:-}" ]] && [[ -n "\${NO_PROXY:-}" ]]; then
  export no_proxy="\$NO_PROXY"
fi

# Ensure desktop-launch environment matches terminal launch as closely as possible.
# This helps with PATH/proxy vars that are initialized in shell startup files.
LAUNCH_SHELL="\${SHELL:-}"
if [[ -z "\$LAUNCH_SHELL" ]] || [[ ! -x "\$LAUNCH_SHELL" ]]; then
  if command -v zsh >/dev/null 2>&1; then
    LAUNCH_SHELL="$(command -v zsh)"
  elif command -v bash >/dev/null 2>&1; then
    LAUNCH_SHELL="$(command -v bash)"
  else
    LAUNCH_SHELL=""
  fi
fi

if [[ -n "\$LAUNCH_SHELL" ]]; then
  printf -v _quoted_cmd '%q ' "\$LAUNCH_BIN" "\$@"
  exec "\$LAUNCH_SHELL" "-lc" "exec \${_quoted_cmd}"
fi

exec "\$LAUNCH_BIN" "\$@"
EOF
chmod +x "$WRAPPER_PATH"

cp "$PROJECT_ROOT/assets/icons/${APP_ID}.svg" "$ICON_PATH"

cat >"$DESKTOP_PATH" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=$APP_NAME
Comment=Switch Codex OAuth accounts and open project sessions
Exec=$WRAPPER_PATH
Icon=$ICON_PATH
Terminal=false
Categories=Development;Utility;
StartupNotify=true
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Installed desktop entry: $DESKTOP_PATH"
echo "Launch command wrapper: $WRAPPER_PATH"
