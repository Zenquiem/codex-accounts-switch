const DEFAULT_UI_SETTINGS = {
  language: "zh-CN",
  theme: "light",
  window_close_behavior: "exit",
};

const TOOLBAR_ICONS = {
  refresh: "⟳",
  settings: "⚙",
  trash: "🗑",
  open_project: "▶",
  history: "⟲",
  add_project: "⊞",
  accounts: "👥",
};

const TOOLBAR_SVG_ICONS = {
  open_project: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3.5" y="5.5" width="17" height="13" rx="2"></rect>
      <path d="M10 9L15.5 12L10 15Z" fill="currentColor" stroke="none"></path>
    </svg>
  `,
  history: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 4V9H8"></path>
      <path d="M5.3 17.9A9 9 0 1 0 3 12"></path>
      <path d="M12 8V12.2L14.9 14"></path>
    </svg>
  `,
  add_project: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3.5 8A2.5 2.5 0 0 1 6 5.5H9.6L11.8 7.7H18A2.5 2.5 0 0 1 20.5 10.2V16A2.5 2.5 0 0 1 18 18.5H6A2.5 2.5 0 0 1 3.5 16Z"></path>
      <path d="M12 10.8V15.2"></path>
      <path d="M9.8 13H14.2"></path>
    </svg>
  `,
  accounts: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="9" cy="9" r="2.6"></circle>
      <path d="M4.5 18C4.5 15.7 6.5 14 9 14C11.5 14 13.5 15.7 13.5 18"></path>
      <circle cx="16.8" cy="10.2" r="2.1"></circle>
      <path d="M14.6 18C14.9 16.3 16.3 15 18 15C19.9 15 21 16.2 21 18"></path>
    </svg>
  `,
};

const state = {
  accounts: [],
  projects: [],
  systemStatus: null,
  aboutInfo: null,
  accountQuotas: {},
  accountQuotaLoading: {},
  uiSettings: { ...DEFAULT_UI_SETTINGS },
  settingsTab: "general",
};

