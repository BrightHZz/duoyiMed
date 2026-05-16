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
    # 生成 ROC / 校准曲线 / 特征重要性图
    # 输出文件必须使用 Figure[N]_ 前缀命名
    # ====================================

    print(f"[generate_figures.py] project_dir={project_dir}")
    print(f"  best_model: {cv_results.get('best_model', '?')}")

    # --- 美学基线: seaborn 样式 + 出版级参数 ---
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    STYLE = {
        "figsize": (7, 5.5),
        "dpi": 300,
        "color_main": "#2166ac",
        "font_label": 11,
        "font_tick": 10,
        "spine_color": "#cccccc",
        "spine_width": 0.5,
    }

    def apply_style(ax):
        """统一应用出版级图表样式"""
        sns.set_style("whitegrid")
        sns.set_context("paper", font_scale=1.1)
        ax.tick_params(labelsize=STYLE["font_tick"])
        for spine in ax.spines.values():
            spine.set_edgecolor(STYLE["spine_color"])
            spine.set_linewidth(STYLE["spine_width"])

    def add_legend(ax):
        """图例统一放在右下角, 带边框和透明度"""
        ax.legend(loc='lower right', frameon=True, framealpha=0.9,
                  edgecolor='#dddddd', fontsize=10, borderpad=0.8)

    figures_dir = ensure_output_dir(project_dir, "figures")
    model_name = cv_results.get("best_model", list(cv_results.get("models", {}).keys())[0])

    # ================================================================
    # Figure 2: ROC Curve
    # ================================================================
    try:
        from sklearn.metrics import roc_curve, auc
        models = cv_results.get("models", {})
        fig, ax = plt.subplots(figsize=STYLE["figsize"])
        apply_style(ax)
        for name, m in models.items():
            fpr = np.array(m.get("roc_fpr", []))
            tpr = np.array(m.get("roc_tpr", []))
            roc_auc = m.get("auc", {}).get("mean", auc(fpr, tpr) if len(fpr) > 0 else 0)
            if len(fpr) > 0:
                ax.plot(fpr, tpr, lw=2.5, label=f'{name} (AUC = {roc_auc:.3f})')
                ax.fill_between(fpr, tpr, alpha=0.05)
        ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.6, label='Random')
        ax.set_xlabel('1 − Specificity (FPR)', fontsize=STYLE["font_label"])
        ax.set_ylabel('Sensitivity (TPR)', fontsize=STYLE["font_label"])
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        add_legend(ax)
        fig.tight_layout(pad=1.5)
        roc_path = figures_dir / "Figure2_roc-curve.png"
        fig.savefig(roc_path, dpi=STYLE["dpi"], bbox_inches='tight')
        plt.close()
        print(f"  ✓ {roc_path}")
    except Exception as e:
        print(f"  ✗ Figure 2 失败: {e}")

    # ================================================================
    # Figure 3: Calibration Plot
    # ================================================================
    try:
        from sklearn.calibration import calibration_curve
        fig, ax = plt.subplots(figsize=STYLE["figsize"])
        apply_style(ax)
        for name, m in models.items():
            y_true = np.array(m.get("calib_y_true", []))
            y_prob = np.array(m.get("calib_y_prob", []))
            if len(y_true) > 0 and len(y_prob) > 0:
                frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=10)
                ax.plot(mean_pred, frac_pos, 'o-', lw=2.5, color=STYLE["color_main"],
                        markersize=7, markerfacecolor='white', markeredgewidth=1.5,
                        markeredgecolor=STYLE["color_main"], label=name)
        ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.6, label='Perfect calibration')
        ax.set_xlabel('Predicted Probability', fontsize=STYLE["font_label"])
        ax.set_ylabel('Observed Proportion', fontsize=STYLE["font_label"])
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        add_legend(ax)
        fig.tight_layout(pad=1.5)
        cal_path = figures_dir / "Figure3_calibration-plot.png"
        fig.savefig(cal_path, dpi=STYLE["dpi"], bbox_inches='tight')
        plt.close()
        print(f"  ✓ {cal_path}")
    except Exception as e:
        print(f"  ✗ Figure 3 失败: {e}")

    # ================================================================
    # Figure 4: Feature Importance (SHAP)
    # ================================================================
    try:
        fi = get_feature_importance(cv_results, model_name)
        names = list(fi.keys())
        values = list(fi.values())
        sorted_idx = np.argsort(values)
        names_sorted = [names[i] for i in sorted_idx]
        values_sorted = [values[i] for i in sorted_idx]

        colors = sns.color_palette("Blues_d", n_colors=len(values_sorted))
        fig, ax = plt.subplots(figsize=(8, max(5, len(names_sorted) * 0.35)))
        apply_style(ax)
        ax.barh(range(len(values_sorted)), values_sorted, color=colors,
                edgecolor='white', linewidth=0.5, height=0.7)
        ax.set_yticks(range(len(values_sorted)))
        ax.set_yticklabels(names_sorted, fontsize=10)
        ax.set_xlabel('Mean |SHAP|', fontsize=STYLE["font_label"])
        for i, (val, name) in enumerate(zip(values_sorted, names_sorted)):
            ax.text(val + max(values_sorted) * 0.01, i, f'{val:.4f}',
                    va='center', fontsize=8, color='#333333')
        fig.tight_layout(pad=1.5)
        shap_path = figures_dir / "Figure4_feature-importance.png"
        fig.savefig(shap_path, dpi=STYLE["dpi"], bbox_inches='tight')
        plt.close()
        print(f"  ✓ {shap_path}")
    except Exception as e:
        print(f"  ✗ Figure 4 失败: {e}")

    # ====================================
    print("[generate_figures.py] 完成。")


if __name__ == "__main__":
    main()
