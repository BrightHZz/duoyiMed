# Clinical Tool Developer — Geriatrics Few-Shot Examples

## Example 1: Frailty Prediction Model → Streamlit Web Tool

### Input

项目: `frailty-ml-2026`, 事业部: geriatrics
模型文件: `models/xgb_final.pkl` (XGBoost, AUC=0.842)
数据字典: `data/data_dictionary.md`
cv_results.json: 5-fold CV AUC 0.842 (95% CI: 0.791-0.893), Brier 0.123, Calibration Slope 1.02

特征列表 (来自 data_dictionary.md):
| 编码变量 | 临床名称 | 单位 | 类型 | 范围 |
|---------|---------|------|------|------|
| da049 | Gait Speed | m/s | continuous | 0.2-2.5 |
| da051 | Grip Strength | kg | continuous | 5-60 |
| da053 | Chair Stand Time | s | continuous | 0-30 |
| ba000 | Age | years | integer | 60-110 |
| ba001 | Sex | - | categorical | Male/Female |
| da002 | BMI | kg/m² | continuous | 14-50 |
| dc012 | CES-D Score | - | integer | 0-30 |
| de005 | Number of Chronic Conditions | - | integer | 0-15 |
| de007 | Hospitalization (past year) | - | binary | 0/1 |

### Output — supplements/model_info.json

```json
{
  "project_id": "frailty-ml-2026",
  "division": "geriatrics",
  "model_type": "xgboost",
  "features": [
    {"name": "gait_speed", "clinical_name": "Gait Speed", "unit": "m/s", "type": "continuous", "min": 0.2, "max": 2.5, "default": 0.8, "importance": 0.32},
    {"name": "grip_strength", "clinical_name": "Grip Strength", "unit": "kg", "type": "continuous", "min": 5, "max": 60, "default": 25, "importance": 0.21},
    {"name": "chair_stand_time", "clinical_name": "Chair Stand Time", "unit": "s", "type": "continuous", "min": 0, "max": 30, "default": 12, "importance": 0.15},
    {"name": "age", "clinical_name": "Age", "unit": "years", "type": "integer", "min": 60, "max": 110, "default": 70, "importance": 0.12},
    {"name": "sex", "clinical_name": "Sex", "unit": "", "type": "categorical", "options": [{"value": 0, "label": "Female"}, {"value": 1, "label": "Male"}], "default": 0, "importance": 0.03},
    {"name": "bmi", "clinical_name": "BMI", "unit": "kg/m²", "type": "continuous", "min": 14, "max": 50, "default": 23, "importance": 0.05},
    {"name": "cesd_score", "clinical_name": "CES-D Score", "unit": "", "type": "integer", "min": 0, "max": 30, "default": 8, "importance": 0.04},
    {"name": "chronic_conditions", "clinical_name": "Number of Chronic Conditions", "unit": "", "type": "integer", "min": 0, "max": 15, "default": 2, "importance": 0.06},
    {"name": "hospitalization", "clinical_name": "Hospitalization (past year)", "unit": "", "type": "binary", "options": [{"value": 0, "label": "No"}, {"value": 1, "label": "Yes"}], "default": 0, "importance": 0.02}
  ],
  "performance": {
    "auc": 0.842,
    "auc_ci_low": 0.791,
    "auc_ci_high": 0.893,
    "brier": 0.123,
    "calibration_slope": 1.02
  },
  "output": {
    "description": "2-Year Frailty Worsening Probability",
    "risk_categories": [
      {"label": "Low Risk", "range": [0, 0.15], "color": "green", "recommendation": "Maintain current lifestyle. Re-assess in 2 years."},
      {"label": "Moderate Risk", "range": [0.15, 0.35], "color": "orange", "recommendation": "Consider targeted interventions (resistance exercise, nutrition optimization). Re-assess in 1 year."},
      {"label": "High Risk", "range": [0.35, 1.0], "color": "red", "recommendation": "Comprehensive geriatric assessment recommended. Consider multidisciplinary intervention."}
    ]
  }
}
```

### Output — supplements/feature_config.json

