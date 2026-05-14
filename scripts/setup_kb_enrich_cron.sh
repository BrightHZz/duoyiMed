#!/usr/bin/env bash
# 知识库自主富化 — 定时任务安装脚本
# 支持 macOS (launchd) 和 Linux (crontab)
#
# 用法:
#   bash scripts/setup_kb_enrich_cron.sh              # 安装
#   bash scripts/setup_kb_enrich_cron.sh --uninstall  # 卸载
#   bash scripts/setup_kb_enrich_cron.sh --status     # 查看状态
#
# 频率: 每周执行 3 次 (周一/三/五 08:07)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LABEL="com.geriatrics-research.kb-enrich"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_FILE="/tmp/${LABEL}.log"

# 检查 MAW_PROJECT_ROOT 环境变量
MAW_ROOT="${MAW_PROJECT_ROOT:-$PROJECT_ROOT}"

ACTION="${1:-install}"

# ================================================================
# macOS — launchd
# ================================================================

install_macos() {
    echo "[setup_kb_enrich_cron] 平台: macOS — 安装 launchd 定时任务"

    # 确保使用正确的 Python 路径
    PYTHON_BIN="$(which python3 || which python)"
    echo "  Python: $PYTHON_BIN"
    echo "  项目路径: $MAW_ROOT"

    cat > "$PLIST_PATH" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        <string>${MAW_ROOT}/run_research.py</string>
        <string>--workflow</string>
        <string>kb_enrich</string>
        <string>--division</string>
        <string>all</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${MAW_ROOT}</string>

    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Weekday</key>
            <integer>1</integer>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>7</integer>
        </dict>
        <dict>
            <key>Weekday</key>
            <integer>3</integer>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>7</integer>
        </dict>
        <dict>
            <key>Weekday</key>
            <integer>5</integer>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>7</integer>
        </dict>
    </array>

    <key>StandardOutPath</key>
    <string>${LOG_FILE}</string>

    <key>StandardErrorPath</key>
    <string>${LOG_FILE}</string>

    <key>RunAtLoad</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>MAW_PROJECT_ROOT</key>
        <string>${MAW_ROOT}</string>
    </dict>
</dict>
</plist>
PLIST_EOF

    # 卸载旧版本 (如果存在)
    launchctl unload "$PLIST_PATH" 2>/dev/null || true

    # 加载
    launchctl load "$PLIST_PATH"
    echo "  ✅ launchd 任务已安装并加载"
    echo "  日志: $LOG_FILE"
    echo ""
    echo "  下次执行: 下个周一/三/五 08:07"
    echo "  手动触发: launchctl start ${LABEL}"
    echo "  查看状态: bash $0 --status"
    echo "  卸载:     bash $0 --uninstall"
}

uninstall_macos() {
    echo "[setup_kb_enrich_cron] 卸载 macOS launchd 任务"
    if [ -f "$PLIST_PATH" ]; then
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        rm -f "$PLIST_PATH"
        echo "  ✅ 已卸载并删除 $PLIST_PATH"
    else
        echo "  未找到已安装的任务 ($PLIST_PATH)"
    fi
}

status_macos() {
    echo "[setup_kb_enrich_cron] macOS launchd 状态"
    if [ -f "$PLIST_PATH" ]; then
        echo "  plist: $PLIST_PATH (已安装)"
        launchctl list "$LABEL" 2>/dev/null && echo "  状态: 已加载" || echo "  状态: 已安装但未加载"
    else
        echo "  未安装"
    fi
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "  最近日志 (tail -10):"
        tail -10 "$LOG_FILE" | sed 's/^/    /'
    fi
}

# ================================================================
# Linux — crontab
# ================================================================

CRON_MARKER="# kb-enrich-cron (managed by setup_kb_enrich_cron.sh)"
CRON_ENTRY="7 8 * * 1,3,5 cd ${MAW_ROOT} && ${PYTHON_BIN:-python3} run_research.py --workflow kb_enrich --division all >> /tmp/${LABEL}.log 2>&1 ${CRON_MARKER}"

install_linux() {
    echo "[setup_kb_enrich_cron] 平台: Linux — 安装 crontab 定时任务"

    PYTHON_BIN="$(which python3 || which python)"
    echo "  Python: $PYTHON_BIN"
    echo "  项目路径: $MAW_ROOT"

    # 移除旧条目
    crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab - 2>/dev/null || true

    # 添加新条目
    (crontab -l 2>/dev/null || true; echo "7 8 * * 1,3,5 cd ${MAW_ROOT} && ${PYTHON_BIN} run_research.py --workflow kb_enrich --division all >> /tmp/${LABEL}.log 2>&1 ${CRON_MARKER}") | crontab -

    echo "  ✅ crontab 任务已安装"
    echo "  日志: /tmp/${LABEL}.log"
    echo ""
    echo "  下次执行: 下个周一/三/五 08:07"
    echo "  查看状态: crontab -l"
    echo "  卸载:     bash $0 --uninstall"
}

uninstall_linux() {
    echo "[setup_kb_enrich_cron] 卸载 Linux crontab 任务"
    crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab - 2>/dev/null || true
    echo "  ✅ 已从 crontab 中移除"
}

status_linux() {
    echo "[setup_kb_enrich_cron] Linux crontab 状态"
    if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
        echo "  已安装:"
        crontab -l 2>/dev/null | grep "$CRON_MARKER" | sed 's/^/    /'
    else
        echo "  未安装"
    fi
}

# ================================================================
# 主逻辑
# ================================================================

case "$(uname -s)" in
    Darwin)
        case "$ACTION" in
            install)   install_macos ;;
            --uninstall) uninstall_macos ;;
            --status)   status_macos ;;
            *) echo "用法: $0 [install|--uninstall|--status]"; exit 1 ;;
        esac
        ;;
    Linux)
        case "$ACTION" in
            install)   install_linux ;;
            --uninstall) uninstall_linux ;;
            --status)   status_linux ;;
            *) echo "用法: $0 [install|--uninstall|--status]"; exit 1 ;;
        esac
        ;;
    *)
        echo "不支持的操作系统: $(uname -s)"
        exit 1
        ;;
esac
