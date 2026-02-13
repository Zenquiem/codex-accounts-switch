# codex-accounts-switch

`codex-accounts-switch` 是一个面向 Ubuntu 的本地桌面工具（Web UI 壳），用于管理多个 Codex OAuth 账号，并按项目快速启动或恢复会话。

版本：`1.0.5`

## 核心能力

- 多账号隔离：每个账号独立 `CODEX_HOME`。
- 账号管理：添加（OAuth 登录）、去重、删除。
- 项目管理：新增、编辑、删除、启动。
- 会话管理：按项目列出、筛选、预览、恢复。
- 会话回收站：软删除、恢复、恢复并打开。
- 额度查看：5 小时额度 / 周额度，支持手动刷新。
- 设置页：通用 / 高级 / 关于（语言、主题、关闭行为、环境检测等）。
- 环境组件支持检查最新版，并可一键打开安装终端执行升级。
- 工具自身支持版本检测（对比当前版本与 GitHub 最新 release/tag）并可一键打开更新终端。
- 桌面壳：支持 `pywebview`，可直接以桌面应用方式运行。

## 运行环境

- Ubuntu 桌面环境
- Python 3.10+
- `npm` / `node`
- `codex` CLI
- `gnome-terminal`
- `bash`（必备）
- `zsh`（可选，优先使用）
- `zenity`（可选，目录选择器）

若未安装 `npm` / `node`，先执行：

```bash
sudo apt update
sudo apt install -y nodejs npm
node -v
npm -v
```

然后安装 Codex CLI：

```bash
sudo npm install -g @openai/codex
codex --version
```

桌面壳后端依赖（满足其一）：

- GTK 方案（推荐 Ubuntu 原生）
  - `sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.1`
- Qt 方案（纯 pip）
  - `pip install qtpy PyQt6`

## 快速开始（请先保证至少安装了npm/node和GTK）

```bash
cd /path/to/codexaccountsswitch
python3 -m venv .venv
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt
./codex-accounts-switch
```

默认是桌面模式（`--mode desktop`）。

若你执行过桌面应用入口安装脚本，也可以直接输入：

```bash
cas
```

如需 Web 调试模式：

```bash
python3 run.py --mode web --port 18420
```

## 安装桌面应用入口

```bash
./scripts/install_desktop_entry.sh
```

会安装：

- `~/.local/share/applications/codex-accounts-switch.desktop`
- `~/.local/bin/codex-accounts-switch-desktop`
- `~/.local/bin/cas`

安装脚本会自动检查并补充 `~/.local/bin` 到 `~/.bashrc` / `~/.zshrc` / `~/.profile` 的 `PATH` 配置（若缺失）。

卸载：

```bash
./scripts/uninstall_desktop_entry.sh
```

## 项目结构

```text
codex_accounts_switch/
  webapp.py          # Flask API + 页面路由
  codex_ops.py       # Codex CLI 调用与会话/额度逻辑
  storage.py         # 本地 registry 存储
  desktop_shell.py   # pywebview 桌面壳启动
  templates/
  static/
scripts/
run.py
codex-accounts-switch
```

## 数据目录与安全说明

默认数据目录：`~/.local/share/codex-accounts-switch`

- `registry/accounts.json`
- `registry/projects.json`
- `accounts/<account_id>/`（该账号对应 `CODEX_HOME`）

说明：

- OAuth 凭据由 Codex CLI 在各账号目录中维护。
- 本工具不解析、不存储 token 明文字段。
- 账号去重基于 OAuth 身份指纹。

## 常见问题

- 添加账号跳转网页失败：先确认网络/代理环境，再重试刷新。
- 额度查询失败：先确认网络/代理环境，再重试刷新。
- 桌面图标没更新：重新执行安装脚本，必要时注销重登。
- `permission denied`：
  - `sudo chown -R $(whoami) ~/.local/share/codex-accounts-switch/accounts/<account_id>`

## 开发

```bash
python3 -m compileall run.py codex_accounts_switch
```

## 许可证

MIT，见 `LICENSE`。
