# Clinical Tool Developer — Urology Few-Shot Examples

## Example 1: Prostate Cancer Biochemical Recurrence Prediction → Streamlit Web Tool

### Input

项目: `pca-bcr-prediction`, 事业部: urology
模型文件: `models/lr_final.pkl` (Logistic Regression, AUC=0.891)
数据字典: `data/data_dictionary.md`
cv_results.json: 5-fold CV AUC 0.891 (95% CI: 0.852-0.930), Brier 0.098, Calibration Slope 0.97

特征列表 (来自 data_dictionary.md):
| 编码变量 | 临床名称 | 单位 | 类型 | 范围 |
|---------|---------|------|------|------|
| psa_preop | Preoperative PSA | ng/mL | continuous | 0.1-100 |
| gleason_primary | Primary Gleason Grade | - | integer | 3-5 |
| gleason_secondary | Secondary Gleason Grade | - | integer | 3-5 |
| pT_stage | Pathologic T Stage | - | categorical | pT2/pT3a/pT3b |
| surgical_margin | Positive Surgical Margin | - | binary | 0/1 |
| ece | Extracapsular Extension | - | binary | 0/1 |
| svi | Seminal Vesicle Invasion | - | binary | 0/1 |
| lni | Lymph Node Involvement | - | binary | 0/1 |
| age_surgery | Age at Surgery | years | integer | 40-85 |

### Output — supplements/model_info.json

```json
{
  "project_id": "pca-bcr-prediction",
  "division": "urology",
  "model_type": "logistic_regression",
  "features": [
    {"name": "psa_preop", "clinical_name": "Preoperative PSA", "unit": "ng/mL", "type": "continuous", "min": 0.1, "max": 100.0, "default": 8.0, "importance": 0.28},
    {"name": "gleason_primary", "clinical_name": "Primary Gleason Grade", "unit": "", "type": "categorical", "options": [{"value": 3, "label": "3"}, {"value": 4, "label": "4"}, {"value": 5, "label": "5"}], "default": 3, "importance": 0.22},
    {"name": "gleason_secondary", "clinical_name": "Secondary Gleason Grade", "unit": "", "type": "categorical", "options": [{"value": 3, "label": "3"}, {"value": 4, "label": "4"}, {"value": 5, "label": "5"}], "default": 3, "importance": 0.15},
    {"name": "pt_stage", "clinical_name": "Pathologic T Stage", "unit": "", "type": "categorical", "options": [{"value": 0, "label": "pT2"}, {"value": 1, "label": "pT3a"}, {"value": 2, "label": "pT3b"}], "default": 0, "importance": 0.13},
    {"name": "surgical_margin", "clinical_name": "Positive Surgical Margin", "unit": "", "type": "binary", "options": [{"value": 0, "label": "Negative"}, {"value": 1, "label": "Positive"}], "default": 0, "importance": 0.09},
    {"name": "ece", "clinical_name": "Extracapsular Extension", "unit": "", "type": "binary", "options": [{"value": 0, "label": "Absent"}, {"value": 1, "label": "Present"}], "default": 0, "importance": 0.06},
    {"name": "svi", "clinical_name": "Seminal Vesicle Invasion", "unit": "", "type": "binary", "options": [{"value": 0, "label": "Absent"}, {"value": 1, "label": "Present"}], "default": 0, "importance": 0.04},
    {"name": "lni", "clinical_name": "Lymph Node Involvement", "unit": "", "type": "binary", "options": [{"value": 0, "label": "Negative"}, {"value": 1, "label": "Positive"}], "default": 0, "importance": 0.02},
    {"name": "age_surgery", "clinical_name": "Age at Surgery", "unit": "years", "type": "integer", "min": 40, "max": 85, "default": 65, "importance": 0.01}
  ],
  "coefficients": {
    "intercept": -3.42,
    "psa_preop": 1.24,
    "gleason_primary": 0.87,
    "gleason_secondary": 0.61,
    "pt_stage": 0.93,
    "surgical_margin": 0.55,
    "ece": 0.48,
    "svi": 0.72,
    "lni": 0.41,
    "age_surgery": 0.12
  },
  "performance": {
    "auc": 0.891,
    "auc_ci_low": 0.852,
    "auc_ci_high": 0.930,
    "brier": 0.098,
    "calibration_slope": 0.97
  },
  "output": {
    "description": "5-Year Biochemical Recurrence Risk after Radical Prostatectomy",
    "risk_categories": [
      {"label": "Low Risk", "range": [0, 0.10], "color": "green", "recommendation": "Routine follow-up per NCCN guidelines. PSA monitoring every 6-12 months."},
      {"label": "Intermediate Risk", "range": [0.10, 0.30], "color": "orange", "recommendation": "Closer follow-up. PSA monitoring every 3-6 months. Consider adjuvant therapy discussion."},
      {"label": "High Risk", "range": [0.30, 1.0], "color": "red", "recommendation": "Consider adjuvant or salvage therapy. Discuss with multidisciplinary tumor board. PSA monitoring every 3 months."}
    ]
  }
}
```