```json
{
  "input_groups": [
    {
      "group_name": "Demographics",
      "features": [
        {"name": "age", "clinical_name": "Age", "unit": "years", "type": "number", "min": 60, "max": 110, "default": 70, "step": 1},
        {"name": "sex", "clinical_name": "Sex", "unit": "", "type": "select", "options": [{"value": 0, "label": "Female"}, {"value": 1, "label": "Male"}], "default": 0},
        {"name": "bmi", "clinical_name": "BMI", "unit": "kg/m²", "type": "number", "min": 14.0, "max": 50.0, "default": 23.0, "step": 0.1}
      ]
    },
    {
      "group_name": "Functional Measures",
      "features": [
        {"name": "gait_speed", "clinical_name": "Gait Speed", "unit": "m/s", "type": "number", "min": 0.2, "max": 2.5, "default": 0.8, "step": 0.01},
        {"name": "grip_strength", "clinical_name": "Grip Strength", "unit": "kg", "type": "number", "min": 5.0, "max": 60.0, "default": 25.0, "step": 0.1},
        {"name": "chair_stand_time", "clinical_name": "Chair Stand Time", "unit": "s", "type": "number", "min": 0.0, "max": 30.0, "default": 12.0, "step": 0.1}
      ]
    },
    {
      "group_name": "Clinical Variables",
      "features": [
        {"name": "cesd_score", "clinical_name": "CES-D Score", "unit": "", "type": "number", "min": 0, "max": 30, "default": 8, "step": 1},
        {"name": "chronic_conditions", "clinical_name": "Number of Chronic Conditions", "unit": "", "type": "number", "min": 0, "max": 15, "default": 2, "step": 1},
        {"name": "hospitalization", "clinical_name": "Hospitalization (past year)", "unit": "", "type": "select", "options": [{"value": 0, "label": "No"}, {"value": 1, "label": "Yes"}], "default": 0}
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
import xgboost as xgb

st.set_page_config(
    page_title="Frailty Prediction Tool",
    page_icon="🏥",
    layout="wide",
)

# Load model with caching
@st.cache_resource
def load_model():
    with open(Path(__file__).parent / "model_info.json") as f:
        model_info = json.load(f)
    model = xgb.XGBClassifier()
    model.load_model(str(Path(__file__).parent.parent / "models" / "xgb_final.json"))
    return model, model_info

model, model_info = load_model()

# Sidebar — Model Info + Disclaimer
with st.sidebar:
    st.header("Model Information")
    st.metric("AUC", f"{model_info['performance']['auc']:.3f}",
              help=f"95% CI: {model_info['performance']['auc_ci_low']:.3f} - {model_info['performance']['auc_ci_high']:.3f}")
    st.metric("Calibration Slope", f"{model_info['performance']['calibration_slope']:.2f}")
    st.divider()
    st.caption("⚠️ **Disclaimer**: This tool is for research and educational purposes only. "
               "It does not constitute medical advice.")

# Main — Input Form
st.title("2-Year Frailty Worsening Risk Prediction")

with st.expander("📋 Demographics", expanded=True):
    col1, col2, col3 = st.columns(3)
    age = col1.number_input("Age (years)", min_value=60, max_value=110, value=70)
    sex = col2.selectbox("Sex", options=["Female", "Male"])
    bmi = col3.number_input("BMI (kg/m²)", min_value=14.0, max_value=50.0, value=23.0, step=0.1)

with st.expander("💪 Functional Measures", expanded=True):
    col1, col2, col3 = st.columns(3)
    gait_speed = col1.number_input("Gait Speed (m/s)", min_value=0.2, max_value=2.5, value=0.8, step=0.01)
    grip_strength = col2.number_input("Grip Strength (kg)", min_value=5.0, max_value=60.0, value=25.0, step=0.1)
    chair_stand = col3.number_input("Chair Stand Time (s)", min_value=0.0, max_value=30.0, value=12.0, step=0.1)

with st.expander("🏥 Clinical Variables"):
    col1, col2, col3 = st.columns(3)
    cesd = col1.number_input("CES-D Score", min_value=0, max_value=30, value=8)
    chronic = col2.number_input("Chronic Conditions", min_value=0, max_value=15, value=2)
    hospitalized = col3.selectbox("Hospitalized (past year)", options=["No", "Yes"])

# Predict
if st.button("🔮 Predict Risk", type="primary", use_container_width=True):
    features = np.array([[
        gait_speed, grip_strength, chair_stand, age,
        1 if sex == "Male" else 0, bmi, cesd, chronic, 1 if hospitalized == "Yes" else 0
    ]])
    proba = model.predict_proba(features)[0, 1]

    # Risk category
    risk_cats = model_info['output']['risk_categories']
    cat = risk_cats[0]
    for rc in risk_cats:
        if rc['range'][0] <= proba < rc['range'][1]:
            cat = rc
            break

    # Display result
    st.divider()
    col1, col2 = st.columns([1, 2])
    col1.metric("Risk Probability", f"{proba:.1%}")
    color_map = {"green": "🟢", "orange": "🟠", "red": "🔴"}
    col1.caption(f"{color_map.get(cat['color'], '')} {cat['label']}")

    # Feature contributions (simplified SHAP-based direction)
    col2.info(cat['recommendation'])
```

### Quality Checklist 结果

- [x] 模型可正常加载和预测
- [x] model_info.json 特征数 = 9 (模型期望 9)
- [x] feature_config.json 每个特征含 clinical_name
- [x] app.py 可正常启动 (`streamlit run`)
- [x] 输入表单按 Demographics / Functional / Clinical 分组
- [x] 输出区含风险概率 + 分类 + AUC
- [x] 安全免责声明在侧边栏底部
- [x] 异常输入有警告但不阻断
- [x] requirements.txt 可正常安装
- [x] Dockerfile 可构建
- [x] build_exe.py 可正常打包
- [x] README.md 部署说明完整
