from __future__ import annotations

import contextlib
import logging
import socket
from pathlib import Path
from threading import Thread

from werkzeug.serving import make_server

from .storage import RegistryStore
from .webapp import create_app


class DesktopShellError(Exception):
    """Raised when desktop shell startup fails."""


class _FlaskServerThread(Thread):
    def __init__(self, host: str, port: int, data_root: str | None) -> None:
        super().__init__(daemon=True)
        self._server = make_server(host, port, create_app(data_root=data_root), threaded=True)

    def run(self) -> None:
        self._server.serve_forever()

    def stop(self) -> None:
        self._server.shutdown()


def _resolve_window_icon() -> str | None:
    project_root = Path(__file__).resolve().parent.parent
    icon_path = project_root / "assets" / "icons" / "codex-accounts-switch.svg"
    if icon_path.exists() and icon_path.is_file():
        return str(icon_path)
    return None


def _pick_free_port(host: str = "127.0.0.1") -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def launch_desktop_shell(
    *,
    data_root: str | None = None,
    host: str = "127.0.0.1",
    port: int | None = None,
    title: str = "codex-accounts-switch",
    width: int = 1320,
    height: int = 860,
) -> None:
    try:
        import webview
    except ImportError as exc:
        raise DesktopShellError(
            "缺少 `pywebview` 依赖，无法启动桌面壳。请先安装 requirements.txt。"
        ) from exc

    # Reduce backend probing noise on stderr and provide concise guidance via exceptions below.
    logging.getLogger("pywebview").setLevel(logging.ERROR)

    store = RegistryStore(Path(data_root) if data_root else None)
    bind_port = int(port or _pick_free_port(host))
    server_thread = _FlaskServerThread(host=host, port=bind_port, data_root=data_root)
    server_thread.start()

    app_url = f"http://{host}:{bind_port}"
    try:
        main_window = webview.create_window(
            title=title,
            url=app_url,
            width=width,
            height=height,
            min_size=(980, 680),
        )

        def _on_window_closing(window):
            behavior = store.get_ui_settings().get("window_close_behavior", "exit")
            if behavior == "minimize_to_tray":
                try:
                    window.minimize()
                except Exception:
                    pass
                return False
            return True

        main_window.events.closing += _on_window_closing
        try:
            webview.start(icon=_resolve_window_icon())
        except Exception as exc:
            raw = str(exc).strip()
            if "either QT or GTK" in raw:
                raise DesktopShellError(
                    "桌面壳缺少 GUI 后端（GTK/Qt）。\n"
                    "可选修复方案：\n"
                    "1) GTK 方案（推荐 Ubuntu 原生）：\n"
                    "   sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.1\n"
                    "   然后重建虚拟环境（包含系统包）：\n"
                    "   rm -rf .venv && python3 -m venv .venv --system-site-packages\n"
                    "   source .venv/bin/activate && pip install -r requirements.txt\n"
                    "2) Qt 方案（纯 pip）：\n"
                    "   ./.venv/bin/pip install qtpy PyQt6\n"
                    "安装后重试：./codex-accounts-switch --mode desktop\n"
                    "临时可用方案：./codex-accounts-switch --mode web"
                ) from exc
            raise DesktopShellError(f"桌面壳启动失败：{raw or '未知错误。'}") from exc
    finally:
        server_thread.stop()
        server_thread.join(timeout=2)
