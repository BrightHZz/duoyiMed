"""
项目脚本标准模板 — generate_figures.py / generate_tables.py 的标准骨架。

每个项目的图表生成脚本必须包含:
  1. --project-dir 参数解析 (接收 Phase6Runner 传入的项目目录)
  2. 从 cv_results.json 读取数据 (基线合规: 禁止从模型对象重新提取)
  3. 数值精度舍入 (调用 engine.utils.rounding)
  4. 输出到 project_dir/figures/ 或 project_dir/tables/

ml-engineer 生成脚本时应基于此模板扩展图表/表格逻辑。

用法:
    python generate_figures.py --project-dir /path/to/project
    python generate_tables.py --project-dir /path/to/project
"""

import os
import sys
import json
import argparse
from pathlib import Path

# ================================================================
# 引擎路径注入
# ================================================================
# Phase6Runner 已将 ENGINE_ROOT 注入 PYTHONPATH, 无需手动设置。
# 如果直接运行此脚本, 取消下面的注释:
# ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent
# sys.path.insert(0, str(ENGINE_ROOT))

from engine.utils.rounding import round_half_up, format_value, PRECISION


# ================================================================
# 路径工具
# ================================================================

def resolve_project_dir() -> Path:
    """解析项目目录: --project-dir > 当前目录"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--project-dir", type=Path, default=None,
                        help="项目工作目录 (Phase6Runner 自动传入)")
    args, _ = parser.parse_known_args()
    if args.project_dir:
        return Path(args.project_dir)
    return Path.cwd()


def load_cv_results(project_dir: Path) -> dict:
    """从 Phase 3 基线加载 cv_results.json (强制基线合规)"""
    cv_path = project_dir / "cv_results.json"
    if not cv_path.exists():
        # fallback: models/ 子目录
        alt = project_dir / "models" / "cv_results.json"
        if alt.exists():
            cv_path = alt
        else:
            raise FileNotFoundError(
                f"cv_results.json 未找到于 {project_dir}/ 或 {project_dir}/models/\n"
                f"请确保 Phase 3 已生成 cv_results.json。"
            )
    with open(cv_path) as f:
        return json.load(f)


def ensure_output_dir(project_dir: Path, subdir: str) -> Path:
    """创建输出目录并返回。"""
    out = project_dir / subdir
    out.mkdir(parents=True, exist_ok=True)
    return out


# ================================================================
# 辅助: 数值精度 (从 cv_results.json 安全提取)
# ================================================================

def get_auc(results: dict, model_name: str = None) -> dict:
    """提取 AUC 值, 自动按精度标准舍入。"""
    models = results.get("models", {})
    if model_name is None:
        model_name = results.get("best_model", list(models.keys())[0])
    m = models.get(model_name, {})
    auc = m.get("auc", {})
    return {
        "mean": round_half_up(auc.get("mean", 0), PRECISION["auc"]),
        "ci_low": round_half_up(auc.get("ci_low", 0), PRECISION["auc"]),
        "ci_high": round_half_up(auc.get("ci_high", 0), PRECISION["auc"]),
    }


def get_feature_importance(results: dict, model_name: str = None) -> dict:
    """提取特征重要性 (按值降序)。"""
    models = results.get("models", {})
    if model_name is None:
        model_name = results.get("best_model", list(models.keys())[0])
    fi = models.get(model_name, {}).get("feature_importance", {})
    return dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))


# ================================================================
# 主入口骨架 (ml-engineer 在此处扩展图表/表格逻辑)
# ================================================================

def main():
    parser = argparse.ArgumentParser(
        description="项目图表生成脚本 (基于 engine/templates/project_script_boilerplate.py)"
    )
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="项目工作目录 (Phase6Runner 自动传入)")
    args = parser.parse_args()

    project_dir = args.project_dir
    cv_results = load_cv_results(project_dir)

    # === 以下为 ml-engineer 扩展区域 ===
    # 示例: 生成 ROC 曲线、校准图、特征重要性图
    # 参考本模板中的 get_auc(), get_feature_importance() 等辅助函数
    # 输出文件必须使用 Figure[N]_ 前缀命名
    # ====================================

    print(f"[generate_figures.py] project_dir={project_dir}")
    print(f"  best_model: {cv_results.get('best_model', '?')}")
    # TODO: ml-engineer 在此处添加实际图表生成逻辑

    # ====================================
    print("[generate_figures.py] 完成。")


if __name__ == "__main__":
    main()
