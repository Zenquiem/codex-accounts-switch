# Changelog

All notable changes to this project will be documented in this file.

## [1.0.4] - 2026-02-13

### Fixed
- Installer now auto-adds `~/.local/bin` to `PATH` in `~/.bashrc`, `~/.zshrc`, and `~/.profile` when missing, so `cas` works out of the box after installation.

## [1.0.3] - 2026-02-13

### Fixed
- Fixed desktop shell blank-window issue on some VM/WebKitGTK environments by forcing WebKit compatibility flags at runtime.
- Added `CAS_WEBKIT_VM_COMPAT=0` switch for users who need to disable the forced VM compatibility mode.

## [1.0.2] - 2026-02-13

### Added
- Added a short launcher alias command `cas` (installed to `~/.local/bin/cas` by desktop installer script).
- Added README instructions for installing `npm`/`node` on Ubuntu and then installing Codex CLI.

### Changed
- Self-update repo resolution now falls back to built-in default repo when `CAS_UPDATE_REPO` and git remote are unavailable.
- Self "install latest" now opens GitHub latest release page in non-git package mode.

## [1.0.1] - 2026-02-12

### Added
- About panel now supports per-component latest-version checks.
- Added per-component "install latest" action (opens install terminal).
- Added upgrade status display (current/latest/upgradable) for environment components.
- Added self-update check for this tool (current vs latest GitHub release/tag version).
- Added self "install latest" action and highlighted update status badge in About panel.

## [1.0.0] - 2026-02-12

### Added
- Multi-account Codex OAuth isolation via per-account `CODEX_HOME`.
- Account management: add (OAuth login flow), dedupe by OAuth fingerprint, delete with project reference protection.
- Project management: add, edit, delete, launch in terminal with bound account.
- Session management: list/recover by project, dedupe by `session_id`, search/filter, preview.
- Session delete and recycle bin restore flow.
- Quota panel in account management (5-hour / weekly) with manual refresh.
- Settings panel: General / Advanced / About.
- UI settings: language (zh/en), theme (dark/light), close behavior.
- Environment diagnostics page and config directory quick-open.
- Desktop shell mode (`pywebview`) and `.desktop` installer scripts.

### Changed
- Product form changed from CLI-first to local Web UI + desktop shell.
- Session display title uses first user sentence instead of raw UUID.

### Fixed
- Session history duplicate rendering for one conversation split across rollout files.
- Desktop-launch and terminal-launch environment consistency for quota checks.
