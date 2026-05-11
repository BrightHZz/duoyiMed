"""
轻量级 .env 文件加载器 — 零外部依赖。

加载顺序 (后面的覆盖前面的):
  1. $MAW_PROJECT_ROOT/.env  — 项目级配置
  2. ~/.maw.env                — 用户级配置
  3. os.environ                — 系统环境变量

用法:
    from engine.core.env import load_dotenv, resolve_path

    load_dotenv(project_root)
    data_dir = resolve_path("CHARLS_DATA_DIR", "{MAW_DATA_HOME}/charls")
"""

import os
import re
from pathlib import Path
from typing import Optional


def _expand_env_vars(value: str) -> str:
    """展开字符串中的 $VAR 和 ${VAR} 引用"""
    def _replace(match):
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, "")
    return re.sub(r'\$\{(\w+)\}|\$(\w+)', _replace, value)


def parse_env_file(filepath: Path) -> dict[str, str]:
    """解析 .env 文件, 返回 {KEY: VALUE} dict。忽略空行和注释。"""
    result = {}
    if not filepath.exists():
        return result

    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # KEY=VALUE or KEY="VALUE" or KEY='VALUE'
        match = re.match(r'^(\w+)\s*=\s*(.+)$', line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        # 去掉引号
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        # 展开 $VAR 引用
        value = _expand_env_vars(value)
        result[key] = value
    return result


def load_dotenv(project_root: Optional[Path] = None) -> None:
    """
    按优先级加载 .env 文件到 os.environ (系统环境变量优先级最高, 不会被覆盖)。

    加载顺序:
      1. $MAW_PROJECT_ROOT/.env (如果 MAW_PROJECT_ROOT 已设 → 用该值; 否则用 filesystem project_root)
      2. ~/.maw.env
      3. os.environ (已在进程启动时加载, 优先级最高)

    Args:
        project_root: 项目根目录 (从 filesystem 检测), 仅当 MAW_PROJECT_ROOT 未设时使用
    """
    if project_root is None:
        project_root = _detect_project_root()

    # 确定真正的项目根: env var 优先于 filesystem 检测
    env_project_root = os.environ.get("MAW_PROJECT_ROOT", "")
    if env_project_root:
        effective_root = Path(os.path.expanduser(env_project_root))
    else:
        effective_root = project_root

    # 确保 MAW_PROJECT_ROOT 已设
    os.environ.setdefault("MAW_PROJECT_ROOT", str(effective_root.resolve()))

    # 1. 项目 .env: setdefault → 不覆盖已在 os.environ 中的值
    project_env = effective_root / ".env"
    if project_env.exists():
        for k, v in parse_env_file(project_env).items():
            os.environ.setdefault(k, v)

    # 如未设 MAW_OBSIDIAN_HOME 和 MAW_DATA_HOME, 基于 MAW_PROJECT_ROOT 推断
    _infer_defaults()

    # 2. 用户级 ~/.maw.env
    user_env = Path.home() / ".maw.env"
    if user_env.exists():
        for k, v in parse_env_file(user_env).items():
            os.environ.setdefault(k, v)

    # 3. 系统环境变量已在 os.environ 中, 优先级最高, 不做额外处理


def _detect_project_root() -> Path:
    """自动检测项目根目录: 从当前文件向上找到包含 engine/ 的目录"""
    current = Path(__file__).resolve().parent  # engine/core/
    for _ in range(5):
        if (current / "engine" / "core" / "orchestrator_graph.py").exists():
            return current
        current = current.parent
    # fallback: 当前文件向上 2 级
    return Path(__file__).resolve().parent.parent.parent


def _infer_defaults() -> None:
    """为未设置的关键变量推断默认值"""
    project_root = os.environ.get("MAW_PROJECT_ROOT", "")

    # MAW_OBSIDIAN_HOME 默认: 与项目根目录平行的 obsidian/
    if "MAW_OBSIDIAN_HOME" not in os.environ and project_root:
        candidate = Path(project_root).parent / "obsidian"
        if candidate.exists():
            os.environ.setdefault("MAW_OBSIDIAN_HOME", str(candidate))
        else:
            # fallback: ~/Documents/trae_projects/obsidian
            fallback = Path.home() / "Documents" / "trae_projects" / "obsidian"
            os.environ.setdefault("MAW_OBSIDIAN_HOME", str(fallback))

    # MAW_DATA_HOME 默认: ~/Documents/trae_projects/dataset
    if "MAW_DATA_HOME" not in os.environ:
        candidate = Path.home() / "Documents" / "trae_projects" / "dataset"
        os.environ.setdefault("MAW_DATA_HOME", str(candidate))


def resolve_path(env_key: str, default_template: str = "") -> Path:
    """
    解析路径: 从环境变量获取值，未配置时用 default_template 推断。

    default_template 支持 {VAR} 引用已设置的环境变量。
    例如: resolve_path("CHARLS_DATA_DIR", "{MAW_DATA_HOME}/charls")
    """
    value = os.environ.get(env_key, "")
    if not value:
        value = default_template.format(**os.environ)
    # 展开 ~ 和 $VAR
    value = os.path.expanduser(value)
    value = _expand_env_vars(value)
    return Path(value)