const I18N = {
  "zh-CN": {
    toolbar_refresh_title: "刷新",
    toolbar_settings_title: "设置",
    toolbar_trash_title: "回收站",
    toolbar_open_project: "启动项目",
    toolbar_history: "历史会话",
    toolbar_add_project: "添加项目",
    toolbar_accounts: "账号管理",
    projects_title: "已创建项目",
    empty_projects: "还没有项目，点击上方“添加项目”开始创建。",
    account_prefix: "账号",
    unknown_account: "未知账号",
    action_open: "启动",
    action_sessions: "会话",
    action_edit: "编辑",
    action_delete: "删除",
    action_preview: "预览",
    action_restore: "恢复",
    action_restore_open: "恢复并打开",
    loading: "加载中...",
    reading_failed: "读取失败",
    request_failed: "请求失败",
    no_accounts: "暂无账号",
    add_account_first: "请先添加账号。",
    no_projects: "暂无项目",
    no_history_sessions: "未找到历史会话",
    no_history_sessions_desc: "该项目在当前绑定账号下还没有记录。",
    trash_empty: "回收站为空",
    trash_empty_desc: "当前项目没有可恢复的会话。",
    deleted_time: "删除时间",
    files_count: "文件数",
    session_time_unknown: "未知时间",
    status_ok: "正常",
    status_bad: "异常",
    status_unavailable: "状态不可用",
    status_unavailable_desc: "未返回检测结果。",
    env_ok: "环境可用",
    env_bad: "环境存在问题",
    env_ok_desc: "Codex 与核心依赖可正常使用。",
    env_bad_desc: "请根据下方异常项补齐依赖。",
    status_key: "状态",
    version_key: "版本",
    path_key: "路径",
    reason_key: "说明",
    path_not_found: "未找到",
    status_checking: "检测中...",
    status_check_failed: "检测失败",
    settings_title: "设置",
    add_project_title: "添加项目",
    add_project_label_name: "项目名",
    add_project_label_path: "项目路径（必须已存在）",
    add_project_label_account: "绑定账号",
    add_project_cancel: "取消",
    add_project_submit: "保存项目",
    add_project_name_placeholder: "例如：client-workspace",
    add_project_path_placeholder: "/home/you/workspace/client-workspace",
    edit_project_title: "编辑项目",
    edit_project_label_name: "项目名",
    edit_project_label_path: "项目路径（必须已存在）",
    edit_project_label_account: "绑定账号",
    edit_project_cancel: "取消",
    edit_project_submit: "保存修改",
    project_path_pick: "选择目录",
    edit_project_path_pick: "选择目录",
    accounts_title: "账号管理",
    accounts_hint: "添加后会打开 Codex 登录终端，完成 OAuth 登录后账号才会保存。",
    accounts_close: "关闭",
    account_alias_placeholder: "账号别名，例如：work",
    quota_label_5h: "5 小时额度",
    quota_label_weekly: "周额度",
    quota_not_loaded: "未获取",
    quota_loading: "获取中...",
    quota_refresh: "刷新额度",
    quota_remaining_short: "剩余",
    quota_reset_short: "重置",
    quota_error_prefix: "额度查询失败",
    quota_raw_prefix: "原始状态",
    open_project_title: "启动项目",
    open_project_close: "关闭",
    sessions_title: "历史会话",
    sessions_label_project: "选择项目",
    sessions_filter_apply: "筛选",
    sessions_filter_reset: "重置",
    sessions_close: "关闭",
    session_preview_close: "关闭",
    trash_title: "回收站会话",
    trash_label_project: "选择项目",
    trash_filter_apply: "筛选",
    trash_filter_reset: "重置",
    trash_open_dir: "打开目录",
    trash_close: "关闭",
    settings_tab_general: "通用",
    settings_tab_advanced: "高级",
    settings_tab_about: "关于",
    label_setting_language: "界面语言",
    label_setting_theme: "外观主题",
    label_setting_window_close: "窗口行为",
    label_setting_config_dir: "配置目录",
    setting_language_zh: "中文",
    setting_language_en: "English",
    setting_theme_light: "浅色",
    setting_theme_dark: "深色",
    setting_window_close_exit: "关闭时直接退出",
    setting_window_close_minimize: "关闭时最小化到托盘",
    settings_save_general: "保存设置",
    setting_config_open: "打开目录",
    settings_recheck: "重新检测",
    settings_close: "关闭",
    session_search_placeholder: "搜索会话名或 session_id",
    trash_search_placeholder: "搜索会话名或 session_id",
    account_add_button: "添加账号",
    account_add_in_progress: "登录中...",
    pick_directory_in_progress: "选择中...",
    toast_data_refreshed: "数据已刷新。",
    toast_project_added: "项目添加成功。",
    toast_project_updated: "项目修改成功。",
    toast_account_added: "账号添加成功。",
    toast_account_deleted: "账号已删除。",
    toast_project_deleted: "项目已删除。",
    toast_project_terminal_started: "项目终端已启动。",
    toast_session_opened: "历史会话已打开。",
    toast_session_deleted: "历史会话已删除。",
    toast_session_restored: "会话已恢复。",
    toast_settings_saved: "设置已保存。",
    toast_trash_opened: "已打开回收站目录{alias}。",
    toast_config_opened: "已打开配置目录。",
    toast_quota_refreshed: "额度已刷新。",
    confirm_delete_project: "确认删除该项目吗？",
    confirm_delete_account: "确认删除该账号吗？删除后该账号登录态会被清理。",
    confirm_delete_session:
      "确认删除会话“{title}”吗？\n将移入回收站（软删除），共 {count} 个会话文件。",
    confirm_restore_session: "确认{action}该会话吗？",
    no_preview: "暂无可预览内容",
    no_preview_desc: "该会话还没有可显示的消息片段。",
    preview_title_default: "会话预览",
    preview_role_assistant: "助手",
    preview_role_user: "用户",
    about_unavailable: "关于信息不可用",
    about_unavailable_desc: "未返回版本与运行环境信息。",
    about_version: "工具版本",
    about_platform: "系统平台",
    about_python: "Python",
    about_machine: "架构",
    about_data_root: "配置目录",
    role_status_detail: "状态：{status}",
    role_version_detail: "版本：{version}",
    role_path_detail: "路径：{path}",
    role_reason_detail: "说明：{reason}",
  },
  "en-US": {
    toolbar_refresh_title: "Refresh",
    toolbar_settings_title: "Settings",
    toolbar_trash_title: "Trash",
    toolbar_open_project: "Open Project",
    toolbar_history: "History",
    toolbar_add_project: "Add Project",
    toolbar_accounts: "Accounts",
    projects_title: "Projects",
    empty_projects: "No projects yet. Click “Add Project” to start.",
    account_prefix: "Account",
    unknown_account: "Unknown",
    action_open: "Open",
    action_sessions: "Sessions",
    action_edit: "Edit",
    action_delete: "Delete",
    action_preview: "Preview",
    action_restore: "Restore",
    action_restore_open: "Restore & Open",
    loading: "Loading...",
    reading_failed: "Read failed",
    request_failed: "Request failed",
    no_accounts: "No accounts",
    add_account_first: "Please add an account first.",
    no_projects: "No projects",
    no_history_sessions: "No session history found",
    no_history_sessions_desc: "No records found for this project under the bound account.",
    trash_empty: "Trash is empty",
    trash_empty_desc: "No recoverable sessions for this project.",
    deleted_time: "Deleted",
    files_count: "Files",
    session_time_unknown: "Unknown time",
    status_ok: "OK",
    status_bad: "Error",
    status_unavailable: "Status unavailable",
    status_unavailable_desc: "No diagnostic data was returned.",
    env_ok: "Environment ready",
    env_bad: "Environment issues detected",
    env_ok_desc: "Codex and core dependencies are available.",
    env_bad_desc: "Please fix missing or broken dependencies listed below.",
    status_key: "Status",
    version_key: "Version",
    path_key: "Path",
    reason_key: "Info",
    path_not_found: "Not found",
    status_checking: "Checking...",
    status_check_failed: "Check failed",
    settings_title: "Settings",
    add_project_title: "Add Project",
    add_project_label_name: "Project name",
    add_project_label_path: "Project path (must already exist)",
    add_project_label_account: "Bound account",
    add_project_cancel: "Cancel",
    add_project_submit: "Save Project",
    add_project_name_placeholder: "e.g. client-workspace",
    add_project_path_placeholder: "/home/you/workspace/client-workspace",
    edit_project_title: "Edit Project",
    edit_project_label_name: "Project name",
    edit_project_label_path: "Project path (must already exist)",
    edit_project_label_account: "Bound account",
    edit_project_cancel: "Cancel",
    edit_project_submit: "Save Changes",
    project_path_pick: "Choose directory",
    edit_project_path_pick: "Choose directory",
    accounts_title: "Account Management",
    accounts_hint:
      "After clicking add, a Codex login terminal will open. The account is saved only after OAuth succeeds.",
    accounts_close: "Close",
    account_alias_placeholder: "Account alias, e.g. work",
    quota_label_5h: "5h quota",
    quota_label_weekly: "Weekly quota",
    quota_not_loaded: "Not fetched",
    quota_loading: "Loading...",
    quota_refresh: "Refresh quota",
    quota_remaining_short: "Remaining",
    quota_reset_short: "Reset",
    quota_error_prefix: "Quota check failed",
    quota_raw_prefix: "Raw status",
    open_project_title: "Open Project",
    open_project_close: "Close",
    sessions_title: "History",
    sessions_label_project: "Select project",
    sessions_filter_apply: "Filter",
    sessions_filter_reset: "Reset",
    sessions_close: "Close",
    session_preview_close: "Close",
    trash_title: "Trash Sessions",
    trash_label_project: "Select project",
    trash_filter_apply: "Filter",
    trash_filter_reset: "Reset",
    trash_open_dir: "Open Directory",
    trash_close: "Close",
    settings_tab_general: "General",
    settings_tab_advanced: "Advanced",
    settings_tab_about: "About",
    label_setting_language: "Language",
    label_setting_theme: "Theme",
    label_setting_window_close: "Window behavior",
    label_setting_config_dir: "Config directory",
    setting_language_zh: "Chinese",
    setting_language_en: "English",
    setting_theme_light: "Light",
    setting_theme_dark: "Dark",
    setting_window_close_exit: "Exit on close",
    setting_window_close_minimize: "Minimize to tray on close",
    settings_save_general: "Save settings",
    setting_config_open: "Open Directory",
    settings_recheck: "Recheck",
    settings_close: "Close",
    session_search_placeholder: "Search by title or session_id",
    trash_search_placeholder: "Search by title or session_id",
    account_add_button: "Add Account",
    account_add_in_progress: "Signing in...",
    pick_directory_in_progress: "Picking...",
    toast_data_refreshed: "Data refreshed.",
    toast_project_added: "Project added.",
    toast_project_updated: "Project updated.",
    toast_account_added: "Account added.",
    toast_account_deleted: "Account deleted.",
    toast_project_deleted: "Project deleted.",
    toast_project_terminal_started: "Project terminal launched.",
    toast_session_opened: "Session opened.",
    toast_session_deleted: "Session deleted.",
    toast_session_restored: "Session restored.",
    toast_settings_saved: "Settings saved.",
    toast_trash_opened: "Trash directory opened{alias}.",
    toast_config_opened: "Config directory opened.",
    toast_quota_refreshed: "Quota refreshed.",
    confirm_delete_project: "Delete this project?",
    confirm_delete_account: "Delete this account? The login state under this account will be removed.",
    confirm_delete_session:
      "Delete session \"{title}\"?\nIt will be moved to trash (soft delete), {count} files total.",
    confirm_restore_session: "Confirm to {action} this session?",
    no_preview: "No preview content",
    no_preview_desc: "No message snippets available for this session.",
    preview_title_default: "Session Preview",
    preview_role_assistant: "Assistant",
    preview_role_user: "User",
    about_unavailable: "About information unavailable",
    about_unavailable_desc: "Version/runtime details were not returned.",
    about_version: "Version",
    about_platform: "Platform",
    about_python: "Python",
    about_machine: "Architecture",
    about_data_root: "Config directory",
    role_status_detail: "Status: {status}",
    role_version_detail: "Version: {version}",
    role_path_detail: "Path: {path}",
    role_reason_detail: "Info: {reason}",
  },
};

