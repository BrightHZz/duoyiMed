"""
精确舍入工具 — 使用 Decimal + ROUND_HALF_UP 避免 IEEE 754 浮点误差。

问题: round(0.7595, 3) 在 Python 中返回 0.759, 因为 0.7595 存储为 0.75949999999999995293。
解决: Decimal(str(value)).quantize(...) 精确按十进制四舍五入。

精度标准与 SKILL.md "数值精度规范" 对齐 (2026-05-13)。
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union

# 精度标准: 指标类型 → 小数位数 (与 SKILL.md 保持一致)
PRECISION = {
    "auc": 3,           # AUC / C-statistic / C-index → 0.842
    "p_value": 3,       # p 值 → 0.032 (p < 0.001 除外)
    "or": 2,            # Odds Ratio → 1.34
    "hr": 2,            # Hazard Ratio → 0.78
    "rr": 2,            # Risk Ratio → 1.25
    "percentage": 1,    # 百分比 → 84.2%
    "effect_size": 2,   # Cohen's d / Hedges' g → 0.45
    "sample_size": 0,   # 样本量/计数 → 整数
    "sd": None,         # SD/SE → 比均值多 1 位 (需调用方指定)
    "ci": None,         # 95% CI → 与点估计一致 (需调用方指定)
}

# 常用精度别名
AUC_PRECISION = 3       # 区分度指标
RATIO_PRECISION = 2     # OR/HR/RR
PCT_PRECISION = 1       # 百分比
EFFECT_PRECISION = 2    # Cohen's d, Hedges' g
PVALUE_PRECISION = 3    # p 值


def round_half_up(value: float, decimals: int = 3) -> float:
    """精确四舍五入, 避免 IEEE 754 浮点误差。

    round(0.7595, 3) → 0.759  ❌ (存储为 0.75949999999999995293)
    round_half_up(0.7595, 3) → 0.760  ✅

    Args:
        value: 要舍入的数值
        decimals: 保留小数位数

    Returns:
        舍入后的 float 值

    Examples:
        >>> round_half_up(0.7595, 3)
        0.76
        >>> round_half_up(0.8423, 3)
        0.842
        >>> round_half_up(1.345, 2)
        1.35
        >>> round_half_up(1234, 0)
        1234.0
    """
    quantize = Decimal('0.' + '0' * decimals) if decimals > 0 else Decimal('1')
    return float(Decimal(str(value)).quantize(quantize, rounding=ROUND_HALF_UP))


def format_value(value: float, decimals: int = 3) -> str:
    """舍入并格式化为指定小数位数的字符串 (补零)。

    Args:
        value: 要格式化的数值
        decimals: 保留小数位数

    Returns:
        格式化后的字符串

    Examples:
        >>> format_value(0.76, 3)
        '0.760'
        >>> format_value(0.8423, 3)
        '0.842'
    """
    rounded = round_half_up(value, decimals)
    if decimals == 0:
        return str(int(rounded))
    return f"{rounded:.{decimals}f}"
