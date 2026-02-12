#!/usr/bin/env python3
from __future__ import annotations

import argparse

from codex_accounts_switch import create_app
from codex_accounts_switch.desktop_shell import DesktopShellError, launch_desktop_shell


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="codex-accounts-switch launcher")
    parser.add_argument(
        "--mode",
        choices=("desktop", "web"),
        default="desktop",
        help="启动模式: desktop(默认) / web(仅调试)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=18420, help="Bind port")
    parser.add_argument("--data-root", default=None, help="Override data root path")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    parser.add_argument("--window-width", type=int, default=1320, help="Desktop window width")
    parser.add_argument("--window-height", type=int, default=860, help="Desktop window height")
    return parser.parse_args()


def _run_web(args: argparse.Namespace) -> None:
    app = create_app(data_root=args.data_root)
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


def _run_desktop(args: argparse.Namespace) -> None:
    launch_desktop_shell(
        data_root=args.data_root,
        host=args.host,
        port=args.port,
        width=args.window_width,
        height=args.window_height,
    )


def main() -> None:
    args = parse_args()
    if args.mode == "web":
        _run_web(args)
        return

    try:
        _run_desktop(args)
    except DesktopShellError as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    main()