function byId(id) {
  return document.getElementById(id);
}

function normalizeLanguage(value) {
  return value === "en-US" ? "en-US" : "zh-CN";
}

function normalizeTheme(value) {
  return value === "dark" ? "dark" : "light";
}

function normalizeWindowCloseBehavior(value) {
  return value === "minimize_to_tray" ? "minimize_to_tray" : "exit";
}

function normalizeUISettings(raw) {
  const source = raw && typeof raw === "object" ? raw : {};
  return {
    language: normalizeLanguage(source.language),
    theme: normalizeTheme(source.theme),
    window_close_behavior: normalizeWindowCloseBehavior(source.window_close_behavior),
  };
}

function t(key, vars = {}) {
  const locale = normalizeLanguage(state.uiSettings.language);
  const pack = I18N[locale] || I18N["zh-CN"];
  let text = pack[key] || I18N["zh-CN"][key] || key;
  Object.entries(vars).forEach(([name, value]) => {
    text = text.replaceAll(`{${name}}`, String(value));
  });
  return text;
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", normalizeTheme(theme));
}

function setText(id, value) {
  const el = byId(id);
  if (!el) return;
  el.textContent = value;
}

function setIcon(id, markup) {
  const el = byId(id);
  if (!el) return;
  el.innerHTML = markup;
}

function setTitle(id, value) {
  const el = byId(id);
  if (!el) return;
  el.title = value;
}

function setAriaLabel(id, value) {
  const el = byId(id);
  if (!el) return;
  el.setAttribute("aria-label", value);
}

function setPlaceholder(id, value) {
  const el = byId(id);
  if (!el) return;
  el.placeholder = value;
}

function applyTranslations(options = {}) {
  const rerenderDynamic = options.rerenderDynamic !== false;
  const lang = normalizeLanguage(state.uiSettings.language);
  document.documentElement.lang = lang;

  setText("btn-refresh", TOOLBAR_ICONS.refresh);
  setText("btn-settings", TOOLBAR_ICONS.settings);
  setText("btn-trash", TOOLBAR_ICONS.trash);
  setIcon("btn-open-project", TOOLBAR_SVG_ICONS.open_project);
  setIcon("btn-history", TOOLBAR_SVG_ICONS.history);
  setIcon("btn-add-project", TOOLBAR_SVG_ICONS.add_project);
  setIcon("btn-accounts", TOOLBAR_SVG_ICONS.accounts);

  setTitle("btn-refresh", t("toolbar_refresh_title"));
  setTitle("btn-settings", t("toolbar_settings_title"));
  setTitle("btn-trash", t("toolbar_trash_title"));
  setTitle("btn-open-project", t("toolbar_open_project"));
  setTitle("btn-history", t("toolbar_history"));
  setTitle("btn-add-project", t("toolbar_add_project"));
  setTitle("btn-accounts", t("toolbar_accounts"));
  setAriaLabel("btn-refresh", t("toolbar_refresh_title"));
  setAriaLabel("btn-settings", t("toolbar_settings_title"));
  setAriaLabel("btn-trash", t("toolbar_trash_title"));
  setAriaLabel("btn-open-project", t("toolbar_open_project"));
  setAriaLabel("btn-history", t("toolbar_history"));
  setAriaLabel("btn-add-project", t("toolbar_add_project"));
  setAriaLabel("btn-accounts", t("toolbar_accounts"));
  setText("projects-title", t("projects_title"));
  setText("empty-state", t("empty_projects"));

  setText("add-project-title", t("add_project_title"));
  setText("add-project-label-name", t("add_project_label_name"));
  setText("add-project-label-path", t("add_project_label_path"));
  setText("add-project-label-account", t("add_project_label_account"));
  setText("add-project-cancel", t("add_project_cancel"));
  setText("add-project-submit", t("add_project_submit"));
  setText("project-path-pick", t("project_path_pick"));
  setPlaceholder("project-name", t("add_project_name_placeholder"));
  setPlaceholder("project-path", t("add_project_path_placeholder"));

  setText("edit-project-title", t("edit_project_title"));
  setText("edit-project-label-name", t("edit_project_label_name"));
  setText("edit-project-label-path", t("edit_project_label_path"));
  setText("edit-project-label-account", t("edit_project_label_account"));
  setText("edit-project-cancel", t("edit_project_cancel"));
  setText("edit-project-submit", t("edit_project_submit"));
  setText("edit-project-path-pick", t("edit_project_path_pick"));

  setText("accounts-title", t("accounts_title"));
  setText("accounts-hint", t("accounts_hint"));
  setText("accounts-close", t("accounts_close"));
  setPlaceholder("account-alias", t("account_alias_placeholder"));

  setText("open-project-title", t("open_project_title"));
  setText("open-project-close", t("open_project_close"));

  setText("sessions-title", t("sessions_title"));
  setText("sessions-label-project", t("sessions_label_project"));
  setText("session-filter-apply", t("sessions_filter_apply"));
  setText("session-filter-reset", t("sessions_filter_reset"));
  setText("sessions-close", t("sessions_close"));
  setText("session-preview-close", t("session_preview_close"));

  setText("trash-title", t("trash_title"));
  setText("trash-label-project", t("trash_label_project"));
  setText("trash-filter-apply", t("trash_filter_apply"));
  setText("trash-filter-reset", t("trash_filter_reset"));
  setText("trash-open-dir", t("trash_open_dir"));
  setText("trash-close", t("trash_close"));

  setText("settings-title", t("settings_title"));
  setText("settings-tab-general", t("settings_tab_general"));
  setText("settings-tab-advanced", t("settings_tab_advanced"));
  setText("settings-tab-about", t("settings_tab_about"));
  setText("label-setting-language", t("label_setting_language"));
  setText("label-setting-theme", t("label_setting_theme"));
  setText("label-setting-window-close", t("label_setting_window_close"));
  setText("label-setting-config-dir", t("label_setting_config_dir"));
  setText("setting-language-zh", t("setting_language_zh"));
  setText("setting-language-en", t("setting_language_en"));
  setText("setting-theme-light", t("setting_theme_light"));
  setText("setting-theme-dark", t("setting_theme_dark"));
  setText("setting-window-close-exit", t("setting_window_close_exit"));
  setText("setting-window-close-minimize", t("setting_window_close_minimize"));
  setText("settings-save-general", t("settings_save_general"));
  setText("setting-config-open", t("setting_config_open"));
  setText("settings-recheck", t("settings_recheck"));
  setText("settings-close", t("settings_close"));
  setPlaceholder("session-search", t("session_search_placeholder"));
  setPlaceholder("trash-search", t("trash_search_placeholder"));

  const addAccountBtn = byId("form-add-account")?.querySelector("button[type='submit']");
  if (addAccountBtn && !addAccountBtn.disabled) {
    addAccountBtn.textContent = t("account_add_button");
  }

  if (!rerenderDynamic) return;
  renderProjectGrid();
  renderAccountList();
  renderOpenProjectList();

  const sessionsDialog = byId("dialog-sessions");
  if (sessionsDialog?.open) {
    const projectId = byId("session-project-select")?.value;
    if (projectId) renderSessions(projectId);
  }
  const trashDialog = byId("dialog-trash-sessions");
  if (trashDialog?.open) {
    const projectId = byId("trash-project-select")?.value;
    if (projectId) renderTrashSessions(projectId);
  }
  if (byId("dialog-settings")?.open) {
    renderSystemStatus(state.systemStatus);
    renderAboutInfo(state.aboutInfo);
  }
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `${t("request_failed")}: ${response.status}`);
  }
  return payload;
}

