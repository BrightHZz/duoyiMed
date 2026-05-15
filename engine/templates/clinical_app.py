"""
Clinical Prediction Tool — Streamlit Web Application Template

This template is used by the clinical-tool-developer agent to generate
a deployable clinical prediction web tool from a trained ML model.

Template variables (replaced by agent during Phase 7 build_app step):
  {{PROJECT_TITLE}}        — Research project title
  {{MODEL_TYPE}}           — xgboost / logistic_regression
  {{RISK_OUTCOME}}         — What is being predicted (e.g. "2-Year Frailty Worsening")
  {{FEATURE_GROUPS}}       — Input form groups with clinical feature specs
  {{RISK_CATEGORIES}}      — Risk stratification thresholds
  {{AUC_VALUE}}            — Model AUC
  {{AUC_CI_LOW}}           — AUC 95% CI lower bound
  {{AUC_CI_HIGH}}          — AUC 95% CI upper bound
  {{CALIBRATION_SLOPE}}    — Calibration slope

Usage:
  streamlit run app.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="{{PROJECT_TITLE}} — Clinical Prediction Tool",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Model & Config ──────────────────────────────────────
@st.cache_resource
def load_model():
    """Load trained model and model info."""
    model_path = Path(__file__).parent / "model_info.json"
    with open(model_path) as f:
        model_info = json.load(f)

    # Load model from pickle
    model_file = Path(__file__).parent.parent / "models" / "xgb_final.pkl"
    if not model_file.exists():
        model_file = Path(__file__).parent.parent / "models" / "lr_final.pkl"
    model = joblib.load(str(model_file))
    return model, model_info

@st.cache_resource
def load_feature_config():
    """Load feature configuration for input form."""
    config_path = Path(__file__).parent / "feature_config.json"
    with open(config_path) as f:
        return json.load(f)

model, model_info = load_model()
feature_config = load_feature_config()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 {{PROJECT_TITLE}}")
    st.markdown("---")

    st.subheader("📊 Model Performance")
    auc = model_info["performance"]["auc"]
    auc_ci = model_info["performance"].get("auc_ci_low", 0), model_info["performance"].get("auc_ci_high", 0)
    st.metric("AUC (ROC)", f"{auc:.3f}")
    st.caption(f"95% CI: {auc_ci[0]:.3f}–{auc_ci[1]:.3f}")

    brier = model_info["performance"].get("brier")
    if brier:
        st.metric("Brier Score", f"{brier:.3f}")
    calib = model_info["performance"].get("calibration_slope")
    if calib:
        st.metric("Calibration Slope", f"{calib:.2f}")

    st.markdown("---")
    st.subheader("ℹ️ About")
    st.markdown(f"""
    This tool predicts **{{RISK_OUTCOME}}** based on
    {len(model_info['features'])} clinical and functional measures.

    **Model type:** {{MODEL_TYPE}}
    """)

    st.markdown("---")
    st.warning("""
    ⚠️ **Disclaimer**

    This tool is for **research and educational purposes only**.
    It does not constitute medical advice. Clinical decisions
    should not be based solely on this prediction. Always
    consider the full clinical picture and consult current
    guidelines.
    """)

# ── Main Content ─────────────────────────────────────────────
st.title("{{RISK_OUTCOME}} Risk Prediction")
st.markdown(f"*{{PROJECT_TITLE}}*")

# ── Input Form ───────────────────────────────────────────────
st.subheader("📋 Patient Information")

# Build input form from feature_config
input_values = {}

for group in feature_config.get("input_groups", []):
    with st.expander(f"**{group['group_name']}**", expanded=(group == feature_config["input_groups"][0])):
        cols = st.columns(3)
        for i, feature in enumerate(group.get("features", [])):
            col = cols[i % 3]
            name = feature["name"]
            clinical_name = feature.get("clinical_name", name)
            unit = feature.get("unit", "")
            label = f"{clinical_name} ({unit})" if unit else clinical_name

            ftype = feature.get("type", "number")
            if ftype == "number":
                input_values[name] = col.number_input(
                    label,
                    min_value=float(feature.get("min", 0)),
                    max_value=float(feature.get("max", 200)),
                    value=float(feature.get("default", 0)),
                    step=float(feature.get("step", 0.1)),
                    help=f"Normal range: {feature.get('normal_range', 'N/A')}",
                )
            elif ftype == "select":
                options = feature.get("options", [])
                input_values[name] = col.selectbox(
                    label,
                    options=options,
                    help=feature.get("help", ""),
                )
            elif ftype == "checkbox":
                input_values[name] = 1 if col.checkbox(label) else 0

            # Warning for out-of-range values
            if ftype == "number":
                val = input_values[name]
                normal_range = feature.get("normal_range")
                if normal_range and isinstance(normal_range, list) and len(normal_range) == 2:
                    if val < normal_range[0] or val > normal_range[1]:
                        col.warning(f"Outside typical range ({normal_range[0]}–{normal_range[1]})")

# ── Prediction ───────────────────────────────────────────────
st.markdown("---")
predict_col1, predict_col2, predict_col3 = st.columns([1, 1, 2])

with predict_col1:
    predict_btn = st.button("🔍 Calculate Risk", type="primary", use_container_width=True)
with predict_col2:
    reset_btn = st.button("🔄 Reset", use_container_width=True)

if reset_btn:
    st.rerun()

if predict_btn:
    with st.spinner("Calculating risk..."):
        # Prepare feature vector
        feature_names = [f["name"] for f in model_info["features"]]
        feature_vector = []
        for fname in feature_names:
            val = input_values.get(fname)
            if val is None:
                val = 0.0
            feature_vector.append(float(val))

        X = np.array(feature_vector).reshape(1, -1)

        # Predict
        try:
            proba = model.predict_proba(X)[0]
            risk = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception:
            risk = float(model.predict(X)[0])

        # Classify risk
        categories = model_info.get("output", {}).get("risk_categories", [
            {"label": "Low Risk", "range": [0, 0.15], "color": "green"},
            {"label": "Moderate Risk", "range": [0.15, 0.35], "color": "orange"},
            {"label": "High Risk", "range": [0.35, 1.0], "color": "red"},
        ])
        risk_label = "Unknown"
        risk_color = "grey"
        for cat in categories:
            if cat["range"][0] <= risk < cat["range"][1]:
                risk_label = cat["label"]
                risk_color = cat["color"]
                break

    # ── Display Results ───────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Prediction Results")

    res_col1, res_col2, res_col3 = st.columns([1, 1, 1])

    with res_col1:
        # Risk probability with color
        color_map = {"green": "#27ae60", "orange": "#e67e22", "red": "#e74c3c"}
        st.markdown(f"""
        <div style="text-align:center; padding:20px; border-radius:10px;
                    background:{color_map.get(risk_color, '#95a5a6')}20;
                    border:2px solid {color_map.get(risk_color, '#95a5a6')}">
            <p style="font-size:14px; color:gray; margin:0">Predicted Risk</p>
            <p style="font-size:48px; font-weight:bold; margin:0;
                      color:{color_map.get(risk_color, '#95a5a6')}">
                {risk * 100:.1f}%
            </p>
            <p style="font-size:16px; margin:0">{risk_label}</p>
        </div>
        """, unsafe_allow_html=True)

    with res_col2:
        st.markdown("**Risk Category**")
        for cat in categories:
            is_current = cat["label"] == risk_label
            prefix = "▶️ " if is_current else "• "
            st.markdown(f"{prefix}{cat['label']}: {cat['range'][0]*100:.0f}–{cat['range'][1]*100:.0f}%")

    with res_col3:
        st.markdown("**Top Contributing Factors**")
        # Show feature contributions if available (from model_info importances)
        features_with_importance = [
            (f["clinical_name"], f.get("importance", 0))
            for f in model_info["features"]
        ]
        features_with_importance.sort(key=lambda x: x[1], reverse=True)
        for clin_name, imp in features_with_importance[:5]:
            direction = "↑" if imp > 0 else "↓"
            st.markdown(f"{direction} **{clin_name}**")

    # ── Disclaimer (repeated at bottom for prominence) ────────
    st.markdown("---")
    st.warning(
        "⚠️ **Disclaimer**: This tool is for research and educational purposes only. "
        "It does not constitute medical advice. Clinical decisions should not be based "
        "solely on this prediction. Always consider the full clinical picture and "
        "consult current clinical guidelines."
    )

# ── Footer ───────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Powered by Computational Medicine Research Co. | "
    "Model trained with scikit-learn/XGBoost | "
    "External validation pending before clinical use"
)
