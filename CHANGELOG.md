# Changelog

All notable changes to this project will be documented in this file.

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