function showToast(text, isError = false) {
  const toast = byId("toast");
  toast.textContent = text;
  toast.style.background = isError ? "#8a2525" : "";
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 3200);
}

function closeDialog(id) {
  const dialog = byId(id);
  if (dialog && dialog.open) {
    dialog.close();
  }
}

function openDialog(id) {
  const dialog = byId(id);
  if (dialog && !dialog.open) {
    dialog.showModal();
  }
}

function formatTimestamp(timestamp) {
  if (!timestamp) return t("session_time_unknown");
  const dt = new Date(timestamp);
  if (Number.isNaN(dt.getTime())) return timestamp;
  const locale = normalizeLanguage(state.uiSettings.language);
  return dt.toLocaleString(locale);
}

function truncateText(text, maxLen = 220) {
  const normalized = String(text || "").trim();
  if (normalized.length <= maxLen) return normalized;
  return `${normalized.slice(0, maxLen).trim()}...`;
}

function containsQuotaMarkers(text) {
  const normalized = String(text || "").toLowerCase();
  return (
    normalized.includes("5h") ||
    normalized.includes("5-hour") ||
    normalized.includes("5 hour") ||
    normalized.includes("5小时") ||
    normalized.includes("weekly") ||
    normalized.includes("week") ||
    normalized.includes("周")
  );
}

function formatQuotaEntry(entry) {
  if (!entry || typeof entry !== "object") return t("quota_not_loaded");

  const parts = [];
  if (entry.used && entry.limit) {
    parts.push(`${entry.used}/${entry.limit}`);
  } else if (entry.percent_used) {
    parts.push(`${entry.percent_used}%`);
  }
  if (entry.remaining) {
    parts.push(`${t("quota_remaining_short")}: ${entry.remaining}`);
  }
  if (entry.reset) {
    parts.push(`${t("quota_reset_short")}: ${entry.reset}`);
  }
  if (parts.length > 0) return parts.join(" · ");

  if (entry.line) return truncateText(entry.line, 150);
  return t("quota_not_loaded");
}

function renderProjectGrid() {
  const grid = byId("project-grid");
  const empty = byId("empty-state");
  const count = byId("project-count");
  grid.innerHTML = "";
  count.textContent = String(state.projects.length);

  if (state.projects.length === 0) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");

  state.projects.forEach((project) => {
    const nameText = String(project.name || "");
    const pathText = String(project.path || "");
    const accountText = String(project.account_alias || t("unknown_account"));
    const card = document.createElement("article");
    card.className = "project-card";
    card.innerHTML = `
      <div class="project-title" title="${escapeHtmlAttr(nameText)}">${escapeHtml(nameText)}</div>
      <div class="project-path" title="${escapeHtmlAttr(pathText)}">${escapeHtml(pathText)}</div>
      <div class="project-meta" title="${escapeHtmlAttr(`${t("account_prefix")}: ${accountText}`)}">${escapeHtml(
        t("account_prefix")
      )}: ${escapeHtml(accountText)}</div>
      <div class="actions">
        <button class="primary" data-action="open" data-id="${project.id}">${escapeHtml(t(
      "action_open"
    ))}</button>
        <button class="secondary" data-action="sessions" data-id="${project.id}">${escapeHtml(t(
      "action_sessions"
    ))}</button>
        <button class="secondary" data-action="edit" data-id="${project.id}">${escapeHtml(t(
      "action_edit"
    ))}</button>
        <button class="danger" data-action="delete" data-id="${project.id}">${escapeHtml(t(
      "action_delete"
    ))}</button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function renderAccountList() {
  const container = byId("account-list");
  container.innerHTML = "";
  if (state.accounts.length === 0) {
    container.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("no_accounts")
    )}</strong><span>${escapeHtml(t("add_account_first"))}</span></div></div>`;
    return;
  }

  state.accounts.forEach((account) => {
    const quota = state.accountQuotas[account.id] || null;
    const quotaLoading = Boolean(state.accountQuotaLoading[account.id]);
    const quotaError = quota && quota.error ? truncateText(quota.error, 180) : "";
    const fiveHourText = quotaLoading ? t("quota_loading") : formatQuotaEntry(quota?.five_hour);
    const weeklyText = quotaLoading ? t("quota_loading") : formatQuotaEntry(quota?.weekly);
    const showRawQuota =
      !quotaError &&
      quota &&
      !quotaLoading &&
      !quota?.five_hour &&
      !quota?.weekly &&
      typeof quota.raw_text === "string" &&
      quota.raw_text.trim() &&
      containsQuotaMarkers(quota.raw_text);
    const rawQuotaText = showRawQuota ? truncateText(quota.raw_text, 180) : "";

    const row = document.createElement("div");
    row.className = "list-row";
    row.innerHTML = `
      <div class="list-main">
        <strong>${escapeHtml(account.alias)}</strong>
        <span>${escapeHtml(account.codex_home)}</span>
        <span>${escapeHtml(t("quota_label_5h"))}：${escapeHtml(fiveHourText)}</span>
        <span>${escapeHtml(t("quota_label_weekly"))}：${escapeHtml(weeklyText)}</span>
        ${
          quotaError
            ? `<span>${escapeHtml(t("quota_error_prefix"))}：${escapeHtml(quotaError)}</span>`
            : ""
        }
        ${
          rawQuotaText
            ? `<span>${escapeHtml(t("quota_raw_prefix"))}：${escapeHtml(rawQuotaText)}</span>`
            : ""
        }
      </div>
      <div class="row-actions">
        <button class="secondary" data-account-quota-refresh="${account.id}" ${
      quotaLoading ? "disabled" : ""
    }>${escapeHtml(quotaLoading ? t("quota_loading") : t("quota_refresh"))}</button>
        <button class="danger" data-account-delete="${account.id}">${escapeHtml(
      t("action_delete")
    )}</button>
      </div>
    `.trim();
    container.appendChild(row);
  });
}

function fillProjectAccountSelect(selectId = "project-account", selectedAccountId = "") {
  const select = byId(selectId);
  if (!select) return;
  select.innerHTML = "";
  if (state.accounts.length === 0) {
    select.innerHTML = `<option value="">${escapeHtml(t("add_account_first"))}</option>`;
    return;
  }
  state.accounts.forEach((account) => {
    const option = document.createElement("option");
    option.value = account.id;
    option.textContent = account.alias;
    if (selectedAccountId && selectedAccountId === account.id) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function renderOpenProjectList() {
  const container = byId("open-project-list");
  container.innerHTML = "";
  if (state.projects.length === 0) {
    container.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("no_projects")
    )}</strong></div></div>`;
    return;
  }
  state.projects.forEach((project) => {
    const row = document.createElement("div");
    row.className = "list-row";
    row.innerHTML = `
      <div class="list-main">
        <strong>${escapeHtml(project.name)}</strong>
        <span>${escapeHtml(project.path)}</span>
      </div>
      <button class="primary" data-project-open="${project.id}">${escapeHtml(t(
      "action_open"
    ))}</button>
    `;
    container.appendChild(row);
  });
}

function fillSessionProjectSelect() {
  const select = byId("session-project-select");
  select.innerHTML = "";
  state.projects.forEach((project) => {
    const option = document.createElement("option");
    option.value = project.id;
    option.textContent = project.name;
    select.appendChild(option);
  });
}

function fillTrashProjectSelect() {
  const select = byId("trash-project-select");
  if (!select) return;
  select.innerHTML = "";
  state.projects.forEach((project) => {
    const option = document.createElement("option");
    option.value = project.id;
    option.textContent = project.name;
    select.appendChild(option);
  });
}

function findProjectById(projectId) {
  return state.projects.find((project) => project.id === projectId) || null;
}

function statusLabel(ok) {
  return ok ? t("status_ok") : t("status_bad");
}

function componentDisplayName(key) {
  const labels = {
    codex: "Codex CLI",
    gnome_terminal: "gnome-terminal",
    zsh: "zsh",
    bash: "bash",
    zenity: "zenity",
  };
  return labels[key] || key;
}

function renderSystemStatus(status) {
  const list = byId("system-status-list");
  if (!status || !status.components) {
    list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("status_unavailable")
    )}</strong><span>${escapeHtml(t("status_unavailable_desc"))}</span></div></div>`;
    return;
  }

  const overall = status.overall_ok ? t("env_ok") : t("env_bad");
  const overallDesc = status.overall_ok ? t("env_ok_desc") : t("env_bad_desc");
  list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
    overall
  )}</strong><span>${escapeHtml(overallDesc)}</span></div></div>`;

  const order = ["codex", "gnome_terminal", "zsh", "bash", "zenity"];
  order.forEach((key) => {
    const item = status.components[key];
    if (!item) return;
    const details = [];
    details.push(t("role_status_detail", { status: statusLabel(Boolean(item.ok)) }));
    if (item.version) details.push(t("role_version_detail", { version: item.version }));
    if (item.path) details.push(t("role_path_detail", { path: item.path }));
    else details.push(t("role_path_detail", { path: t("path_not_found") }));
    if (item.error) details.push(t("role_reason_detail", { reason: item.error }));

    const row = document.createElement("div");
    row.className = "list-row";
    row.innerHTML = `
      <div class="list-main">
        <strong>${escapeHtml(componentDisplayName(key))}</strong>
        <span>${escapeHtml(details.join(" · "))}</span>
      </div>
    `;
    list.appendChild(row);
  });
}

function renderAboutInfo(about) {
  const list = byId("about-info-list");
  if (!about) {
    list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("about_unavailable")
    )}</strong><span>${escapeHtml(t("about_unavailable_desc"))}</span></div></div>`;
    return;
  }

  const rows = [
    { key: t("about_version"), value: about.version || "-" },
    { key: t("about_platform"), value: about.platform || "-" },
    { key: t("about_python"), value: about.python_version || "-" },
    { key: t("about_machine"), value: about.machine || "-" },
    { key: t("about_data_root"), value: about.data_root || "-" },
  ];
  list.innerHTML = "";
  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "list-row";
    item.innerHTML = `
      <div class="list-main">
        <strong>${escapeHtml(row.key)}</strong>
        <span>${escapeHtml(row.value)}</span>
      </div>
    `;
    list.appendChild(item);
  });
}

