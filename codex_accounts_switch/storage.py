from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class StorageError(Exception):
    """Raised when registry operations fail validation."""


@dataclass
class RegistryPaths:
    root: Path
    registry: Path
    accounts_root: Path
    logs: Path
    accounts_file: Path
    projects_file: Path
    settings_file: Path


UI_LANGUAGE_VALUES = {"zh-CN", "en-US"}
UI_THEME_VALUES = {"light", "dark"}
UI_WINDOW_CLOSE_BEHAVIOR_VALUES = {"exit", "minimize_to_tray"}


def _default_ui_settings() -> dict[str, str]:
    return {
        "language": "zh-CN",
        "theme": "light",
        "window_close_behavior": "exit",
    }


def _default_settings_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "ui": _default_ui_settings(),
        "updated_at": _utc_now(),
    }


class RegistryStore:
    def __init__(self, root: Path | None = None) -> None:
        base = root or Path.home() / ".local" / "share" / "codex-accounts-switch"
        self.paths = RegistryPaths(
            root=base,
            registry=base / "registry",
            accounts_root=base / "accounts",
            logs=base / "logs",
            accounts_file=base / "registry" / "accounts.json",
            projects_file=base / "registry" / "projects.json",
            settings_file=base / "registry" / "settings.json",
        )
        self._lock = threading.Lock()
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        for folder in (
            self.paths.root,
            self.paths.registry,
            self.paths.accounts_root,
            self.paths.logs,
        ):
            folder.mkdir(parents=True, exist_ok=True)
            self._chmod_best_effort(folder, 0o700)

        if not self.paths.accounts_file.exists():
            self._write_json(self.paths.accounts_file, {"version": 1, "accounts": []})
        if not self.paths.projects_file.exists():
            self._write_json(self.paths.projects_file, {"version": 1, "projects": []})
        if not self.paths.settings_file.exists():
            self._write_json(self.paths.settings_file, _default_settings_payload())

        self._chmod_best_effort(self.paths.accounts_file, 0o600)
        self._chmod_best_effort(self.paths.projects_file, 0o600)
        self._chmod_best_effort(self.paths.settings_file, 0o600)

    @staticmethod
    def _chmod_best_effort(path: Path, mode: int) -> None:
        try:
            os.chmod(path, mode)
        except OSError:
            pass

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        tmp_path.replace(path)

    def _read_accounts(self) -> dict[str, Any]:
        return self._read_json(self.paths.accounts_file)

    def _write_accounts(self, payload: dict[str, Any]) -> None:
        self._write_json(self.paths.accounts_file, payload)
        self._chmod_best_effort(self.paths.accounts_file, 0o600)

    def _read_projects(self) -> dict[str, Any]:
        return self._read_json(self.paths.projects_file)

    def _write_projects(self, payload: dict[str, Any]) -> None:
        self._write_json(self.paths.projects_file, payload)
        self._chmod_best_effort(self.paths.projects_file, 0o600)

    def _read_settings(self) -> dict[str, Any]:
        try:
            payload = self._read_json(self.paths.settings_file)
            if isinstance(payload, dict):
                return payload
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            pass
        payload = _default_settings_payload()
        self._write_settings(payload)
        return payload

    def _write_settings(self, payload: dict[str, Any]) -> None:
        self._write_json(self.paths.settings_file, payload)
        self._chmod_best_effort(self.paths.settings_file, 0o600)

    @staticmethod
    def _normalize_ui_settings(raw_ui: Any) -> dict[str, str]:
        defaults = _default_ui_settings()
        if not isinstance(raw_ui, dict):
            return defaults

        language = str(raw_ui.get("language", defaults["language"])).strip()
        theme = str(raw_ui.get("theme", defaults["theme"])).strip()
        close_behavior = str(
            raw_ui.get("window_close_behavior", defaults["window_close_behavior"])
        ).strip()

        if language not in UI_LANGUAGE_VALUES:
            language = defaults["language"]
        if theme not in UI_THEME_VALUES:
            theme = defaults["theme"]
        if close_behavior not in UI_WINDOW_CLOSE_BEHAVIOR_VALUES:
            close_behavior = defaults["window_close_behavior"]

        return {
            "language": language,
            "theme": theme,
            "window_close_behavior": close_behavior,
        }

    def get_ui_settings(self) -> dict[str, str]:
        with self._lock:
            payload = self._read_settings()
            normalized = self._normalize_ui_settings(payload.get("ui"))
            if payload.get("ui") != normalized:
                payload["ui"] = normalized
                payload["updated_at"] = _utc_now()
                self._write_settings(payload)
            return dict(normalized)

    def update_ui_settings(self, updates: dict[str, Any]) -> dict[str, str]:
        if not isinstance(updates, dict):
            raise StorageError("设置更新参数无效。")

        with self._lock:
            payload = self._read_settings()
            current = self._normalize_ui_settings(payload.get("ui"))
            next_settings = dict(current)

            if "language" in updates and updates.get("language") is not None:
                language = str(updates.get("language", "")).strip()
                if language not in UI_LANGUAGE_VALUES:
                    raise StorageError("language 取值无效。")
                next_settings["language"] = language

            if "theme" in updates and updates.get("theme") is not None:
                theme = str(updates.get("theme", "")).strip()
                if theme not in UI_THEME_VALUES:
                    raise StorageError("theme 取值无效。")
                next_settings["theme"] = theme

            if "window_close_behavior" in updates and updates.get("window_close_behavior") is not None:
                behavior = str(updates.get("window_close_behavior", "")).strip()
                if behavior not in UI_WINDOW_CLOSE_BEHAVIOR_VALUES:
                    raise StorageError("window_close_behavior 取值无效。")
                next_settings["window_close_behavior"] = behavior

            payload["ui"] = next_settings
            payload["updated_at"] = _utc_now()
            self._write_settings(payload)
            return dict(next_settings)

    def list_accounts(self) -> list[dict[str, Any]]:
        with self._lock:
            payload = self._read_accounts()
            return payload.get("accounts", [])

    def list_projects(self) -> list[dict[str, Any]]:
        with self._lock:
            payload = self._read_projects()
            return payload.get("projects", [])

    def find_account(self, account_id: str) -> dict[str, Any] | None:
        for account in self.list_accounts():
            if account["id"] == account_id:
                return account
        return None

    def find_account_by_alias(self, alias: str) -> dict[str, Any] | None:
        alias_norm = alias.strip().lower()
        for account in self.list_accounts():
            if account["alias"].strip().lower() == alias_norm:
                return account
        return None

    def find_account_by_oauth_fingerprint(self, oauth_fingerprint: str) -> dict[str, Any] | None:
        fingerprint = oauth_fingerprint.strip()
        if not fingerprint:
            return None
        for account in self.list_accounts():
            if account.get("oauth_fingerprint") == fingerprint:
                return account
        return None

    def add_account(
        self,
        alias: str,
        account_id: str,
        codex_home: Path,
        oauth_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        alias = alias.strip()
        if not alias:
            raise StorageError("账号别名不能为空。")
        fingerprint = oauth_fingerprint.strip() if isinstance(oauth_fingerprint, str) else ""

        with self._lock:
            accounts_payload = self._read_accounts()
            accounts = accounts_payload.get("accounts", [])
            for account in accounts:
                if account["alias"].strip().lower() == alias.lower():
                    raise StorageError(f"账号别名 `{alias}` 已存在。")
                if fingerprint and account.get("oauth_fingerprint") == fingerprint:
                    existing_alias = account.get("alias", account.get("id", "未知账号"))
                    raise StorageError(f"该 OAuth 账号已存在（别名 `{existing_alias}`）。")

            record = {
                "id": account_id,
                "alias": alias,
                "codex_home": str(codex_home),
                "created_at": _utc_now(),
                "last_used_at": None,
            }
            if fingerprint:
                record["oauth_fingerprint"] = fingerprint
            accounts.append(record)
            accounts_payload["accounts"] = accounts
            self._write_accounts(accounts_payload)
            return record

    def set_account_oauth_fingerprint(self, account_id: str, oauth_fingerprint: str) -> None:
        fingerprint = oauth_fingerprint.strip()
        if not fingerprint:
            raise StorageError("oauth_fingerprint 不能为空。")

        with self._lock:
            accounts_payload = self._read_accounts()
            accounts = accounts_payload.get("accounts", [])

            target = None
            for account in accounts:
                if account.get("oauth_fingerprint") == fingerprint and account["id"] != account_id:
                    existing_alias = account.get("alias", account.get("id", "未知账号"))
                    raise StorageError(f"该 OAuth 账号已存在（别名 `{existing_alias}`）。")
                if account["id"] == account_id:
                    target = account

            if target is None:
                raise StorageError("未找到账号。")

            if target.get("oauth_fingerprint") == fingerprint:
                return

            target["oauth_fingerprint"] = fingerprint
            accounts_payload["accounts"] = accounts
            self._write_accounts(accounts_payload)

    def delete_account(self, account_id: str) -> dict[str, Any]:
        with self._lock:
            projects_payload = self._read_projects()
            referenced = [
                item
                for item in projects_payload.get("projects", [])
                if item.get("account_id") == account_id
            ]
            if referenced:
                refs = ", ".join(sorted(item["name"] for item in referenced))
                raise StorageError(f"该账号仍被项目引用：{refs}")

            accounts_payload = self._read_accounts()
            accounts = accounts_payload.get("accounts", [])
            target = None
            remaining: list[dict[str, Any]] = []
            for account in accounts:
                if account["id"] == account_id:
                    target = account
                else:
                    remaining.append(account)

            if target is None:
                raise StorageError("未找到要删除的账号。")

            accounts_payload["accounts"] = remaining
            self._write_accounts(accounts_payload)
            return target

    def add_project(self, name: str, path: Path, account_id: str) -> dict[str, Any]:
        name = name.strip()
        if not name:
            raise StorageError("项目名不能为空。")
        if not path.exists() or not path.is_dir():
            raise StorageError("项目路径不存在或不是目录。")

        with self._lock:
            accounts_payload = self._read_accounts()
            projects_payload = self._read_projects()
            projects = projects_payload.get("projects", [])

            if not any(item["id"] == account_id for item in accounts_payload.get("accounts", [])):
                raise StorageError("所选账号不存在。")

            for project in projects:
                if project["name"].strip().lower() == name.lower():
                    raise StorageError(f"项目名 `{name}` 已存在。")

            record = {
                "id": uuid.uuid4().hex[:12],
                "name": name,
                "path": str(path.resolve()),
                "account_id": account_id,
                "preferred_shell": "zsh",
                "created_at": _utc_now(),
                "last_opened_at": None,
            }
            projects.append(record)
            projects_payload["projects"] = projects
            self._write_projects(projects_payload)
            return record

    def update_project(self, project_id: str, name: str, path: Path, account_id: str) -> dict[str, Any]:
        name = name.strip()
        if not name:
            raise StorageError("项目名不能为空。")
        if not path.exists() or not path.is_dir():
            raise StorageError("项目路径不存在或不是目录。")

        with self._lock:
            accounts_payload = self._read_accounts()
            projects_payload = self._read_projects()
            projects = projects_payload.get("projects", [])

            if not any(item["id"] == account_id for item in accounts_payload.get("accounts", [])):
                raise StorageError("所选账号不存在。")

            target = None
            for project in projects:
                if project["id"] == project_id:
                    target = project
                elif project["name"].strip().lower() == name.lower():
                    raise StorageError(f"项目名 `{name}` 已存在。")

            if target is None:
                raise StorageError("未找到要更新的项目。")

            target["name"] = name
            target["path"] = str(path.resolve())
            target["account_id"] = account_id
            target["updated_at"] = _utc_now()

            projects_payload["projects"] = projects
            self._write_projects(projects_payload)
            return target

    def find_project(self, project_id: str) -> dict[str, Any] | None:
        for project in self.list_projects():
            if project["id"] == project_id:
                return project
        return None

    def delete_project(self, project_id: str) -> dict[str, Any]:
        with self._lock:
            projects_payload = self._read_projects()
            projects = projects_payload.get("projects", [])
            target = None
            remaining: list[dict[str, Any]] = []
            for project in projects:
                if project["id"] == project_id:
                    target = project
                else:
                    remaining.append(project)

            if target is None:
                raise StorageError("未找到要删除的项目。")

            projects_payload["projects"] = remaining
            self._write_projects(projects_payload)
            return target

    def touch_project_opened(self, project_id: str) -> None:
        with self._lock:
            projects_payload = self._read_projects()
            changed = False
            for project in projects_payload.get("projects", []):
                if project["id"] == project_id:
                    project["last_opened_at"] = _utc_now()
                    changed = True
                    break
            if changed:
                self._write_projects(projects_payload)

    def touch_account_used(self, account_id: str) -> None:
        with self._lock:
            accounts_payload = self._read_accounts()
            changed = False
            for account in accounts_payload.get("accounts", []):
                if account["id"] == account_id:
                    account["last_used_at"] = _utc_now()
                    changed = True
                    break
            if changed:
                self._write_accounts(accounts_payload)