### Output — supplements/feature_config.json

```json
{
  "input_groups": [
    {
      "group_name": "Preoperative Parameters",
      "features": [
        {"name": "psa_preop", "clinical_name": "Preoperative PSA", "unit": "ng/mL", "type": "number", "min": 0.1, "max": 100.0, "default": 8.0, "step": 0.1},
        {"name": "age_surgery", "clinical_name": "Age at Surgery", "unit": "years", "type": "number", "min": 40, "max": 85, "default": 65, "step": 1}
      ]
    },
    {
      "group_name": "Pathology — Gleason Grade",
      "features": [
        {"name": "gleason_primary", "clinical_name": "Primary Gleason Grade", "unit": "", "type": "select", "options": [{"value": 3, "label": "3"}, {"value": 4, "label": "4"}, {"value": 5, "label": "5"}], "default": 3},
        {"name": "gleason_secondary", "clinical_name": "Secondary Gleason Grade", "unit": "", "type": "select", "options": [{"value": 3, "label": "3"}, {"value": 4, "label": "4"}, {"value": 5, "label": "5"}], "default": 3}
      ]
    },
    {
      "group_name": "Pathology — Adverse Features",
      "features": [
        {"name": "pt_stage", "clinical_name": "Pathologic T Stage", "unit": "", "type": "select", "options": [{"value": 0, "label": "pT2"}, {"value": 1, "label": "pT3a"}, {"value": 2, "label": "pT3b"}], "default": 0},
        {"name": "surgical_margin", "clinical_name": "Positive Surgical Margin", "unit": "", "type": "select", "options": [{"value": 0, "label": "Negative"}, {"value": 1, "label": "Positive"}], "default": 0},
        {"name": "ece", "clinical_name": "Extracapsular Extension", "unit": "", "type": "select", "options": [{"value": 0, "label": "Absent"}, {"value": 1, "label": "Present"}], "default": 0},
        {"name": "svi", "clinical_name": "Seminal Vesicle Invasion", "unit": "", "type": "select", "options": [{"value": 0, "label": "Absent"}, {"value": 1, "label": "Present"}], "default": 0},
        {"name": "lni", "clinical_name": "Lymph Node Involvement", "unit": "", "type": "select", "options": [{"value": 0, "label": "Negative"}, {"value": 1, "label": "Positive"}], "default": 0}
      ]
    }
  ]
}
```

### Output — supplements/app.py (核心片段)