async function refreshAboutPanel() {
  renderAboutInfo(null);
  const statusList = byId("system-status-list");
  statusList.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
    t("status_checking")
  )}</strong></div></div>`;
  try {
    const payload = await apiRequest("/api/system/about");
    state.aboutInfo = payload.about || null;
    state.systemStatus = payload.status || null;
    renderAboutInfo(state.aboutInfo);
    renderSystemStatus(state.systemStatus);
  } catch (error) {
    statusList.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("status_check_failed")
    )}</strong><span>${escapeHtml(error.message)}</span></div></div>`;
  }
}

async function refreshConfigDirInfo() {
  try {
    const payload = await apiRequest("/api/system/config-dir");
    byId("setting-config-dir").value = payload.path || "";
  } catch (error) {
    byId("setting-config-dir").value = error.message;
  }
}

function openSettingsTab(tabName) {
  state.settingsTab = tabName;
  const tabs = byId("settings-tabs").querySelectorAll(".settings-tab");
  tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.settingsTab === tabName);
  });

  const panelGeneral = byId("settings-panel-general");
  const panelAdvanced = byId("settings-panel-advanced");
  const panelAbout = byId("settings-panel-about");
  panelGeneral.classList.toggle("hidden", tabName !== "general");
  panelAdvanced.classList.toggle("hidden", tabName !== "advanced");
  panelAbout.classList.toggle("hidden", tabName !== "about");

  byId("settings-recheck").classList.toggle("hidden", tabName !== "about");
}

function fillSettingsForm() {
  byId("setting-language").value = normalizeLanguage(state.uiSettings.language);
  byId("setting-theme").value = normalizeTheme(state.uiSettings.theme);
  byId("setting-window-close").value = normalizeWindowCloseBehavior(
    state.uiSettings.window_close_behavior
  );
}

async function fetchUISettings() {
  const payload = await apiRequest("/api/settings/ui");
  return normalizeUISettings(payload.settings || {});
}

