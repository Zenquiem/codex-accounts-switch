## Summary

- What changed?
- Why this change is needed?

## Changes

- [ ] Backend
- [ ] Frontend
- [ ] Scripts / Packaging
- [ ] Docs

## Testing

Describe what you tested and the results.

```bash
python3 -m compileall run.py codex_accounts_switch
bash -n scripts/install_desktop_entry.sh scripts/uninstall_desktop_entry.sh scripts/build_appimage.sh
node --check codex_accounts_switch/static/app.js
```

## Screenshots (if UI changed)

Attach before/after screenshots if applicable.

## Compatibility Notes

- Any behavior changes?
- Any migration steps required for users?

## Checklist

- [ ] I kept this PR focused (single purpose).
- [ ] I updated docs when behavior changed.
- [ ] I updated `CHANGELOG.md` if needed.
- [ ] CI checks pass.
