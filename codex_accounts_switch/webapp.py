from __future__ import annotations

import os
import platform
import shutil
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from .codex_ops import (
    CodexOpsError,
    check_component_latest_version,
    check_self_latest_version,
    collect_system_status,
    delete_project_session_files,
    get_account_quota,
    get_project_session_preview,
    launch_component_latest_install,
    list_project_sessions,
    list_project_trashed_sessions,
    launch_self_latest_install,
    open_directory,
    open_account_trash,
    open_project_terminal,
    pick_existing_directory,
    plan_project_session_deletion,
    read_oauth_account_fingerprint,
    restore_project_session_files,
    run_oauth_login_in_terminal,
)
from .storage import RegistryStore, StorageError
from .version import __version__


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _sanitize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _pick_most_recent_account(accounts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not accounts:
        return None

    def _key(item: dict[str, Any]) -> str:
        return _sanitize_text(item.get("last_used_at")) or _sanitize_text(item.get("created_at"))

    return sorted(accounts, key=_key, reverse=True)[0]


def create_app(data_root: str | None = None) -> Flask:
    app = Flask(__name__)
    store = RegistryStore(Path(data_root) if data_root else None)
    static_dir = Path(app.static_folder) if app.static_folder else None

    def _backfill_account_fingerprint(account: dict[str, Any]) -> str | None:
        existing = _sanitize_text(account.get("oauth_fingerprint"))
        if existing:
            return existing

        codex_home_raw = _sanitize_text(account.get("codex_home"))
        if not codex_home_raw:
            return None

        try:
            fingerprint = read_oauth_account_fingerprint(Path(codex_home_raw))
        except CodexOpsError:
            return None

        try:
            store.set_account_oauth_fingerprint(account["id"], fingerprint)
            return fingerprint
        except StorageError:
            return None

    def _find_existing_account_by_fingerprint(oauth_fingerprint: str) -> dict[str, Any] | None:
        direct = store.find_account_by_oauth_fingerprint(oauth_fingerprint)
        if direct:
            return direct

        for account in store.list_accounts():
            if _sanitize_text(account.get("oauth_fingerprint")):
                continue
            fingerprint = _backfill_account_fingerprint(account)
            if fingerprint == oauth_fingerprint:
                return store.find_account(account["id"]) or account
        return None

    for existing_account in store.list_accounts():
        if not _sanitize_text(existing_account.get("oauth_fingerprint")):
            _backfill_account_fingerprint(existing_account)

    @app.get("/")
    def index():
        asset_version: str | int = __version__
        if static_dir:
            try:
                css_mtime = (static_dir / "styles.css").stat().st_mtime
                js_mtime = (static_dir / "app.js").stat().st_mtime
                asset_version = int(max(css_mtime, js_mtime))
            except OSError:
                asset_version = __version__
        return render_template(
            "index.html",
            app_version=__version__,
            asset_version=asset_version,
        )

    @app.get("/api/bootstrap")
    def api_bootstrap():
        accounts = store.list_accounts()
        projects = store.list_projects()
        ui_settings = store.get_ui_settings()
        account_map = {item["id"]: item["alias"] for item in accounts}
        for project in projects:
            project["account_alias"] = account_map.get(project["account_id"], "未知账号")
        return jsonify(
            {
                "ok": True,
                "accounts": accounts,
                "projects": projects,
                "ui_settings": ui_settings,
            }
        )

    @app.post("/api/accounts")
    def api_add_account():
        alias = _sanitize_text(request.json.get("alias") if request.is_json else None)
        if not alias:
            return _json_error("账号别名不能为空。")
        if store.find_account_by_alias(alias):
            return _json_error(f"账号别名 `{alias}` 已存在。", status=409)

        account_id = uuid.uuid4().hex[:12]
        codex_home = store.paths.accounts_root / account_id
        codex_home.mkdir(parents=True, exist_ok=False)
        try:
            try:
                os.chmod(codex_home, 0o700)
            except OSError:
                pass
            logged_in, message = run_oauth_login_in_terminal(codex_home)
            if not logged_in:
                shutil.rmtree(codex_home, ignore_errors=True)
                return _json_error(f"账号登录未完成：{message}")

            oauth_fingerprint = read_oauth_account_fingerprint(codex_home)
            duplicate = _find_existing_account_by_fingerprint(oauth_fingerprint)
            if duplicate:
                shutil.rmtree(codex_home, ignore_errors=True)
                duplicate_alias = _sanitize_text(duplicate.get("alias")) or duplicate.get("id", "未知账号")
                return _json_error(
                    f"该 OAuth 账号已存在（别名 `{duplicate_alias}`），无需重复添加。",
                    status=409,
                )

            record = store.add_account(
                alias=alias,
                account_id=account_id,
                codex_home=codex_home,
                oauth_fingerprint=oauth_fingerprint,
            )
            return jsonify({"ok": True, "account": record, "message": "账号添加成功。"})
        except StorageError as exc:
            status = 409 if "已存在" in str(exc) else 400
            shutil.rmtree(codex_home, ignore_errors=True)
            return _json_error(str(exc), status=status)
        except CodexOpsError as exc:
            shutil.rmtree(codex_home, ignore_errors=True)
            return _json_error(str(exc))
        except Exception:
            shutil.rmtree(codex_home, ignore_errors=True)
            return _json_error("添加账号时发生未知错误。", status=500)

    @app.delete("/api/accounts/<account_id>")
    def api_delete_account(account_id: str):
        try:
            removed = store.delete_account(account_id)
            shutil.rmtree(Path(removed["codex_home"]), ignore_errors=True)
            return jsonify({"ok": True, "removed": removed})
        except StorageError as exc:
            return _json_error(str(exc))

    @app.get("/api/accounts/<account_id>/quota")
    def api_get_account_quota(account_id: str):
        account = store.find_account(account_id)
        if not account:
            return _json_error("未找到账号。", status=404)

        force_refresh = _to_bool(request.args.get("force"), default=False)
        try:
            quota = get_account_quota(
                codex_home=Path(account["codex_home"]),
                force_refresh=force_refresh,
            )
            return jsonify(
                {
                    "ok": True,
                    "account_id": account_id,
                    "quota": quota,
                }
            )
        except CodexOpsError as exc:
            return _json_error(str(exc), status=502)

    @app.post("/api/projects")
    def api_add_project():
        payload = request.json if request.is_json else {}
        name = _sanitize_text(payload.get("name"))
        raw_path = _sanitize_text(payload.get("path"))
        account_id = _sanitize_text(payload.get("account_id"))

        if not name:
            return _json_error("项目名不能为空。")
        if not raw_path:
            return _json_error("项目路径不能为空。")
        if not account_id:
            return _json_error("必须选择一个账号。")

        try:
            record = store.add_project(name=name, path=Path(raw_path), account_id=account_id)
            return jsonify({"ok": True, "project": record})
        except StorageError as exc:
            return _json_error(str(exc))

    @app.post("/api/system/pick-directory")
    def api_pick_directory():
        payload = request.json if request.is_json else {}
        raw_initial = _sanitize_text(payload.get("initial_path"))
        initial_path = Path(raw_initial).expanduser() if raw_initial else None
        try:
            selected = pick_existing_directory(initial_path=initial_path)
            if selected is None:
                return jsonify({"ok": True, "cancelled": True})
            return jsonify({"ok": True, "cancelled": False, "path": str(selected)})
        except CodexOpsError as exc:
            if "未找到 `zenity`" in str(exc):
                return _json_error("系统未安装 `zenity`，请手动输入项目路径。")
            return _json_error(str(exc))

    @app.get("/api/settings/ui")
    def api_get_ui_settings():
        return jsonify({"ok": True, "settings": store.get_ui_settings()})

    @app.put("/api/settings/ui")
    def api_update_ui_settings():
        payload = request.json if request.is_json else {}
        try:
            settings = store.update_ui_settings(
                {
                    "language": payload.get("language"),
                    "theme": payload.get("theme"),
                    "window_close_behavior": payload.get("window_close_behavior"),
                }
            )
            return jsonify({"ok": True, "settings": settings})
        except StorageError as exc:
            return _json_error(str(exc))

    @app.delete("/api/projects/<project_id>")
    def api_delete_project(project_id: str):
        try:
            removed = store.delete_project(project_id)
            return jsonify({"ok": True, "removed": removed})
        except StorageError as exc:
            return _json_error(str(exc))

    @app.put("/api/projects/<project_id>")
    def api_update_project(project_id: str):
        payload = request.json if request.is_json else {}
        name = _sanitize_text(payload.get("name"))
        raw_path = _sanitize_text(payload.get("path"))
        account_id = _sanitize_text(payload.get("account_id"))

        if not name:
            return _json_error("项目名不能为空。")
        if not raw_path:
            return _json_error("项目路径不能为空。")
        if not account_id:
            return _json_error("必须选择一个账号。")

        try:
            record = store.update_project(
                project_id=project_id,
                name=name,
                path=Path(raw_path),
                account_id=account_id,
            )
            return jsonify({"ok": True, "project": record})
        except StorageError as exc:
            message = str(exc)
            if "未找到要更新的项目" in message:
                return _json_error(message, status=404)
            if "已存在" in message:
                return _json_error(message, status=409)
            return _json_error(message)

    @app.post("/api/projects/<project_id>/open")
    def api_open_project(project_id: str):
        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        project_path = Path(project["path"])
        if not project_path.exists():
            return _json_error("项目路径不存在。")

        try:
            open_project_terminal(project_path=project_path, codex_home=Path(account["codex_home"]))
            store.touch_project_opened(project_id)
            store.touch_account_used(account["id"])
            return jsonify({"ok": True, "message": "已启动项目终端。"})
        except CodexOpsError as exc:
            return _json_error(str(exc))

    @app.get("/api/projects/<project_id>/sessions")
    def api_list_sessions(project_id: str):
        limit_raw = request.args.get("limit", "30")
        query = _sanitize_text(request.args.get("q"))
        date_from = _sanitize_text(request.args.get("date_from"))
        date_to = _sanitize_text(request.args.get("date_to"))
        try:
            limit = max(1, min(200, int(limit_raw)))
        except ValueError:
            limit = 30

        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        sessions = list_project_sessions(
            codex_home=Path(account["codex_home"]),
            project_path=Path(project["path"]),
            limit=limit,
            query=query,
            date_from=date_from,
            date_to=date_to,
        )
        return jsonify({"ok": True, "sessions": sessions})

    @app.post("/api/projects/<project_id>/sessions/open")
    def api_open_session(project_id: str):
        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        payload = request.json if request.is_json else {}
        session_id = _sanitize_text(payload.get("session_id"))
        if not session_id:
            return _json_error("session_id 不能为空。")

        try:
            open_project_terminal(
                project_path=Path(project["path"]),
                codex_home=Path(account["codex_home"]),
                session_id=session_id,
            )
            store.touch_project_opened(project_id)
            store.touch_account_used(account["id"])
            return jsonify({"ok": True, "message": "已打开历史会话。"})
        except CodexOpsError as exc:
            return _json_error(str(exc))

    @app.post("/api/projects/<project_id>/sessions/delete-plan")
    def api_delete_session_plan(project_id: str):
        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        payload = request.json if request.is_json else {}
        session_id = _sanitize_text(payload.get("session_id"))
        if not session_id:
            return _json_error("session_id 不能为空。")

        try:
            plan = plan_project_session_deletion(
                codex_home=Path(account["codex_home"]),
                project_path=Path(project["path"]),
                session_id=session_id,
            )
            return jsonify({"ok": True, "plan": plan})
        except CodexOpsError as exc:
            message = str(exc)
            status = 404 if "未找到指定会话" in message else 400
            return _json_error(message, status=status)

    @app.get("/api/projects/<project_id>/sessions/preview")
    def api_session_preview(project_id: str):
        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        session_id = _sanitize_text(request.args.get("session_id"))
        if not session_id:
            return _json_error("session_id 不能为空。")

        try:
            preview = get_project_session_preview(
                codex_home=Path(account["codex_home"]),
                project_path=Path(project["path"]),
                session_id=session_id,
            )
            return jsonify({"ok": True, "preview": preview})
        except CodexOpsError as exc:
            message = str(exc)
            status = 404 if "未找到指定会话" in message else 400
            return _json_error(message, status=status)

    @app.post("/api/projects/<project_id>/sessions/delete")
    def api_delete_session(project_id: str):
        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        payload = request.json if request.is_json else {}
        session_id = _sanitize_text(payload.get("session_id"))
        if not session_id:
            return _json_error("session_id 不能为空。")
        soft_delete = _to_bool(payload.get("soft_delete") if isinstance(payload, dict) else None, True)

        try:
            result = delete_project_session_files(
                codex_home=Path(account["codex_home"]),
                project_path=Path(project["path"]),
                session_id=session_id,
                soft_delete=soft_delete,
            )
            return jsonify(
                {
                    "ok": True,
                    **result,
                    "message": (
                        f"已删除会话（{result['mode']}，清理 {result['removed_files']} 个文件）。"
                    ),
                }
            )
        except CodexOpsError as exc:
            message = str(exc)
            status = 404 if "未找到指定会话" in message else 400
            return _json_error(message, status=status)

    @app.get("/api/projects/<project_id>/trash/sessions")
    def api_list_trashed_sessions(project_id: str):
        limit_raw = request.args.get("limit", "30")
        query = _sanitize_text(request.args.get("q"))
        try:
            limit = max(1, min(200, int(limit_raw)))
        except ValueError:
            limit = 30

        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        sessions = list_project_trashed_sessions(
            codex_home=Path(account["codex_home"]),
            project_path=Path(project["path"]),
            limit=limit,
            query=query,
        )
        return jsonify({"ok": True, "sessions": sessions})

    @app.post("/api/projects/<project_id>/trash/sessions/restore")
    def api_restore_trashed_session(project_id: str):
        project = store.find_project(project_id)
        if not project:
            return _json_error("未找到项目。", status=404)
        account = store.find_account(project["account_id"])
        if not account:
            return _json_error("项目绑定账号不存在。", status=404)

        payload = request.json if request.is_json else {}
        session_id = _sanitize_text(payload.get("session_id"))
        if not session_id:
            return _json_error("session_id 不能为空。")
        open_after_restore = _to_bool(
            payload.get("open_after_restore") if isinstance(payload, dict) else None,
            False,
        )

        try:
            result = restore_project_session_files(
                codex_home=Path(account["codex_home"]),
                project_path=Path(project["path"]),
                session_id=session_id,
            )
            if open_after_restore:
                open_project_terminal(
                    project_path=Path(project["path"]),
                    codex_home=Path(account["codex_home"]),
                    session_id=session_id,
                )
                store.touch_project_opened(project_id)
                store.touch_account_used(account["id"])
            return jsonify(
                {
                    "ok": True,
                    **result,
                    "opened": open_after_restore,
                    "message": (
                        "已恢复并打开会话。"
                        if open_after_restore
                        else f"已恢复会话（{result['restored_files']} 个文件）。"
                    ),
                }
            )
        except CodexOpsError as exc:
            message = str(exc)
            status = 404 if "未找到回收站中的指定会话" in message else 400
            return _json_error(message, status=status)

    @app.get("/api/health")
    def api_health():
        return jsonify(
            {
                "ok": True,
                "platform": os.uname().sysname if hasattr(os, "uname") else os.name,
                "data_root": str(store.paths.root),
            }
        )

    @app.get("/api/system/status")
    def api_system_status():
        return jsonify({"ok": True, "status": collect_system_status()})

    @app.get("/api/system/components/<component_key>/latest")
    def api_component_latest(component_key: str):
        try:
            latest = check_component_latest_version(component_key)
            return jsonify({"ok": True, "latest": latest})
        except CodexOpsError as exc:
            message = str(exc)
            status = 404 if "不支持的组件" in message else 502
            return _json_error(message, status=status)

    @app.post("/api/system/components/<component_key>/install")
    def api_component_install(component_key: str):
        try:
            result = launch_component_latest_install(component_key)
            return jsonify({"ok": True, **result})
        except CodexOpsError as exc:
            message = str(exc)
            status = 404 if "不支持的组件" in message else 502
            return _json_error(message, status=status)

    @app.get("/api/system/config-dir")
    def api_system_config_dir():
        return jsonify({"ok": True, "path": str(store.paths.root)})

    @app.post("/api/system/config-dir/open")
    def api_open_system_config_dir():
        try:
            opened_path = open_directory(store.paths.root)
            return jsonify({"ok": True, "path": str(opened_path)})
        except CodexOpsError as exc:
            return _json_error(str(exc))

    @app.get("/api/system/about")
    def api_system_about():
        uname = os.uname() if hasattr(os, "uname") else None
        return jsonify(
            {
                "ok": True,
                "about": {
                    "version": __version__,
                    "python_version": platform.python_version(),
                    "platform": f"{platform.system()} {platform.release()}",
                    "machine": platform.machine(),
                    "kernel": uname.release if uname else "",
                    "data_root": str(store.paths.root),
                },
                "status": collect_system_status(),
            }
        )

    @app.get("/api/system/self/latest")
    def api_system_self_latest():
        try:
            latest = check_self_latest_version(__version__)
            return jsonify({"ok": True, "latest": latest})
        except CodexOpsError as exc:
            return _json_error(str(exc), status=502)

    @app.post("/api/system/self/install")
    def api_system_self_install():
        try:
            result = launch_self_latest_install()
            return jsonify({"ok": True, **result})
        except CodexOpsError as exc:
            return _json_error(str(exc), status=502)

    @app.post("/api/system/open-trash")
    def api_open_trash():
        payload = request.json if request.is_json else {}
        account_id = _sanitize_text(payload.get("account_id"))

        if account_id:
            account = store.find_account(account_id)
        else:
            account = _pick_most_recent_account(store.list_accounts())

        if not account:
            return _json_error("当前没有可用账号，请先添加账号。")

        try:
            opened_path = open_account_trash(Path(account["codex_home"]))
            return jsonify(
                {
                    "ok": True,
                    "path": str(opened_path),
                    "account_id": account["id"],
                    "account_alias": account.get("alias"),
                }
            )
        except CodexOpsError as exc:
            return _json_error(str(exc))

    return app