async function updateUISettings(payload) {
  const result = await apiRequest("/api/settings/ui", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  return normalizeUISettings(result.settings || {});
}

function buildSessionQuery() {
  const params = new URLSearchParams({ limit: "60" });
  const keyword = byId("session-search").value.trim();
  const dateFrom = byId("session-date-from").value;
  const dateTo = byId("session-date-to").value;
  if (keyword) params.set("q", keyword);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return params.toString();
}

function buildTrashQuery() {
  const params = new URLSearchParams({ limit: "60" });
  const keyword = byId("trash-search").value.trim();
  if (keyword) params.set("q", keyword);
  return params.toString();
}

async function renderSessions(projectId) {
  const list = byId("session-list");
  list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
    t("loading")
  )}</strong></div></div>`;
  try {
    const query = buildSessionQuery();
    const payload = await apiRequest(`/api/projects/${projectId}/sessions?${query}`);
    const sessions = payload.sessions || [];
    list.innerHTML = "";
    if (sessions.length === 0) {
      list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
        t("no_history_sessions")
      )}</strong><span>${escapeHtml(t("no_history_sessions_desc"))}</span></div></div>`;
      return;
    }
    sessions.forEach((session) => {
      const row = document.createElement("div");
      row.className = "list-row";
      row.innerHTML = `
        <div class="list-main">
          <strong>${escapeHtml(session.title || session.session_id)}</strong>
          <span>${escapeHtml(formatTimestamp(session.timestamp))} · ${escapeHtml(
            session.session_id
          )}</span>
        </div>
        <div class="row-actions">
          <button class="primary" data-session-open="1" data-session-project="${escapeHtmlAttr(
            projectId
          )}" data-session-id="${escapeHtmlAttr(session.session_id)}">${escapeHtml(
        t("action_open")
      )}</button>
          <button class="secondary" data-session-preview="1" data-session-project="${escapeHtmlAttr(
            projectId
          )}" data-session-id="${escapeHtmlAttr(session.session_id)}">${escapeHtml(
        t("action_preview")
      )}</button>
          <button class="danger" data-session-delete="1" data-session-project="${escapeHtmlAttr(
            projectId
          )}" data-session-id="${escapeHtmlAttr(session.session_id)}">${escapeHtml(
        t("action_delete")
      )}</button>
        </div>
      `;
      list.appendChild(row);
    });
  } catch (error) {
    list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("reading_failed")
    )}</strong><span>${escapeHtml(error.message)}</span></div></div>`;
  }
}

async function renderTrashSessions(projectId) {
  const list = byId("trash-session-list");
  list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
    t("loading")
  )}</strong></div></div>`;
  try {
    const query = buildTrashQuery();
    const payload = await apiRequest(`/api/projects/${projectId}/trash/sessions?${query}`);
    const sessions = payload.sessions || [];
    list.innerHTML = "";
    if (sessions.length === 0) {
      list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
        t("trash_empty")
      )}</strong><span>${escapeHtml(t("trash_empty_desc"))}</span></div></div>`;
      return;
    }

    sessions.forEach((session) => {
      const row = document.createElement("div");
      row.className = "list-row";
      row.innerHTML = `
        <div class="list-main">
          <strong>${escapeHtml(session.title || session.session_id)}</strong>
          <span>${escapeHtml(t("deleted_time"))}：${escapeHtml(
        formatTimestamp(session.deleted_at)
      )} · ${escapeHtml(t("files_count"))} ${escapeHtml(
        String(session.files_count || 0)
      )} · ${escapeHtml(session.session_id)}</span>
        </div>
        <div class="row-actions">
          <button class="secondary" data-trash-restore="1" data-trash-project="${escapeHtmlAttr(
            projectId
          )}" data-trash-session-id="${escapeHtmlAttr(session.session_id)}">${escapeHtml(
        t("action_restore")
      )}</button>
          <button class="primary" data-trash-restore-open="1" data-trash-project="${escapeHtmlAttr(
            projectId
          )}" data-trash-session-id="${escapeHtmlAttr(session.session_id)}">${escapeHtml(
        t("action_restore_open")
      )}</button>
        </div>
      `;
      list.appendChild(row);
    });
  } catch (error) {
    list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("reading_failed")
    )}</strong><span>${escapeHtml(error.message)}</span></div></div>`;
  }
}

async function bootstrap() {
  const payload = await apiRequest("/api/bootstrap");
  state.accounts = payload.accounts || [];
  state.projects = payload.projects || [];
  const accountIds = new Set(state.accounts.map((account) => account.id));
  Object.keys(state.accountQuotas).forEach((accountId) => {
    if (!accountIds.has(accountId)) {
      delete state.accountQuotas[accountId];
    }
  });
  Object.keys(state.accountQuotaLoading).forEach((accountId) => {
    if (!accountIds.has(accountId)) {
      delete state.accountQuotaLoading[accountId];
    }
  });
  if (payload.ui_settings) {
    state.uiSettings = normalizeUISettings(payload.ui_settings);
    applyTheme(state.uiSettings.theme);
  }
  applyTranslations({ rerenderDynamic: false });
  renderProjectGrid();
  renderAccountList();
  fillProjectAccountSelect();
  renderOpenProjectList();
  fillSessionProjectSelect();
  fillTrashProjectSelect();
}

async function onAddProjectSubmit(event) {
  event.preventDefault();
  const name = byId("project-name").value.trim();
  const path = byId("project-path").value.trim();
  const accountId = byId("project-account").value;
  try {
    await apiRequest("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, path, account_id: accountId }),
    });
    closeDialog("dialog-add-project");
    byId("form-add-project").reset();
    await bootstrap();
    showToast(t("toast_project_added"));
  } catch (error) {
    showToast(error.message, true);
  }
}

function openEditProjectDialog(projectId) {
  const project = findProjectById(projectId);
  if (!project) {
    showToast(t("request_failed"), true);
    return;
  }

  byId("edit-project-id").value = project.id;
  byId("edit-project-name").value = project.name || "";
  byId("edit-project-path").value = project.path || "";
  fillProjectAccountSelect("edit-project-account", project.account_id || "");
  openDialog("dialog-edit-project");
}

async function onEditProjectSubmit(event) {
  event.preventDefault();
  const projectId = byId("edit-project-id").value;
  const name = byId("edit-project-name").value.trim();
  const path = byId("edit-project-path").value.trim();
  const accountId = byId("edit-project-account").value;
  if (!projectId) {
    showToast(t("request_failed"), true);
    return;
  }

  try {
    await updateProject(projectId, name, path, accountId);
    closeDialog("dialog-edit-project");
    await bootstrap();
    showToast(t("toast_project_updated"));
  } catch (error) {
    showToast(error.message, true);
  }
}

async function addAccount(alias) {
  await apiRequest("/api/accounts", {
    method: "POST",
    body: JSON.stringify({ alias }),
  });
}

async function fetchAccountQuota(accountId, forceRefresh = false) {
  const query = new URLSearchParams();
  if (forceRefresh) query.set("force", "1");
  const suffix = query.toString();
  return apiRequest(`/api/accounts/${accountId}/quota${suffix ? `?${suffix}` : ""}`);
}

async function refreshAccountQuota(accountId, forceRefresh = true) {
  state.accountQuotaLoading[accountId] = true;
  renderAccountList();
  try {
    const payload = await fetchAccountQuota(accountId, forceRefresh);
    state.accountQuotas[accountId] = payload.quota || null;
    showToast(t("toast_quota_refreshed"));
  } catch (error) {
    state.accountQuotas[accountId] = { error: error.message };
    showToast(error.message, true);
  } finally {
    delete state.accountQuotaLoading[accountId];
    renderAccountList();
  }
}

async function pickProjectDirectory(initialPath) {
  return apiRequest("/api/system/pick-directory", {
    method: "POST",
    body: JSON.stringify({ initial_path: initialPath || "" }),
  });
}

async function openTrashDirectory(accountId = "") {
  return apiRequest("/api/system/open-trash", {
    method: "POST",
    body: JSON.stringify({ account_id: accountId || "" }),
  });
}

async function openConfigDirectory() {
  return apiRequest("/api/system/config-dir/open", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

async function restoreTrashedSession(projectId, sessionId, openAfterRestore = false) {
  return apiRequest(`/api/projects/${projectId}/trash/sessions/restore`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, open_after_restore: openAfterRestore }),
  });
}

async function refreshHistoryIfVisible(projectId) {
  const sessionsDialog = byId("dialog-sessions");
  if (!sessionsDialog || !sessionsDialog.open) return;
  if (byId("session-project-select").value !== projectId) return;
  await renderSessions(projectId);
}

