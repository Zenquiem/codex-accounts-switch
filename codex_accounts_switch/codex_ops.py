from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import select
import shlex
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


class CodexOpsError(Exception):
    """Raised when Codex command operations fail."""


_QUOTA_CACHE_TTL_SECONDS = 60.0
_QUOTA_CACHE: dict[str, dict[str, Any]] = {}
_BINARY_CACHE: dict[str, str | None] = {}
_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-9;]*[A-Za-z]")
_LOCAL_PROXY_CANDIDATE_PORTS = (7890, 20171, 1080, 8080)
_COMPONENT_SPECS: dict[str, dict[str, str]] = {
    "codex": {
        "binary": "codex",
        "manager": "npm",
        "package": "@openai/codex",
    },
    "gnome_terminal": {
        "binary": "gnome-terminal",
        "manager": "apt",
        "package": "gnome-terminal",
    },
    "zsh": {
        "binary": "zsh",
        "manager": "apt",
        "package": "zsh",
    },
    "bash": {
        "binary": "bash",
        "manager": "apt",
        "package": "bash",
    },
    "zenity": {
        "binary": "zenity",
        "manager": "apt",
        "package": "zenity",
    },
}
_VERSION_TOKEN_RE = re.compile(r"\d[0-9A-Za-z.+:~\-]*")
_APT_POLICY_TABLE_RE = re.compile(r"^\*{0,3}\s*([0-9][^\s]*)\s+\d+")
_REPO_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_DEFAULT_UPDATE_REPO = "Zenquiem/codex-accounts-switch"


def _is_executable_file(path: Path) -> bool:
    try:
        return path.exists() and path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False