```python
import streamlit as st
import numpy as np
import json
from pathlib import Path

st.set_page_config(
    page_title="Prostate Cancer BCR Risk Calculator",
    page_icon="🏥",
    layout="wide",
)

@st.cache_resource
def load_model():
    with open(Path(__file__).parent / "model_info.json") as f:
        model_info = json.load(f)
    return model_info

model_info = load_model()

def predict_lr(features, model_info):
    """Logistic regression prediction from exported coefficients."""
    coef = model_info['coefficients']
    logit = coef['intercept']
    for feat, val in zip(model_info['features'], features):
        logit += coef[feat['name']] * val
    return 1.0 / (1.0 + np.exp(-logit))

# Sidebar
with st.sidebar:
    st.header("Model Information")
    st.metric("AUC", f"{model_info['performance']['auc']:.3f}")
    st.caption(f"95% CI: {model_info['performance']['auc_ci_low']:.3f} - {model_info['performance']['auc_ci_high']:.3f}")
    st.caption(f"Calibration Slope: {model_info['performance']['calibration_slope']:.2f}")
    st.divider()
    st.caption("⚠️ **Disclaimer**: This tool is for research and educational purposes only. "
               "It does not constitute medical advice. Treatment decisions should be made "
               "in consultation with a qualified urologist.")

# Main
st.title("5-Year Biochemical Recurrence Risk Calculator")
st.caption("After Radical Prostatectomy — Logistic Regression Model")

with st.expander("📋 Preoperative Parameters", expanded=True):
    col1, col2 = st.columns(2)
    psa = col1.number_input("Preoperative PSA (ng/mL)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
    age = col2.number_input("Age at Surgery", min_value=40, max_value=85, value=65, step=1)

with st.expander("🔬 Gleason Grade"):
    col1, col2 = st.columns(2)
    g_primary = col1.selectbox("Primary Gleason Grade", options=[3, 4, 5], format_func=lambda x: str(x))
    g_secondary = col2.selectbox("Secondary Gleason Grade", options=[3, 4, 5], format_func=lambda x: str(x))

with st.expander("⚠️ Adverse Pathologic Features", expanded=True):
    col1, col2 = st.columns(2)
    pt = col1.selectbox("Pathologic T Stage", options=["pT2", "pT3a", "pT3b"])
    margin = col1.selectbox("Surgical Margin", options=["Negative", "Positive"])
    ece = col2.selectbox("Extracapsular Extension", options=["Absent", "Present"])
    svi = col2.selectbox("Seminal Vesicle Invasion", options=["Absent", "Present"])
    lni = st.selectbox("Lymph Node Involvement", options=["Negative", "Positive"])

if st.button("🔮 Calculate BCR Risk", type="primary", use_container_width=True):
    # Encode features (matching training encoder)
    pt_map = {"pT2": 0, "pT3a": 1, "pT3b": 2}
    features = [
        psa, g_primary, g_secondary,
        pt_map[pt],
        1 if margin == "Positive" else 0,
        1 if ece == "Present" else 0,
        1 if svi == "Present" else 0,
        1 if lni == "Positive" else 0,
        age
    ]
    proba = predict_lr(features, model_info)

    risk_cats = model_info['output']['risk_categories']
    cat = risk_cats[0]
    for rc in risk_cats:
        if rc['range'][0] <= proba < rc['range'][1]:
            cat = rc
            break

    st.divider()
    col1, col2 = st.columns([1, 2])
    color_map = {"green": "🟢", "orange": "🟠", "red": "🔴"}
    col1.metric("5-Year BCR Risk", f"{proba:.1%}")
    col1.caption(f"{color_map.get(cat['color'], '')} {cat['label']}")
    col2.info(cat['recommendation'])

    # Show Gleason Score
    st.caption(f"Gleason Score: {g_primary}+{g_secondary}={g_primary + g_secondary} "
               f"(Grade Group: {(g_primary + g_secondary - 2) if g_primary + g_secondary <= 10 else 5})")
```

### Quality Checklist 结果

- [x] 模型系数可正常加载和预测 (Logistic Regression via JSON coefficients, no pickle dependency)
- [x] model_info.json 特征数 = 9 (模型期望 9)
- [x] feature_config.json 每个特征含 clinical_name
- [x] app.py 可正常启动 (`streamlit run`)
- [x] 输入表单按 Preoperative / Gleason / Adverse Features 分组
- [x] 输出区含 BCR 风险概率 + 风险分类 + Gleason Score 显示
- [x] 安全免责声明在侧边栏底部 (含 urology-specific 措辞)
- [x] 异常输入有警告但不阻断
- [x] requirements.txt 可正常安装
- [x] Dockerfile 可构建
- [x] build_exe.py 可正常打包
- [x] README.md 部署说明完整