async function onAddAccountSubmit(event) {
  event.preventDefault();
  const aliasInput = byId("account-alias");
  const button = event.target.querySelector("button[type='submit']");
  const alias = aliasInput.value.trim();
  if (!alias) return;
  button.disabled = true;
  button.textContent = t("account_add_in_progress");
  try {
    await addAccount(alias);
    aliasInput.value = "";
    await bootstrap();
    showToast(t("toast_account_added"));
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = t("account_add_button");
  }
}

async function deleteAccount(accountId) {
  await apiRequest(`/api/accounts/${accountId}`, { method: "DELETE" });
}

async function deleteProject(projectId) {
  await apiRequest(`/api/projects/${projectId}`, { method: "DELETE" });
}

async function updateProject(projectId, name, path, accountId) {
  await apiRequest(`/api/projects/${projectId}`, {
    method: "PUT",
    body: JSON.stringify({ name, path, account_id: accountId }),
  });
}

async function openProject(projectId) {
  await apiRequest(`/api/projects/${projectId}/open`, { method: "POST" });
}

async function openSession(projectId, sessionId) {
  await apiRequest(`/api/projects/${projectId}/sessions/open`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

async function getSessionPreview(projectId, sessionId) {
  const params = new URLSearchParams({ session_id: sessionId });
  return apiRequest(`/api/projects/${projectId}/sessions/preview?${params.toString()}`);
}

async function planDeleteSession(projectId, sessionId) {
  return apiRequest(`/api/projects/${projectId}/sessions/delete-plan`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

async function deleteSession(projectId, sessionId, softDelete = true) {
  return apiRequest(`/api/projects/${projectId}/sessions/delete`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, soft_delete: softDelete }),
  });
}

async function openSessionPreviewDialog(projectId, sessionId) {
  byId("session-preview-title").textContent = t("preview_title_default");
  byId("session-preview-meta").textContent = "";
  byId("session-preview-list").innerHTML =
    `<div class="list-row"><div class="list-main"><strong>${escapeHtml(t("loading"))}</strong></div></div>`;
  openDialog("dialog-session-preview");

  try {
    const payload = await getSessionPreview(projectId, sessionId);
    const preview = payload.preview || {};
    byId("session-preview-title").textContent = preview.title || sessionId;
    byId("session-preview-meta").textContent = `${formatTimestamp(preview.timestamp)} · ${t(
      "files_count"
    )} ${preview.files_count || 0}`;
    const list = byId("session-preview-list");
    const messages = preview.messages || [];
    list.innerHTML = "";
    if (messages.length === 0) {
      list.innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
        t("no_preview")
      )}</strong><span>${escapeHtml(t("no_preview_desc"))}</span></div></div>`;
      return;
    }

    messages.forEach((message) => {
      const role =
        message.role === "assistant" ? t("preview_role_assistant") : t("preview_role_user");
      const row = document.createElement("div");
      row.className = "list-row";
      row.innerHTML = `
        <div class="list-main">
          <strong>${escapeHtml(role)}</strong>
          <span>${escapeHtml(message.text || "")}</span>
        </div>
      `;
      list.appendChild(row);
    });
  } catch (error) {
    byId("session-preview-list").innerHTML = `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
      t("reading_failed")
    )}</strong><span>${escapeHtml(error.message)}</span></div></div>`;
  }
}

function escapeHtml(input) {
  return String(input)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeHtmlAttr(input) {
  return escapeHtml(input).replaceAll("`", "&#096;");
}

async function openSettingsDialog() {
  fillSettingsForm();
  openSettingsTab("general");
  openDialog("dialog-settings");
  await Promise.all([refreshConfigDirInfo(), refreshAboutPanel()]);
}

async function saveGeneralSettingsFromForm() {
  const next = {
    language: normalizeLanguage(byId("setting-language").value),
    theme: normalizeTheme(byId("setting-theme").value),
    window_close_behavior: normalizeWindowCloseBehavior(byId("setting-window-close").value),
  };
  const settings = await updateUISettings(next);
  state.uiSettings = normalizeUISettings(settings);
  applyTheme(state.uiSettings.theme);
  applyTranslations();
  fillSettingsForm();
}

async function loadUISettings() {
  try {
    state.uiSettings = await fetchUISettings();
  } catch (error) {
    state.uiSettings = { ...DEFAULT_UI_SETTINGS };
  }
  applyTheme(state.uiSettings.theme);
  applyTranslations({ rerenderDynamic: false });
}