def _resolve_binary(binary: str) -> str | None:
    cached = _BINARY_CACHE.get(binary)
    if cached:
        if _is_executable_file(Path(cached)):
            return cached
        _BINARY_CACHE.pop(binary, None)

    direct = shutil.which(binary)
    if direct:
        _BINARY_CACHE[binary] = direct
        return direct

    home = Path.home()
    candidates = [
        home / ".local" / "bin" / binary,
        home / ".npm-global" / "bin" / binary,
        home / ".npm" / "bin" / binary,
        home / ".yarn" / "bin" / binary,
        home / ".pnpm" / binary,
        Path("/usr/local/bin") / binary,
        Path("/usr/bin") / binary,
        Path("/snap/bin") / binary,
    ]
    for candidate in candidates:
        if _is_executable_file(candidate):
            resolved = str(candidate)
            _BINARY_CACHE[binary] = resolved
            return resolved

    npm_prefixes: list[str] = []
    npm_env_prefix = os.environ.get("NPM_CONFIG_PREFIX", "").strip()
    if npm_env_prefix:
        npm_prefixes.append(npm_env_prefix)
    npm_bin = shutil.which("npm")
    if npm_bin:
        try:
            completed = subprocess.run(
                [npm_bin, "config", "get", "prefix"],
                capture_output=True,
                text=True,
                timeout=6,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            completed = None
        if completed and completed.returncode == 0:
            output = (completed.stdout or "").strip()
            if output and output not in {"undefined", "null"}:
                npm_prefixes.append(output)

    for prefix in npm_prefixes:
        base = Path(prefix).expanduser()
        for candidate in (base / "bin" / binary, base / binary):
            if _is_executable_file(candidate):
                resolved = str(candidate)
                _BINARY_CACHE[binary] = resolved
                return resolved

    for shell_name in ("zsh", "bash"):
        shell_path = shutil.which(shell_name)
        if not shell_path:
            continue
        try:
            completed = subprocess.run(
                [shell_path, "-lc", f"command -v {shlex.quote(binary)}"],
                capture_output=True,
                text=True,
                timeout=6,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue

        if completed.returncode != 0:
            continue
        output = (completed.stdout or "").strip()
        if not output:
            continue
        first = output.splitlines()[0].strip()
        if not first:
            continue
        if first.startswith("/"):
            resolved = Path(first)
            if _is_executable_file(resolved):
                resolved_str = str(resolved)
                _BINARY_CACHE[binary] = resolved_str
                return resolved_str

    _BINARY_CACHE[binary] = None
    return None


def _require_binary(binary: str) -> str:
    resolved = _resolve_binary(binary)
    if not resolved:
        raise CodexOpsError(f"系统中未找到 `{binary}` 命令。")
    return resolved


def _build_env(codex_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    return env


def _guess_local_proxy_env() -> dict[str, str]:
    for port in _LOCAL_PROXY_CANDIDATE_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except OSError:
            return {}
        sock.settimeout(0.25)
        try:
            sock.connect(("127.0.0.1", port))
        except OSError:
            continue
        finally:
            sock.close()

        http_proxy = f"http://127.0.0.1:{port}/"
        socks_proxy = f"socks://127.0.0.1:{port}/"
        return {
            "HTTP_PROXY": http_proxy,
            "HTTPS_PROXY": http_proxy,
            "ALL_PROXY": socks_proxy,
            "NO_PROXY": "localhost,127.0.0.0/8,::1",
            "http_proxy": http_proxy,
            "https_proxy": http_proxy,
            "all_proxy": socks_proxy,
            "no_proxy": "localhost,127.0.0.0/8,::1",
        }
    return {}


def _binary_status(binary: str) -> dict[str, Any]:
    path = _resolve_binary(binary)
    return {
        "binary": binary,
        "available": bool(path),
        "path": path,
    }


def _component_key(component_key: str) -> str:
    key = str(component_key or "").strip().lower()
    if key not in _COMPONENT_SPECS:
        raise CodexOpsError(f"不支持的组件 `{component_key}`。")
    return key


def _component_display_name(component_key: str) -> str:
    labels = {
        "codex": "Codex CLI",
        "gnome_terminal": "gnome-terminal",
        "zsh": "zsh",
        "bash": "bash",
        "zenity": "zenity",
    }
    return labels.get(component_key, component_key)


def _extract_version_token(text: str) -> str | None:
    cleaned = _clean_line_value(text)
    if not cleaned:
        return None
    match = _VERSION_TOKEN_RE.search(cleaned)
    if not match:
        return None
    return match.group(0).strip()


def _is_none_version(value: str | None) -> bool:
    if value is None:
        return True
    normalized = str(value).strip().lower()
    return not normalized or normalized == "(none)"


def _run_text_command(command: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        cmd_text = " ".join(shlex.quote(part) for part in command)
        raise CodexOpsError(f"命令执行超时：{cmd_text}") from exc
    except OSError as exc:
        cmd_text = " ".join(shlex.quote(part) for part in command)
        raise CodexOpsError(f"命令执行失败：{cmd_text}（{exc}）") from exc


def _parse_apt_policy_versions(output: str) -> tuple[str | None, str | None]:
    installed = None
    candidate = None
    in_version_table = False
    for line in output.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()

        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key_norm = key.strip().lower()
            parsed_value = value.strip() or None
            if any(token in key_norm for token in ("installed", "已安装", "installiert", "instalado")):
                installed = parsed_value
            elif any(token in key_norm for token in ("candidate", "候选", "kandidat", "candidato")):
                candidate = parsed_value

        if lowered.startswith("version table") or stripped.startswith("版本列表"):
            in_version_table = True
            continue

        if not in_version_table:
            continue

        matched = _APT_POLICY_TABLE_RE.match(stripped)
        if matched:
            table_version = matched.group(1).strip()
            if table_version and (_is_none_version(candidate) or not candidate):
                candidate = table_version
            if table_version and "***" in stripped and (_is_none_version(installed) or not installed):
                installed = table_version
    return installed, candidate


def _parse_apt_madison_latest(output: str) -> str | None:
    for line in output.splitlines():
        if "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2:
            continue
        version = _extract_version_token(parts[1]) or _clean_line_value(parts[1])
        if version:
            return version
    return None


def _parse_github_repo_slug(remote_url: str) -> str | None:
    raw = _clean_line_value(remote_url)
    if not raw or "github.com" not in raw:
        return None

    path = ""
    if raw.startswith("git@github.com:"):
        path = raw.split(":", 1)[1]
    elif "github.com/" in raw:
        path = raw.split("github.com/", 1)[1]
    elif "github.com:" in raw:
        path = raw.split("github.com:", 1)[1]
    else:
        return None

    normalized = path.split("?", 1)[0].split("#", 1)[0].strip().strip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    parts = [part for part in normalized.split("/") if part]
    if len(parts) < 2:
        return None
    slug = f"{parts[0]}/{parts[1]}"
    if not _REPO_SLUG_RE.match(slug):
        return None
    return slug


def _resolve_update_repo_slug() -> str | None:
    env_repo = _clean_line_value(os.environ.get("CAS_UPDATE_REPO", ""))
    if env_repo and _REPO_SLUG_RE.match(env_repo):
        return env_repo

    git_bin = _resolve_binary("git")
    if git_bin:
        project_root = Path(__file__).resolve().parent.parent
        try:
            completed = subprocess.run(
                [git_bin, "-C", str(project_root), "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                timeout=6,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            completed = None
        if completed and completed.returncode == 0:
            parsed = _parse_github_repo_slug(completed.stdout or "")
            if parsed:
                return parsed

    return _DEFAULT_UPDATE_REPO if _REPO_SLUG_RE.match(_DEFAULT_UPDATE_REPO) else None


def _open_url_with_desktop(url: str) -> None:
    target = _clean_line_value(url)
    if not target:
        raise CodexOpsError("无效的链接地址。")
    if shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", target], start_new_session=True)
        return
    if shutil.which("gio"):
        subprocess.Popen(["gio", "open", target], start_new_session=True)
        return
    raise CodexOpsError("系统中未找到可用的链接打开器（`xdg-open`/`gio`）。")


def _fetch_json(url: str, timeout: int = 10) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-accounts-switch",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def _normalize_version_text(raw_version: str | None) -> str | None:
    cleaned = _clean_line_value(raw_version or "")
    if not cleaned:
        return None
    if cleaned.startswith(("v", "V")) and len(cleaned) > 1 and cleaned[1].isdigit():
        cleaned = cleaned[1:]
    token = _extract_version_token(cleaned)
    if token:
        return token.lstrip("vV")
    return cleaned


def _version_int_parts(raw_version: str | None) -> tuple[int, ...]:
    normalized = _normalize_version_text(raw_version)
    if not normalized:
        return ()
    numbers = re.findall(r"\d+", normalized)
    if not numbers:
        return ()
    return tuple(int(part) for part in numbers[:8])


def _compare_versions(left: str | None, right: str | None) -> int:
    left_parts = _version_int_parts(left)
    right_parts = _version_int_parts(right)
    max_len = max(len(left_parts), len(right_parts), 1)
    left_padded = left_parts + (0,) * (max_len - len(left_parts))
    right_padded = right_parts + (0,) * (max_len - len(right_parts))
    if left_padded < right_padded:
        return -1
    if left_padded > right_padded:
        return 1
    return 0


def check_self_latest_version(current_version: str) -> dict[str, Any]:
    repo_slug = _resolve_update_repo_slug()
    if not repo_slug:
        raise CodexOpsError("未配置版本检测仓库。")

    api_base = f"https://api.github.com/repos/{repo_slug}"
    latest_tag = None
    source = ""
    release_url = None

    try:
        release_payload = _fetch_json(f"{api_base}/releases/latest", timeout=12)
        if isinstance(release_payload, dict):
            latest_tag = _clean_line_value(str(release_payload.get("tag_name") or ""))
            release_url = _clean_line_value(str(release_payload.get("html_url") or "")) or None
            source = "github_release"
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise CodexOpsError(f"检查工具最新版失败：HTTP {exc.code}。") from exc
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        raise CodexOpsError(f"检查工具最新版失败：{exc}") from exc

    if not latest_tag:
        try:
            tags_payload = _fetch_json(f"{api_base}/tags?per_page=1", timeout=12)
        except urllib.error.HTTPError as exc:
            raise CodexOpsError(f"检查工具最新版失败：HTTP {exc.code}。") from exc
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            raise CodexOpsError(f"检查工具最新版失败：{exc}") from exc

        if isinstance(tags_payload, list) and tags_payload:
            first = tags_payload[0]
            if isinstance(first, dict):
                latest_tag = _clean_line_value(str(first.get("name") or ""))
                source = "github_tags"

    latest_version = _normalize_version_text(latest_tag)
    current_normalized = _normalize_version_text(current_version) or str(current_version).strip()
    if not latest_version:
        raise CodexOpsError("检查工具最新版失败：未获取到有效版本号。")

    comparison = _compare_versions(current_normalized, latest_version)
    upgradable = comparison < 0

    return {
        "current_version": current_normalized,
        "latest_version": latest_version,
        "upgradable": bool(upgradable),
        "repo": repo_slug,
        "source": source or "unknown",
        "release_url": release_url,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def launch_self_latest_install(current_version: str | None = None) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parent.parent
    repo_slug = _resolve_update_repo_slug()
    if not repo_slug:
        raise CodexOpsError("未配置版本检测仓库，无法打开最新版下载页。")
    release_url = f"https://github.com/{repo_slug}/releases/latest"

    if not (project_root / ".git").exists():
        _open_url_with_desktop(release_url)
        return {
            "mode": "release_page",
            "release_url": release_url,
            "message": "当前为发布包模式，已打开最新版下载页面。",
        }

    terminal_bin = _require_binary("gnome-terminal")
    git_bin = _require_binary("git")
    project_root_quoted = shlex.quote(str(project_root))
    git_bin_quoted = shlex.quote(git_bin)

    commands = [
        f"cd {project_root_quoted}",
        f"{git_bin_quoted} pull --ff-only",
    ]

    venv_pip = project_root / ".venv" / "bin" / "pip"
    if _is_executable_file(venv_pip):
        commands.append(f"{shlex.quote(str(venv_pip))} install -r requirements.txt")
    else:
        commands.append(
            "if command -v pip3 >/dev/null 2>&1; then "
            "pip3 install -r requirements.txt; "
            "elif command -v pip >/dev/null 2>&1; then "
            "pip install -r requirements.txt; "
            "fi"
        )

    desktop_install_script = project_root / "scripts" / "install_desktop_entry.sh"
    if desktop_install_script.exists() and desktop_install_script.is_file():
        commands.append(f"bash {shlex.quote(str(desktop_install_script))}")

    install_command = " && ".join(commands)
    shell_command = (
        f"{install_command}; "
        "status=$?; "
        "echo; "
        "if [ $status -eq 0 ]; then "
        "echo '工具更新完成。请重启应用以生效。按 Enter 关闭窗口。'; "
        "else "
        "echo '工具更新失败，请检查输出后重试。按 Enter 关闭窗口。'; "
        "fi; "
        "read -r _; "
        "exit $status"
    )

    subprocess.Popen(
        [terminal_bin, "--", "bash", "-lc", shell_command],
        start_new_session=True,
    )

    return {
        "mode": "git_pull",
        "command": install_command,
        "message": "已打开工具更新终端。",
        "release_url": release_url,
    }


def _build_install_command_for_component(component_key: str) -> str:
    key = _component_key(component_key)
    spec = _COMPONENT_SPECS[key]
    manager = spec["manager"]
    package = spec["package"]

    if manager == "npm":
        npm_bin = _require_binary("npm")
        npm_bin_quoted = shlex.quote(npm_bin)
        package_quoted = shlex.quote(package + "@latest")
        return (
            f"pkg={package_quoted}; "
            f"npm_bin={npm_bin_quoted}; "
            "prefix=\"$($npm_bin config get prefix 2>/dev/null || true)\"; "
            "prefix=\"${prefix%%$'\\r'}\"; "
            "prefix=\"${prefix%%$'\\n'}\"; "
            "if [ -n \"$prefix\" ] && [ \"$prefix\" != \"undefined\" ] && [ \"$prefix\" != \"null\" ] && [ -w \"$prefix\" ]; then "
            "$npm_bin install -g \"$pkg\"; "
            "elif command -v sudo >/dev/null 2>&1; then "
            "sudo $npm_bin install -g \"$pkg\"; "
            "else "
            "echo 'npm 全局目录不可写，且系统未安装 sudo，无法自动安装。' >&2; "
            "echo '建议先配置 npm 用户级 prefix（例如 ~/.npm-global）后重试。' >&2; "
            "exit 1; "
            "fi"
        )

    if manager == "apt":
        apt_get_bin = _require_binary("apt-get")
        apt_get_quoted = shlex.quote(apt_get_bin)
        package_quoted = shlex.quote(package)
        return (
            f"sudo {apt_get_quoted} update && "
            f"sudo {apt_get_quoted} install -y {package_quoted}"
        )

    raise CodexOpsError(f"组件 `{component_key}` 暂不支持自动安装。")


def check_component_latest_version(component_key: str) -> dict[str, Any]:
    key = _component_key(component_key)
    spec = _COMPONENT_SPECS[key]
    manager = spec["manager"]
    package = spec["package"]
    display_name = _component_display_name(key)

    current_version: str | None = None
    latest_version: str | None = None
    message = ""

    if manager == "npm":
        codex_path = _resolve_binary(spec["binary"])
        if codex_path:
            current_raw, _ = _run_binary_version(codex_path)
            if current_raw:
                current_version = _extract_version_token(current_raw) or current_raw

        npm_bin = _require_binary("npm")
        completed = _run_text_command([npm_bin, "view", package, "version"], timeout=25)
        stdout = _clean_line_value(completed.stdout or "")
        stderr = _clean_line_value(completed.stderr or "")
        if completed.returncode != 0:
            error = stderr or stdout or "未知错误。"
            raise CodexOpsError(f"检查 {display_name} 最新版失败：{error}")

        latest_version = _extract_version_token(stdout) or stdout
        if not latest_version:
            raise CodexOpsError(f"检查 {display_name} 最新版失败：未返回版本信息。")

    elif manager == "apt":
        apt_cache_bin = _require_binary("apt-cache")
        completed = _run_text_command([apt_cache_bin, "policy", package], timeout=20)
        stdout = completed.stdout or ""
        stderr = _clean_line_value(completed.stderr or "")
        if completed.returncode != 0:
            error = stderr or _clean_line_value(stdout) or "未知错误。"
            raise CodexOpsError(f"检查 {display_name} 最新版失败：{error}")

        installed, candidate = _parse_apt_policy_versions(stdout)
        if not _is_none_version(installed):
            current_version = str(installed)
        if not _is_none_version(candidate):
            latest_version = str(candidate)

        # Fallback: apt-cache policy output can vary by locale/format.
        if not latest_version:
            madison = _run_text_command([apt_cache_bin, "madison", package], timeout=20)
            if madison.returncode == 0:
                latest_version = _parse_apt_madison_latest(madison.stdout or "")

        # Fallback: derive current version from binary if policy did not expose it.
        if not current_version:
            binary_path = _resolve_binary(spec["binary"])
            if binary_path:
                current_raw, _ = _run_binary_version(binary_path)
                if current_raw:
                    current_version = _extract_version_token(current_raw) or current_raw

        if not current_version and not latest_version:
            raise CodexOpsError(f"检查 {display_name} 最新版失败：未解析到版本信息。")

    else:
        raise CodexOpsError(f"组件 `{component_key}` 暂不支持版本检查。")

    if current_version and latest_version:
        upgradable = current_version != latest_version
    elif latest_version and not current_version:
        upgradable = True
    else:
        upgradable = False

    if upgradable:
        message = f"{display_name} 可升级。"
    else:
        message = f"{display_name} 已是最新。"

    install_supported = bool(_resolve_binary("gnome-terminal"))
    if manager == "npm":
        install_supported = install_supported and bool(_resolve_binary("npm"))
    elif manager == "apt":
        install_supported = install_supported and bool(_resolve_binary("apt-get"))

    return {
        "component": key,
        "display_name": display_name,
        "manager": manager,
        "package": package,
        "current_version": current_version,
        "latest_version": latest_version,
        "upgradable": bool(upgradable),
        "install_supported": bool(install_supported),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "message": message,
    }


def launch_component_latest_install(component_key: str) -> dict[str, Any]:
    key = _component_key(component_key)
    display_name = _component_display_name(key)
    terminal_bin = _require_binary("gnome-terminal")
    install_command = _build_install_command_for_component(key)

    shell_command = (
        f"{install_command}; "
        "status=$?; "
        "echo; "
        "if [ $status -eq 0 ]; then "
        "echo '安装命令执行完成。按 Enter 关闭窗口。'; "
        "else "
        "echo '安装命令执行失败，请检查输出后重试。按 Enter 关闭窗口。'; "
        "fi; "
        "read -r _; "
        "exit $status"
    )

    subprocess.Popen(
        [terminal_bin, "--", "bash", "-lc", shell_command],
        start_new_session=True,
    )

    return {
        "component": key,
        "display_name": display_name,
        "command": install_command,
        "message": f"已打开 {display_name} 的安装终端。",
    }


def _run_binary_version(binary: str) -> tuple[str | None, str | None]:
    result = subprocess.run(
        [binary, "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    output = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return None, output or "命令执行失败。"
    if not output:
        return None, "未返回版本信息。"
    return output.splitlines()[0].strip(), None


def _open_directory_with_desktop(target_dir: Path) -> None:
    if shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", str(target_dir)], start_new_session=True)
        return
    if shutil.which("gio"):
        subprocess.Popen(["gio", "open", str(target_dir)], start_new_session=True)
        return
    raise CodexOpsError("系统中未找到可用的目录打开器（`xdg-open`/`gio`）。")


def open_account_trash(codex_home: Path) -> Path:
    trash_dir = (codex_home / "trash" / "sessions").resolve()
    try:
        trash_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CodexOpsError("创建回收站目录失败。") from exc
    _open_directory_with_desktop(trash_dir)
    return trash_dir


def open_directory(target_dir: Path) -> Path:
    resolved = target_dir.expanduser().resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise CodexOpsError("目录不存在或不可访问。")
    _open_directory_with_desktop(resolved)
    return resolved


def collect_system_status() -> dict[str, Any]:
    codex = _binary_status("codex")
    gnome_terminal = _binary_status("gnome-terminal")
    zsh = _binary_status("zsh")
    bash = _binary_status("bash")
    zenity = _binary_status("zenity")

    codex_version = None
    codex_error = None
    if codex["available"]:
        codex_version, codex_error = _run_binary_version(str(codex["path"]))

    codex_ok = bool(codex["available"] and codex_version)
    terminal_ok = bool(gnome_terminal["available"])
    shell_ok = bool(zsh["available"] or bash["available"])
    overall_ok = bool(codex_ok and terminal_ok and shell_ok)

    return {
        "overall_ok": overall_ok,
        "components": {
            "codex": {
                **codex,
                "version": codex_version,
                "error": codex_error,
                "ok": codex_ok,
            },
            "gnome_terminal": {
                **gnome_terminal,
                "ok": terminal_ok,
            },
            "zsh": {
                **zsh,
                "ok": bool(zsh["available"]),
            },
            "bash": {
                **bash,
                "ok": bool(bash["available"]),
            },
            "zenity": {
                **zenity,
                "ok": bool(zenity["available"]),
            },
        },
    }


def read_oauth_account_fingerprint(codex_home: Path) -> str:
    auth_path = codex_home / "auth.json"
    try:
        with auth_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise CodexOpsError("未找到登录凭据文件，无法识别 OAuth 账号。") from exc
    except OSError as exc:
        raise CodexOpsError("读取登录凭据文件失败，无法识别 OAuth 账号。") from exc
    except json.JSONDecodeError as exc:
        raise CodexOpsError("登录凭据文件格式无效，无法识别 OAuth 账号。") from exc

    account_id = payload.get("tokens", {}).get("account_id")
    if not isinstance(account_id, str) or not account_id.strip():
        raise CodexOpsError("未检测到 OAuth 账号标识，无法完成去重。")

    normalized = account_id.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def check_login_status(codex_home: Path) -> tuple[bool, str]:
    codex_bin = _require_binary("codex")
    result = subprocess.run(
        [codex_bin, "login", "status"],
        env=_build_env(codex_home),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    message = stdout or stderr or "未返回状态信息。"
    logged_in = result.returncode == 0 and "logged in" in message.lower()
    return logged_in, message


def run_oauth_login_in_terminal(codex_home: Path) -> tuple[bool, str]:
    codex_bin = _require_binary("codex")
    terminal_bin = _require_binary("gnome-terminal")

    codex_home_quoted = shlex.quote(str(codex_home))
    codex_bin_quoted = shlex.quote(codex_bin)
    login_cmd = (
        f"export CODEX_HOME={codex_home_quoted}; "
        f"{codex_bin_quoted} login; "
        "status=$?; "
        "if [ $status -ne 0 ]; then "
        "echo; echo 'codex login 执行失败。按 Enter 关闭窗口。'; read -r _; "
        "fi; "
        "exit $status"
    )
    completed = subprocess.run(
        [terminal_bin, "--wait", "--", "bash", "-lc", login_cmd],
        check=False,
    )
    if completed.returncode != 0:
        return False, "登录窗口关闭或登录命令失败。"

    return check_login_status(codex_home)


def pick_existing_directory(initial_path: Path | None = None) -> Path | None:
    zenity_bin = _require_binary("zenity")
    command = [
        zenity_bin,
        "--file-selection",
        "--directory",
        "--title=选择项目目录",
    ]
    if initial_path and initial_path.exists() and initial_path.is_dir():
        command.extend(["--filename", f"{str(initial_path)}/"])

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 1:
        return None
    if completed.returncode != 0:
        message = (completed.stderr or "").strip() or "未知错误。"
        raise CodexOpsError(f"目录选择器执行失败：{message}")

    selected = (completed.stdout or "").strip()
    if not selected:
        return None

    selected_path = Path(selected).expanduser()
    if not selected_path.exists() or not selected_path.is_dir():
        raise CodexOpsError("目录选择器返回了无效目录。")
    return selected_path.resolve()


def _pick_shell() -> str:
    if shutil.which("zsh"):
        return "zsh"
    return "bash"


def open_project_terminal(project_path: Path, codex_home: Path, session_id: str | None = None) -> None:
    codex_bin = _require_binary("codex")
    terminal_bin = _require_binary("gnome-terminal")
    shell_name = _pick_shell()

    project_quoted = shlex.quote(str(project_path))
    codex_home_quoted = shlex.quote(str(codex_home))
    codex_bin_quoted = shlex.quote(codex_bin)
    if session_id:
        session_quoted = shlex.quote(session_id)
        codex_command = f"{codex_bin_quoted} resume {session_quoted} -C {project_quoted}"
    else:
        codex_command = f"{codex_bin_quoted} -C {project_quoted}"

    shell_command = f"export CODEX_HOME={codex_home_quoted}; exec {codex_command}"
    subprocess.Popen(
        [
            terminal_bin,
            "--working-directory",
            str(project_path),
            "--",
            shell_name,
            "-lc",
            shell_command,
        ],
        start_new_session=True,
    )


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _strip_ansi(value: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", value)


def _compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_line_value(value: str) -> str:
    cleaned = _compact_whitespace(_strip_ansi(value))
    return cleaned.strip(" |,，;；")


def _quota_entry_has_signal(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False

    used = _clean_line_value(str(entry.get("used") or ""))
    limit = _clean_line_value(str(entry.get("limit") or ""))
    pct = _clean_line_value(str(entry.get("percent_used") or ""))
    if pct:
        return True
    if used and limit:
        return True

    # Fallback for status formats that only expose remaining/reset.
    line = _clean_line_value(str(entry.get("line") or ""))
    remaining = _clean_line_value(str(entry.get("remaining") or ""))
    reset = _clean_line_value(str(entry.get("reset") or ""))
    if len(line) > 180:
        return False
    if remaining and reset:
        return True
    return False


def _parsed_quota_has_signal(parsed: Any) -> bool:
    if not isinstance(parsed, dict):
        return False
    return _quota_entry_has_signal(parsed.get("five_hour")) or _quota_entry_has_signal(
        parsed.get("weekly")
    )


def _quota_raw_text_for_payload(raw_text: str, parsed: Any) -> str:
    lines: list[str] = []
    if isinstance(parsed, dict):
        for key in ("five_hour", "weekly"):
            entry = parsed.get(key)
            if not isinstance(entry, dict):
                continue
            line = _clean_line_value(str(entry.get("line") or ""))
            if not line:
                continue
            if line in lines:
                continue
            lines.append(line)
    if lines:
        return "\n".join(lines)

    compact = _clean_line_value(raw_text)
    if len(compact) > 480:
        return f"{compact[:480]}..."
    return compact


def _coerce_positive_int(value: Any) -> int | None:
    try:
        parsed = int(float(str(value)))
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _format_reset_timestamp_utc(epoch_seconds: Any) -> str | None:
    parsed = _coerce_positive_int(epoch_seconds)
    if parsed is None:
        return None
    try:
        dt = datetime.fromtimestamp(parsed, tz=timezone.utc).astimezone()
    except (OverflowError, OSError, ValueError):
        return None
    return dt.strftime("%Y-%m-%d %H:%M")


def _build_quota_entry_from_window(raw_window: Any, label: str) -> tuple[dict[str, Any] | None, int | None]:
    if not isinstance(raw_window, dict):
        return None, None

    raw_percent = raw_window.get("usedPercent", raw_window.get("used_percent"))
    if raw_percent is None:
        return None, None
    try:
        percent = int(round(float(str(raw_percent))))
    except (TypeError, ValueError):
        return None, None
    percent = max(0, min(100, percent))

    window_mins = _coerce_positive_int(
        raw_window.get("windowDurationMins", raw_window.get("window_minutes"))
    )
    reset_at = _format_reset_timestamp_utc(raw_window.get("resetsAt", raw_window.get("resets_at")))
    remaining_pct = max(0, 100 - percent)

    details = [f"{label} used {percent}%"]
    if reset_at:
        details.append(f"reset {reset_at}")
    if window_mins:
        details.append(f"window {window_mins}m")

    entry: dict[str, Any] = {
        "line": " · ".join(details),
        "used": None,
        "limit": None,
        "percent_used": str(percent),
        "remaining": f"{remaining_pct}%",
        "reset": reset_at,
    }
    return entry, window_mins


def _map_rate_limits_snapshot_to_quota(snapshot: Any) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {"five_hour": None, "weekly": None}

    primary_entry, primary_mins = _build_quota_entry_from_window(snapshot.get("primary"), "primary")
    secondary_entry, secondary_mins = _build_quota_entry_from_window(
        snapshot.get("secondary"),
        "secondary",
    )
    candidates: list[tuple[dict[str, Any], int | None]] = []
    if primary_entry:
        candidates.append((primary_entry, primary_mins))
    if secondary_entry:
        candidates.append((secondary_entry, secondary_mins))
    if not candidates:
        return {"five_hour": None, "weekly": None}

    five_hour: dict[str, Any] | None = None
    weekly: dict[str, Any] | None = None

    if len(candidates) >= 2:
        with_mins = [item for item in candidates if item[1] is not None]
        if len(with_mins) >= 2:
            ordered = sorted(with_mins, key=lambda item: int(item[1] or 0))
            five_hour = ordered[0][0]
            weekly = ordered[-1][0]
        else:
            five_hour = candidates[0][0]
            weekly = candidates[1][0]
    else:
        only_entry, only_mins = candidates[0]
        if only_mins is not None and only_mins >= 24 * 60 * 3:
            weekly = only_entry
        else:
            five_hour = only_entry

    if five_hour:
        five_hour["line"] = _clean_line_value(
            str(five_hour.get("line", "")).replace("primary", "5h").replace("secondary", "5h")
        )
    if weekly:
        weekly["line"] = _clean_line_value(
            str(weekly.get("line", "")).replace("primary", "weekly").replace("secondary", "weekly")
        )

    return {
        "five_hour": five_hour,
        "weekly": weekly,
    }


def _run_quota_probe_app_server(
    codex_home: Path,
    codex_bin: str,
    timeout_sec: int = 25,
    override_network_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    launch_env = _build_env(codex_home)
    if override_network_env:
        launch_env.update(override_network_env)

    try:
        process = subprocess.Popen(
            [codex_bin, "app-server"],
            env=launch_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except OSError as exc:
        return {
            "parsed": {"five_hour": None, "weekly": None},
            "raw_text": "",
            "error": f"无法获取额度：启动 Codex app-server 失败（{exc}）。",
        }

    init_id = "cas-init"
    quota_id = "cas-quota"
    responses: dict[str, Any] = {}
    stderr_lines: list[str] = []

    try:
        requests = [
            {
                "jsonrpc": "2.0",
                "id": init_id,
                "method": "initialize",
                "params": {
                    "clientInfo": {"name": "cas-quota", "version": "1.0.0"},
                    "capabilities": {},
                },
            },
            {
                "jsonrpc": "2.0",
                "id": quota_id,
                "method": "account/rateLimits/read",
                "params": None,
            },
        ]
        for request in requests:
            if process.stdin is None:
                raise BrokenPipeError("stdin not available")
            process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
            process.stdin.flush()
    except (BrokenPipeError, OSError) as exc:
        process.kill()
        return {
            "parsed": {"five_hour": None, "weekly": None},
            "raw_text": "",
            "error": f"无法获取额度：app-server 通信失败（{exc}）。",
        }

    start = time.monotonic()
    try:
        while time.monotonic() - start < timeout_sec:
            streams: list[Any] = []
            if process.stdout:
                streams.append(process.stdout)
            if process.stderr:
                streams.append(process.stderr)
            if not streams:
                break

            ready, _, _ = select.select(streams, [], [], 0.25)
            if not ready:
                if process.poll() is not None:
                    break
                continue

            for stream in ready:
                line = stream.readline()
                if not line:
                    continue
                text = line.strip()
                if not text:
                    continue
                if stream is process.stderr:
                    cleaned = _clean_line_value(text)
                    if cleaned and not cleaned.startswith("WARNING:"):
                        stderr_lines.append(cleaned)
                    continue

                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                msg_id = str(payload.get("id", ""))
                if msg_id == init_id:
                    responses["init"] = payload
                elif msg_id == quota_id:
                    responses["quota"] = payload

            if "quota" in responses:
                break
    finally:
        process.terminate()
        try:
            process.wait(timeout=1.0)
        except (subprocess.TimeoutExpired, OSError):
            process.kill()

    quota_response = responses.get("quota")
    if not isinstance(quota_response, dict):
        detail = ""
        if stderr_lines:
            detail = stderr_lines[0]
        return {
            "parsed": {"five_hour": None, "weekly": None},
            "raw_text": "",
            "error": f"无法获取额度：app-server 未返回额度结果。{detail}".strip(),
        }

    if "error" in quota_response:
        error_obj = quota_response.get("error")
        message = ""
        code = None
        if isinstance(error_obj, dict):
            message = _clean_line_value(str(error_obj.get("message") or ""))
            code = error_obj.get("code")
        else:
            message = _clean_line_value(str(error_obj or ""))
        if not message:
            message = "app-server 返回未知错误。"
        lowered = message.lower()
        if "failed to fetch codex rate limits" in lowered:
            message = "Codex 额度接口请求失败，请检查网络连接或稍后重试。"
        elif "not logged in" in lowered or "login required" in lowered:
            message = "该账号未登录或登录态已失效，请重新登录后再试。"
        if (
            code == -32601
            or "method not found" in lowered
            or ("ratelimits/read" in lowered and "not found" in lowered)
        ):
            message = "当前 Codex 版本不支持额度查询接口，请升级 Codex 后重试。"
        return {
            "parsed": {"five_hour": None, "weekly": None},
            "raw_text": "",
            "error": f"无法获取额度：{message}",
        }

    result = quota_response.get("result")
    rate_limits = None
    if isinstance(result, dict):
        rate_limits = result.get("rateLimits", result.get("rate_limits"))
    parsed = _map_rate_limits_snapshot_to_quota(rate_limits)
    raw_text = _quota_raw_text_for_payload("", parsed)
    if not _parsed_quota_has_signal(parsed):
        return {
            "parsed": parsed,
            "raw_text": raw_text,
            "error": "无法获取额度：未从 app-server 响应中解析到可用额度信息。",
        }

    return {
        "parsed": parsed,
        "raw_text": raw_text,
        "error": None,
    }


def get_account_quota(codex_home: Path, force_refresh: bool = False) -> dict[str, Any]:
    codex_bin = _require_binary("codex")
    resolved_home = codex_home.expanduser().resolve()

    cache_key = str(resolved_home)
    now = time.monotonic()
    cached = _QUOTA_CACHE.get(cache_key)
    if cached and not force_refresh:
        cached_at = float(cached.get("cached_at", 0.0))
        if now - cached_at <= _QUOTA_CACHE_TTL_SECONDS:
            payload = copy.deepcopy(cached.get("payload", {}))
            payload["cached"] = True
            return payload

    def _build_payload(source: str, parsed: Any, raw_text: str) -> dict[str, Any]:
        return {
            "source": source,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "five_hour": parsed.get("five_hour") if isinstance(parsed, dict) else None,
            "weekly": parsed.get("weekly") if isinstance(parsed, dict) else None,
            "raw_text": _quota_raw_text_for_payload(raw_text, parsed),
            "cached": False,
        }

    app_probe = _run_quota_probe_app_server(resolved_home, codex_bin=codex_bin, timeout_sec=30)
    app_parsed = app_probe.get("parsed", {})
    app_raw = str(app_probe.get("raw_text", "") or "").strip()
    if _parsed_quota_has_signal(app_parsed):
        payload = _build_payload("app_server_rate_limits", app_parsed, app_raw)
        _QUOTA_CACHE[cache_key] = {"cached_at": now, "payload": copy.deepcopy(payload)}
        return payload

    app_error = _clean_line_value(str(app_probe.get("error", "") or ""))
    if "Codex 额度接口请求失败" in app_error:
        local_proxy_env = _guess_local_proxy_env()
        if local_proxy_env:
            retry_probe = _run_quota_probe_app_server(
                resolved_home,
                codex_bin=codex_bin,
                timeout_sec=30,
                override_network_env=local_proxy_env,
            )
            retry_parsed = retry_probe.get("parsed", {})
            retry_raw = str(retry_probe.get("raw_text", "") or "").strip()
            if _parsed_quota_has_signal(retry_parsed):
                payload = _build_payload(
                    "app_server_rate_limits_local_proxy",
                    retry_parsed,
                    retry_raw,
                )
                _QUOTA_CACHE[cache_key] = {"cached_at": now, "payload": copy.deepcopy(payload)}
                return payload
            retry_error = _clean_line_value(str(retry_probe.get("error", "") or ""))
            if retry_error:
                app_error = retry_error

    if app_error:
        raise CodexOpsError(app_error)
    raise CodexOpsError("无法获取额度：未从 app-server 响应中解析到可用额度信息。")


def _parse_timestamp(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _parse_timestamp_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_text_from_message_content(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") not in {"input_text", "text", "output_text"}:
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return "\n".join(parts).strip()


def _build_session_title(raw_text: str) -> str:
    text = raw_text.strip()
    if not text:
        return ""
    collapsed = re.sub(r"\s+", " ", text).strip()
    if not collapsed:
        return ""

    split_index = -1
    for marker in ("。", "！", "？", "!", "?"):
        idx = collapsed.find(marker)
        if idx != -1:
            split_index = idx
            break

    if split_index != -1:
        title = collapsed[: split_index + 1].strip()
    else:
        title = collapsed

    if len(title) > 72:
        title = f"{title[:72].rstrip()}..."
    return title


def _should_ignore_title_source(raw_text: str) -> bool:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return True
    first = lines[0].lower()
    prefixes = (
        "# agents.md instructions for",
        "<environment_context>",
        "<permissions instructions>",
        "<collaboration_mode>",
    )
    return any(first.startswith(prefix) for prefix in prefixes)


def _truncate_preview_text(raw_text: str, max_len: int = 180) -> str:
    collapsed = re.sub(r"\s+", " ", raw_text).strip()
    if len(collapsed) <= max_len:
        return collapsed
    return f"{collapsed[:max_len].rstrip()}..."


def _extract_session_meta(jsonl_path: Path) -> dict[str, Any] | None:
    meta: dict[str, Any] | None = None
    title: str | None = None
    preview_messages: list[dict[str, str]] = []
    try:
        with jsonl_path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= 1500:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                item_type = obj.get("type")
                if item_type == "session_meta" and meta is None:
                    payload = obj.get("payload", {})
                    meta = {
                        "session_id": payload.get("id"),
                        "timestamp": payload.get("timestamp"),
                        "cwd": payload.get("cwd"),
                        "model_provider": payload.get("model_provider"),
                        "file": str(jsonl_path),
                    }
                    if title:
                        meta["title"] = title
                    if preview_messages:
                        meta["preview_messages"] = preview_messages
                    continue

                if item_type != "response_item":
                    continue

                payload = obj.get("payload", {})
                if payload.get("type") != "message":
                    continue

                role = payload.get("role")
                if role not in {"user", "assistant"}:
                    continue

                raw_text = _extract_text_from_message_content(payload.get("content"))
                if not raw_text:
                    continue

                ignore_for_title = role == "user" and _should_ignore_title_source(raw_text)
                if role == "user" and not title and not ignore_for_title:
                    parsed_title = _build_session_title(raw_text)
                    if parsed_title:
                        title = parsed_title
                        if meta is not None:
                            meta["title"] = title

                if not (role == "user" and ignore_for_title):
                    if len(preview_messages) < 8:
                        preview_text = _truncate_preview_text(raw_text)
                        if preview_text:
                            preview_messages.append({"role": role, "text": preview_text})
                            if meta is not None:
                                meta["preview_messages"] = preview_messages

                if meta is not None and title and len(preview_messages) >= 8:
                    break
    except OSError:
        return None

    if meta is None:
        return None
    if title and not meta.get("title"):
        meta["title"] = title
    if preview_messages and not meta.get("preview_messages"):
        meta["preview_messages"] = preview_messages
    return meta


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _session_index_path(sessions_root: Path) -> Path:
    return sessions_root / ".session_index.v1.json"


def _load_session_index(index_path: Path) -> dict[str, Any]:
    default = {"version": 1, "files": {}}
    try:
        with index_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return default

    if not isinstance(payload, dict):
        return default
    files = payload.get("files")
    if not isinstance(files, dict):
        return default
    return {"version": 1, "files": files}


def _save_session_index(index_path: Path, payload: dict[str, Any]) -> None:
    tmp_path = index_path.with_suffix(index_path.suffix + ".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        tmp_path.replace(index_path)
    except OSError:
        return


def _scan_rollout_items(codex_home: Path) -> list[dict[str, Any]]:
    sessions_root = codex_home / "sessions"
    if not sessions_root.exists():
        return []

    index_path = _session_index_path(sessions_root)
    previous_index = _load_session_index(index_path)
    previous_files = previous_index.get("files", {})
    if not isinstance(previous_files, dict):
        previous_files = {}

    next_files: dict[str, Any] = {}
    changed = False
    items: list[dict[str, Any]] = []

    rollout_files: list[tuple[Path, int]] = []
    for path in sessions_root.rglob("rollout-*.jsonl"):
        try:
            stat = path.stat()
        except OSError:
            continue
        rollout_files.append((path, int(stat.st_mtime_ns)))
    rollout_files.sort(key=lambda item: item[1], reverse=True)

    for path, _ in rollout_files:
        try:
            stat = path.stat()
        except OSError:
            continue

        rel = str(path.relative_to(sessions_root))
        cached = previous_files.get(rel)
        meta: dict[str, Any] | None = None
        cache_hit = False
        if isinstance(cached, dict):
            cached_mtime = cached.get("mtime_ns")
            cached_size = cached.get("size")
            cached_meta = cached.get("meta")
            if (
                isinstance(cached_mtime, int)
                and isinstance(cached_size, int)
                and cached_mtime == stat.st_mtime_ns
                and cached_size == stat.st_size
            ):
                cache_hit = True
                if isinstance(cached_meta, dict):
                    meta = dict(cached_meta)
        if not cache_hit:
            changed = True
            meta = _extract_session_meta(path)

        next_files[rel] = {
            "mtime_ns": int(stat.st_mtime_ns),
            "size": int(stat.st_size),
            "meta": meta,
        }

        if meta:
            runtime_meta = dict(meta)
            runtime_meta["file"] = str(path)
            items.append(
                {
                    "path": path,
                    "mtime_ns": int(stat.st_mtime_ns),
                    "meta": runtime_meta,
                }
            )

    if set(previous_files.keys()) != set(next_files.keys()):
        changed = True
    if changed:
        _save_session_index(index_path, {"version": 1, "files": next_files})
    return items


def _find_project_session_items(
    codex_home: Path,
    project_path: Path,
    session_id: str,
) -> list[dict[str, Any]]:
    normalized_session = session_id.strip()
    if not normalized_session:
        raise CodexOpsError("session_id 不能为空。")

    sessions_root = codex_home / "sessions"
    if not sessions_root.exists():
        raise CodexOpsError("当前账号下没有历史会话目录。")

    target_path = os.path.realpath(str(project_path))
    matched: list[dict[str, Any]] = []
    for item in _scan_rollout_items(codex_home):
        meta = item.get("meta", {})
        if meta.get("session_id") != normalized_session:
            continue
        cwd = meta.get("cwd")
        if not cwd or os.path.realpath(str(cwd)) != target_path:
            continue
        matched.append(item)
    matched.sort(key=lambda item: int(item.get("mtime_ns", 0)), reverse=True)
    return matched


def _scan_trash_rollout_items(codex_home: Path) -> list[dict[str, Any]]:
    trash_root = codex_home / "trash" / "sessions"
    if not trash_root.exists():
        return []

    items: list[dict[str, Any]] = []
    for path in trash_root.rglob("rollout-*.jsonl"):
        try:
            stat = path.stat()
        except OSError:
            continue
        meta = _extract_session_meta(path)
        if not meta:
            continue

        try:
            rel = path.relative_to(trash_root)
        except ValueError:
            continue
        if len(rel.parts) < 2:
            continue

        restore_rel = Path(*rel.parts[1:])
        runtime_meta = dict(meta)
        runtime_meta["file"] = str(path)
        runtime_meta["trash_batch"] = rel.parts[0]
        runtime_meta["restore_rel"] = str(restore_rel)
        runtime_meta["deleted_at"] = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat()
        items.append(
            {
                "path": path,
                "mtime_ns": int(stat.st_mtime_ns),
                "meta": runtime_meta,
            }
        )
    items.sort(key=lambda item: int(item.get("mtime_ns", 0)), reverse=True)
    return items


def _find_project_trashed_items(
    codex_home: Path,
    project_path: Path,
    session_id: str,
) -> list[dict[str, Any]]:
    normalized_session = session_id.strip()
    if not normalized_session:
        raise CodexOpsError("session_id 不能为空。")

    target_path = os.path.realpath(str(project_path))
    matched: list[dict[str, Any]] = []
    for item in _scan_trash_rollout_items(codex_home):
        meta = item.get("meta", {})
        if meta.get("session_id") != normalized_session:
            continue
        cwd = meta.get("cwd")
        if not cwd or os.path.realpath(str(cwd)) != target_path:
            continue
        matched.append(item)
    matched.sort(key=lambda item: int(item.get("mtime_ns", 0)), reverse=True)
    return matched


def list_project_trashed_sessions(
    codex_home: Path,
    project_path: Path,
    limit: int = 30,
    query: str | None = None,
) -> list[dict[str, Any]]:
    query_norm = (query or "").strip().lower()
    target_path = os.path.realpath(str(project_path))
    sessions_by_id: dict[str, dict[str, Any]] = {}

    for item in _scan_trash_rollout_items(codex_home):
        meta = dict(item.get("meta", {}))
        session_id = str(meta.get("session_id", "")).strip()
        cwd = str(meta.get("cwd", "")).strip()
        if not session_id or not cwd:
            continue
        if os.path.realpath(cwd) != target_path:
            continue

        existing = sessions_by_id.get(session_id)
        if existing is None:
            sessions_by_id[session_id] = {
                "session_id": session_id,
                "title": meta.get("title") or session_id,
                "timestamp": meta.get("timestamp"),
                "deleted_at": meta.get("deleted_at"),
                "files_count": 1,
            }
            continue

        existing["files_count"] = int(existing.get("files_count", 0)) + 1
        if _parse_timestamp(meta.get("deleted_at")) > _parse_timestamp(existing.get("deleted_at")):
            existing["deleted_at"] = meta.get("deleted_at")
        if not existing.get("title") and meta.get("title"):
            existing["title"] = meta.get("title")

    sessions = list(sessions_by_id.values())
    if query_norm:
        sessions = [
            item
            for item in sessions
            if query_norm in str(item.get("session_id", "")).lower()
            or query_norm in str(item.get("title", "")).lower()
        ]
    sessions.sort(key=lambda item: _parse_timestamp(item.get("deleted_at")), reverse=True)
    return sessions[: max(1, limit)]


def list_project_sessions(
    codex_home: Path,
    project_path: Path,
    limit: int = 30,
    query: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    sessions_root = codex_home / "sessions"
    if not sessions_root.exists():
        return []

    query_norm = (query or "").strip().lower()
    from_date = _parse_date(date_from)
    to_date = _parse_date(date_to)
    need_full_scan = bool(query_norm or from_date or to_date)
    if from_date and to_date and from_date > to_date:
        from_date, to_date = to_date, from_date

    sessions_by_id: dict[str, dict[str, Any]] = {}
    target_path = os.path.realpath(str(project_path))
    for item in _scan_rollout_items(codex_home):
        meta = dict(item.get("meta", {}))
        if not meta:
            continue
        session_id = meta.get("session_id")
        cwd = meta.get("cwd")
        if not session_id or not cwd:
            continue
        if os.path.realpath(cwd) != target_path:
            continue

        existing = sessions_by_id.get(session_id)
        if existing is None:
            sessions_by_id[session_id] = meta
        else:
            current_ts = _parse_timestamp(meta.get("timestamp"))
            existing_ts = _parse_timestamp(existing.get("timestamp"))
            if current_ts >= existing_ts:
                if not meta.get("title") and existing.get("title"):
                    meta["title"] = existing.get("title")
                sessions_by_id[session_id] = meta
            elif not existing.get("title") and meta.get("title"):
                existing["title"] = meta.get("title")

        if not need_full_scan and len(sessions_by_id) >= max(1, limit):
            break

    sessions = list(sessions_by_id.values())
    if query_norm:
        sessions = [
            item
            for item in sessions
            if query_norm in str(item.get("session_id", "")).lower()
            or query_norm in str(item.get("title", "")).lower()
        ]

    if from_date or to_date:
        filtered: list[dict[str, Any]] = []
        for item in sessions:
            dt = _parse_timestamp_datetime(item.get("timestamp"))
            if dt is None:
                continue
            item_date = dt.date()
            if from_date and item_date < from_date:
                continue
            if to_date and item_date > to_date:
                continue
            filtered.append(item)
        sessions = filtered

    sessions.sort(key=lambda item: _parse_timestamp(item.get("timestamp")), reverse=True)
    for item in sessions:
        if not item.get("title"):
            item["title"] = item.get("session_id")
    sessions = sessions[: max(1, limit)]
    return sessions


def delete_project_session(codex_home: Path, project_path: Path, session_id: str) -> int:
    result = delete_project_session_files(
        codex_home=codex_home,
        project_path=project_path,
        session_id=session_id,
        soft_delete=False,
    )
    return int(result.get("removed_files", 0))


def plan_project_session_deletion(
    codex_home: Path,
    project_path: Path,
    session_id: str,
) -> dict[str, Any]:
    items = _find_project_session_items(codex_home, project_path, session_id)
    if not items:
        raise CodexOpsError("未找到指定会话。")

    sessions_root = codex_home / "sessions"
    files: list[str] = []
    for item in items:
        path = item["path"]
        try:
            files.append(str(path.relative_to(sessions_root)))
        except ValueError:
            files.append(str(path))

    meta = items[0].get("meta", {})
    return {
        "session_id": session_id.strip(),
        "title": meta.get("title") or session_id.strip(),
        "files_count": len(files),
        "files": files,
    }


def get_project_session_preview(
    codex_home: Path,
    project_path: Path,
    session_id: str,
    max_messages: int = 8,
) -> dict[str, Any]:
    items = _find_project_session_items(codex_home, project_path, session_id)
    if not items:
        raise CodexOpsError("未找到指定会话。")

    latest = items[0]
    meta = latest.get("meta", {})
    raw_messages = meta.get("preview_messages")
    preview_messages: list[dict[str, str]] = []
    if isinstance(raw_messages, list):
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip()
            text = str(item.get("text", "")).strip()
            if role not in {"user", "assistant"} or not text:
                continue
            preview_messages.append({"role": role, "text": text})
            if len(preview_messages) >= max(1, max_messages):
                break

    return {
        "session_id": session_id.strip(),
        "title": meta.get("title") or session_id.strip(),
        "timestamp": meta.get("timestamp"),
        "files_count": len(items),
        "messages": preview_messages,
    }


def delete_project_session_files(
    codex_home: Path,
    project_path: Path,
    session_id: str,
    soft_delete: bool = True,
) -> dict[str, Any]:
    items = _find_project_session_items(codex_home, project_path, session_id)
    if not items:
        raise CodexOpsError("未找到指定会话。")

    sessions_root = codex_home / "sessions"
    trash_dir: Path | None = None
    removed = 0
    for item in items:
        path = item["path"]
        try:
            if soft_delete:
                if trash_dir is None:
                    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
                    trash_dir = codex_home / "trash" / "sessions" / stamp
                try:
                    rel = path.relative_to(sessions_root)
                except ValueError:
                    rel = Path(path.name)
                target = trash_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target))
            else:
                path.unlink()
            removed += 1
        except FileNotFoundError:
            continue
        except OSError as exc:
            action = "移动到回收站" if soft_delete else "永久删除"
            raise CodexOpsError(f"{action}失败：{path}") from exc

    _scan_rollout_items(codex_home)
    return {
        "removed_files": removed,
        "mode": "soft" if soft_delete else "hard",
        "trash_dir": str(trash_dir) if trash_dir else None,
    }


def restore_project_session_files(
    codex_home: Path,
    project_path: Path,
    session_id: str,
) -> dict[str, Any]:
    items = _find_project_trashed_items(codex_home, project_path, session_id)
    if not items:
        raise CodexOpsError("未找到回收站中的指定会话。")

    sessions_root = codex_home / "sessions"

    def _unique_target(path: Path) -> Path:
        if not path.exists():
            return path
        suffix = 1
        while True:
            candidate = path.with_name(f"{path.stem}.restored-{suffix}{path.suffix}")
            if not candidate.exists():
                return candidate
            suffix += 1

    restored = 0
    for item in items:
        src = item["path"]
        meta = item.get("meta", {})
        restore_rel = _sanitize_restore_rel(meta.get("restore_rel"))
        target = _unique_target(sessions_root / restore_rel)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(target))
            restored += 1
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise CodexOpsError(f"恢复会话文件失败：{src}") from exc

    _scan_rollout_items(codex_home)
    return {
        "session_id": session_id.strip(),
        "restored_files": restored,
    }


def _sanitize_restore_rel(raw_value: Any) -> Path:
    raw = str(raw_value or "").strip().replace("\\", "/")
    raw = raw.lstrip("/")
    path = Path(raw) if raw else Path("unknown-rollout.jsonl")
    safe_parts: list[str] = []
    for part in path.parts:
        if part in {"", ".", ".."}:
            continue
        safe_parts.append(part)
    if not safe_parts:
        return Path("unknown-rollout.jsonl")
    return Path(*safe_parts)
