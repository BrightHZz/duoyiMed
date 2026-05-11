#!/bin/bash
# ================================================================
# 知识库定时备份 — 设置指南
#
# macOS 推荐使用 launchd (每天定时执行备份脚本)
# Linux 使用 cron
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_knowledge.sh"

chmod +x "$BACKUP_SCRIPT"

echo "知识库定时备份设置"
echo "=================="
echo ""
echo "备份脚本: $BACKUP_SCRIPT"
echo ""

# ================================================================
# macOS: launchd
# ================================================================

if [[ "$OSTYPE" == "darwin"* ]]; then
    PLIST_NAME="com.geriatrics-research.knowledge-backup"
    PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

    cat > "$PLIST_PATH" << LAUNCHD
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${BACKUP_SCRIPT}</string>
    </array>
    <!-- 每天凌晨 2:00 执行 -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/${PLIST_NAME}.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/${PLIST_NAME}.err</string>
</dict>
</plist>
LAUNCHD

    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH" 2>/dev/null

    echo "✅ launchd 定时任务已设置"
    echo "   执行时间: 每天 2:00 AM"
    echo "   日志: /tmp/${PLIST_NAME}.log"
    echo ""
    echo "手动测试: bash $BACKUP_SCRIPT"
    echo "停止任务: launchctl unload $PLIST_PATH"
    echo "查看日志: cat /tmp/${PLIST_NAME}.log"

# ================================================================
# Linux: cron
# ================================================================

elif [[ "$OSTYPE" == "linux"* ]]; then
    CRON_LINE="0 2 * * * /bin/bash $BACKUP_SCRIPT >> /tmp/knowledge-backup.log 2>&1"

    if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
        echo "⊙ cron 任务已存在"
    else
        (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
        echo "✅ cron 定时任务已设置"
        echo "   执行时间: 每天 2:00 AM"
        echo "   日志: /tmp/knowledge-backup.log"
    fi

else
    echo "⚠️  未知操作系统: $OSTYPE"
    echo "   请手动设置定时任务: bash $BACKUP_SCRIPT"
fi

echo ""
echo "=== 设置完成 ==="
echo ""
echo "立即执行一次备份测试:"
echo "  bash $BACKUP_SCRIPT"