function bindEvents() {
  byId("btn-refresh").addEventListener("click", async () => {
    await bootstrap();
    showToast(t("toast_data_refreshed"));
  });

  byId("btn-settings").addEventListener("click", async () => {
    await openSettingsDialog();
  });

  byId("settings-tabs").addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const tab = target.dataset.settingsTab;
    if (!tab) return;
    openSettingsTab(tab);
  });

  byId("settings-save-general").addEventListener("click", async () => {
    try {
      await saveGeneralSettingsFromForm();
      showToast(t("toast_settings_saved"));
    } catch (error) {
      showToast(error.message, true);
    }
  });

  byId("setting-config-open").addEventListener("click", async () => {
    try {
      await openConfigDirectory();
      showToast(t("toast_config_opened"));
    } catch (error) {
      showToast(error.message, true);
    }
  });

  byId("settings-recheck").addEventListener("click", refreshAboutPanel);
  byId("settings-close").addEventListener("click", () => closeDialog("dialog-settings"));

  byId("btn-trash").addEventListener("click", async () => {
    fillTrashProjectSelect();
    openDialog("dialog-trash-sessions");
    const first = byId("trash-project-select").value;
    if (first) {
      await renderTrashSessions(first);
    } else {
      byId("trash-session-list").innerHTML =
        `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
          t("no_projects")
        )}</strong></div></div>`;
    }
  });
  byId("session-preview-close").addEventListener("click", () => closeDialog("dialog-session-preview"));
  byId("trash-close").addEventListener("click", () => closeDialog("dialog-trash-sessions"));
  byId("trash-project-select").addEventListener("change", async (event) => {
    const projectId = event.target.value;
    if (!projectId) return;
    await renderTrashSessions(projectId);
  });
  byId("trash-filter-apply").addEventListener("click", async () => {
    const projectId = byId("trash-project-select").value;
    if (!projectId) return;
    await renderTrashSessions(projectId);
  });
  byId("trash-filter-reset").addEventListener("click", async () => {
    byId("trash-search").value = "";
    const projectId = byId("trash-project-select").value;
    if (!projectId) return;
    await renderTrashSessions(projectId);
  });
  byId("trash-search").addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const projectId = byId("trash-project-select").value;
    if (!projectId) return;
    await renderTrashSessions(projectId);
  });
  byId("trash-open-dir").addEventListener("click", async () => {
    try {
      const projectId = byId("trash-project-select").value;
      const project = findProjectById(projectId);
      const payload = await openTrashDirectory(project?.account_id || "");
      const alias = payload.account_alias
        ? normalizeLanguage(state.uiSettings.language) === "en-US"
          ? ` (${payload.account_alias})`
          : `（${payload.account_alias}）`
        : "";
      showToast(t("toast_trash_opened", { alias }));
    } catch (error) {
      showToast(error.message, true);
    }
  });

  byId("btn-add-project").addEventListener("click", () => {
    fillProjectAccountSelect("project-account");
    openDialog("dialog-add-project");
  });
  byId("add-project-cancel").addEventListener("click", () => closeDialog("dialog-add-project"));
  byId("form-add-project").addEventListener("submit", onAddProjectSubmit);
  byId("project-path-pick").addEventListener("click", async () => {
    const input = byId("project-path");
    const button = byId("project-path-pick");
    const previousText = button.textContent;
    button.disabled = true;
    button.textContent = t("pick_directory_in_progress");
    try {
      const payload = await pickProjectDirectory(input.value.trim());
      if (!payload.cancelled && payload.path) {
        input.value = payload.path;
      }
    } catch (error) {
      showToast(error.message, true);
    } finally {
      button.disabled = false;
      button.textContent = previousText;
    }
  });
  byId("edit-project-cancel").addEventListener("click", () => closeDialog("dialog-edit-project"));
  byId("form-edit-project").addEventListener("submit", onEditProjectSubmit);
  byId("edit-project-path-pick").addEventListener("click", async () => {
    const input = byId("edit-project-path");
    const button = byId("edit-project-path-pick");
    const previousText = button.textContent;
    button.disabled = true;
    button.textContent = t("pick_directory_in_progress");
    try {
      const payload = await pickProjectDirectory(input.value.trim());
      if (!payload.cancelled && payload.path) {
        input.value = payload.path;
      }
    } catch (error) {
      showToast(error.message, true);
    } finally {
      button.disabled = false;
      button.textContent = previousText;
    }
  });

  byId("btn-accounts").addEventListener("click", () => {
    renderAccountList();
    openDialog("dialog-accounts");
  });
  byId("accounts-close").addEventListener("click", () => closeDialog("dialog-accounts"));
  byId("form-add-account").addEventListener("submit", onAddAccountSubmit);

  byId("btn-open-project").addEventListener("click", () => {
    renderOpenProjectList();
    openDialog("dialog-open-project");
  });
  byId("open-project-close").addEventListener("click", () => closeDialog("dialog-open-project"));

  byId("btn-history").addEventListener("click", async () => {
    fillSessionProjectSelect();
    openDialog("dialog-sessions");
    const first = byId("session-project-select").value;
    if (first) {
      await renderSessions(first);
    } else {
      byId("session-list").innerHTML =
        `<div class="list-row"><div class="list-main"><strong>${escapeHtml(
          t("no_projects")
        )}</strong></div></div>`;
    }
  });
  byId("sessions-close").addEventListener("click", () => closeDialog("dialog-sessions"));

  byId("session-project-select").addEventListener("change", async (event) => {
    const projectId = event.target.value;
    if (!projectId) return;
    await renderSessions(projectId);
  });
  byId("session-filter-apply").addEventListener("click", async () => {
    const projectId = byId("session-project-select").value;
    if (!projectId) return;
    await renderSessions(projectId);
  });
  byId("session-filter-reset").addEventListener("click", async () => {
    byId("session-search").value = "";
    byId("session-date-from").value = "";
    byId("session-date-to").value = "";
    const projectId = byId("session-project-select").value;
    if (!projectId) return;
    await renderSessions(projectId);
  });
  byId("session-search").addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const projectId = byId("session-project-select").value;
    if (!projectId) return;
    await renderSessions(projectId);
  });

  byId("project-grid").addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const action = target.dataset.action;
    const id = target.dataset.id;
    if (!action || !id) return;

    if (action === "open") {
      try {
        await openProject(id);
        showToast(t("toast_project_terminal_started"));
      } catch (error) {
        showToast(error.message, true);
      }
      return;
    }

    if (action === "sessions") {
      openDialog("dialog-sessions");
      fillSessionProjectSelect();
      byId("session-project-select").value = id;
      await renderSessions(id);
      return;
    }

    if (action === "edit") {
      openEditProjectDialog(id);
      return;
    }

    if (action === "delete") {
      if (!confirm(t("confirm_delete_project"))) return;
      try {
        await deleteProject(id);
        await bootstrap();
        showToast(t("toast_project_deleted"));
      } catch (error) {
        showToast(error.message, true);
      }
    }
  });

  byId("account-list").addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const quotaAccountId = target.dataset.accountQuotaRefresh;
    if (quotaAccountId) {
      await refreshAccountQuota(quotaAccountId, true);
      return;
    }

    const accountId = target.dataset.accountDelete;
    if (!accountId) return;
    if (!confirm(t("confirm_delete_account"))) return;
    try {
      await deleteAccount(accountId);
      delete state.accountQuotas[accountId];
      delete state.accountQuotaLoading[accountId];
      await bootstrap();
      renderAccountList();
      showToast(t("toast_account_deleted"));
    } catch (error) {
      showToast(error.message, true);
    }
  });

  byId("open-project-list").addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const projectId = target.dataset.projectOpen;
    if (!projectId) return;
    try {
      await openProject(projectId);
      showToast(t("toast_project_terminal_started"));
    } catch (error) {
      showToast(error.message, true);
    }
  });

  byId("session-list").addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const projectId = target.dataset.sessionProject;
    const sessionId = target.dataset.sessionId;
    if (!projectId || !sessionId) return;
    if (target.dataset.sessionOpen === "1") {
      try {
        await openSession(projectId, sessionId);
        showToast(t("toast_session_opened"));
      } catch (error) {
        showToast(error.message, true);
      }
      return;
    }

    if (target.dataset.sessionPreview === "1") {
      await openSessionPreviewDialog(projectId, sessionId);
      return;
    }

    if (target.dataset.sessionDelete === "1") {
      try {
        const planPayload = await planDeleteSession(projectId, sessionId);
        const plan = planPayload.plan || {};
        const title = plan.title || sessionId;
        const filesCount = plan.files_count || 0;
        if (!confirm(t("confirm_delete_session", { title, count: filesCount }))) {
          return;
        }
        const payload = await deleteSession(projectId, sessionId, true);
        await renderSessions(projectId);
        showToast(payload.message || t("toast_session_deleted"));
      } catch (error) {
        showToast(error.message, true);
      }
    }
  });

  byId("trash-session-list").addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const projectId = target.dataset.trashProject;
    const sessionId = target.dataset.trashSessionId;
    if (!projectId || !sessionId) return;

    if (target.dataset.trashRestore === "1" || target.dataset.trashRestoreOpen === "1") {
      const openAfterRestore = target.dataset.trashRestoreOpen === "1";
      const actionText = openAfterRestore ? t("action_restore_open") : t("action_restore");
      if (!confirm(t("confirm_restore_session", { action: actionText }))) return;
      try {
        const payload = await restoreTrashedSession(projectId, sessionId, openAfterRestore);
        await renderTrashSessions(projectId);
        await refreshHistoryIfVisible(projectId);
        showToast(payload.message || t("toast_session_restored"));
      } catch (error) {
        showToast(error.message, true);
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadUISettings();
  bindEvents();
  try {
    await bootstrap();
  } catch (error) {
    showToast(error.message, true);
  }
});
