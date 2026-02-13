# Contributing

Thanks for your interest in contributing to `codex-accounts-switch`.

## Before You Start

- Open an issue first for non-trivial changes.
- Keep changes focused. One PR should solve one problem.
- If you are fixing a bug, include clear reproduction steps.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Local Checks (Required)

Run these before creating a PR:

```bash
python3 -m compileall run.py codex_accounts_switch
bash -n scripts/install_desktop_entry.sh scripts/uninstall_desktop_entry.sh scripts/build_appimage.sh
node --check codex_accounts_switch/static/app.js
```

## Commit Message Convention

Use concise Conventional Commits style when possible:

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`
- `chore: ...`

Example:

```text
fix: fallback to sudo for npm global codex update
```

## Pull Request Guidelines

- Fill out the PR template completely.
- Describe:
  - what changed
  - why it changed
  - how you tested it
- For UI changes, include screenshots.
- For behavior changes, include migration/upgrade notes if needed.

## Release Checklist (Maintainers)

1. Update `codex_accounts_switch/version.py`.
2. Update `CHANGELOG.md`.
3. Ensure CI passes.
4. Tag release: `vX.Y.Z`.
5. Publish GitHub Release notes.
