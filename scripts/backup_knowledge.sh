#!/bin/bash
# ================================================================
# 知识库 Git 自动备份脚本
# 遍历所有 Obsidian vault, 执行 git add -A && git commit
#
# 用法:
#   bash scripts/backup_knowledge.sh          # 手动执行一次
#   bash scripts/backup_knowledge.sh --push   # 备份并推送到 remote
#
# 定时任务 (launchd / cron):
#   建议每天执行一次。见 setup_backup_cron.sh
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Obsidian vault 路径
VAULTS=(
    "$HOME/Documents/trae_projects/obsidian/laoNianYiXue"
    "$HOME/Documents/trae_projects/obsidian/miNiaoWaiKe"
)

# 可选: 公司项目目录 (包含了所有 Agent 定义和 SOP)
PROJECT_DIR="$HOME/Documents/trae_projects/my-ai-writer"

PUSH=false
if [ "$1" = "--push" ]; then
    PUSH=true
fi

commit_and_push() {
    local repo_path="$1"
    local repo_name="$2"

    if [ ! -d "$repo_path/.git" ]; then
        echo "⊙ $repo_name: 非 git 仓库, 跳过 ($repo_path)"
        return
    fi

    cd "$repo_path"

    # 检查是否有变更
    if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
        echo "✓ $repo_name: 无变更"
        return
    fi

    git add -A
    if git commit -m "auto-backup: $TIMESTAMP" 2>/dev/null; then
        echo "✓ $repo_name: 已提交"
    else
        echo "✓ $repo_name: 无新变更 (add 后无 diff)"
    fi

    if $PUSH; then
        if git push 2>/dev/null; then
            echo "  ↳ 已推送"
        else
            echo "  ⚠️ 推送失败 (检查 remote 配置)"
        fi
    fi
}

echo "=== 知识库备份 ==="
echo "时间: $TIMESTAMP"
echo ""

for vault in "${VAULTS[@]}"; do
    if [ -d "$vault" ]; then
        name=$(basename "$vault")
        commit_and_push "$vault" "$name"
    else
        echo "⊙ $vault: 目录不存在, 跳过"
    fi
done

# 同时备份公司项目 (Agent 定义 + SOP + SKILL)
if [ -d "$PROJECT_DIR/.git" ]; then
    commit_and_push "$PROJECT_DIR" "my-ai-writer (公司项目)"
fi

echo ""
echo "=== 备份完成 ==="
