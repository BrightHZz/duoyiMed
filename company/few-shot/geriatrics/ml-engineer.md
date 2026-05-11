# Few-Shot 示例 — ML Engineer Agent

## Example 1: 特征工程 + 训练脚本

### Input

```
任务: 基于建模方案, 实现 CHARLS 衰弱转换预测的特征工程 + XGBoost 训练

建模方案要点:
  - 数据: CHARLS 2013 (基线) → 2015 (结局)
  - 结局: Fried Phenotype 恶化 (≥1分增加) = 1
  - 特征: 78 个候选, 6 个类别
  - 需要处理: 缺失值 (MICE), 类别不平衡, 记忆/学习效应

数据文件路径:
  {CHARLS_DATA_DIR}/analysis/
  需要合并: 2013_Health_Status_and_Functioning.csv, 
            2013_Biomarker.csv, 2013_Demographic_Background.csv 等

请写出特征工程的 Python 代码 + XGBoost 训练 + SHAP 可解释性。
```

### Reasoning (Chain of Thought)

```
1. 读取数据:
   - 多个 CSV, 以 subject_id 合并
   - 需要加载权重文件 (2013_Weights.csv) 用于描述性统计
   - ⚠️ 2013 数据中 subject_id 可能叫 'ID' 或 'householdID'+'personID', 
     需先 inspect

2. 特征工程考虑:
   - 时间窗口: 这是单次基线 → 不需要时间窗口特征工程
   - 但需注意: CES-D 的 10 个问题是否独立作为特征还是会聚合
   - 握力: 取优势手 2 次测量的最大值
   - 步速: 2.5m 计时 → 转换为 m/s
   - BMI: weight / height²
   - 多重用药: 统计自报用药种类数

3. 缺失值策略:
   - 在 nested CV 内部做 MICE (避免信息泄露)
   - 但 MICE 在 CV 循环内太慢 → 可先用简单插补 (中位数/众数) 
     做快速实验, 最终版本用 MICE

4. 类别不平衡:
   - 预估恶化率 ~25% → 1:3 不平衡
   - 使用 scale_pos_weight 而非 SMOTE (因为样本量够, SMOTE 可能引入噪声)

5. Nested CV 实现:
   - sklearn 的 cross_val_score 是 single CV!
   → 需手动实现 nested CV 或使用 mlxtend 等库
```

### Output

```python
"""
CHARLS 衰弱转换预测 — 特征工程 + XGBoost 训练
================================================
项目: frailty_ml_2026
数据基线: CHARLS 2013 Wave
结局评估: CHARLS 2015 Wave

注意事项:
  - 2013 是首次包含握力+步速的 wave
  - 特征选择必须在 CV 内部进行
  - 使用 scale_pos_weight 处理类别不平衡
"""

# ============================================
# 内存安全配置 — 必须放在所有 import 之前
# ============================================
import os
os.environ["JOBLIB_START_METHOD"] = "forkserver"
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import xgboost as xgb
import shap
import mlflow
import warnings
warnings.filterwarnings('ignore')

N_JOBS = 2       # 全局并行上限, M4 24GB 绝对不超过此值
RANDOM_SEED = 42

# ============================================================
# 1. 数据加载与合并
# ============================================================

DATA_DIR = "{CHARLS_DATA_DIR}/analysis/"

def load_wave_data(wave, files):
    """加载某个 wave 的多个 CSV 并合并"""
    dfs = []
    for f in files:
        path = f"{DATA_DIR}{wave}_{f}.csv"
        df = pd.read_csv(path)
        # 统一 ID 列名
        id_col = [c for c in df.columns if c.lower() in ('id', 'subject_id', 'householdid')][0]
        if id_col != 'ID':
            df.rename(columns={id_col: 'ID'}, inplace=True)
        dfs.append(df)
    
    # 按 ID 合并
    merged = dfs[0]
    for df in dfs[1:]:
        # 避免重复列 (如多个文件都有 sex/age)
        overlap = [c for c in df.columns if c in merged.columns and c != 'ID']
        merged = merged.merge(df.drop(columns=overlap, errors='ignore'), on='ID', how='inner')
    return merged

# 加载 2013 基线数据
wave2013_files = [
    'Demographic_Background',
    'Health_Status_and_Functioning',
    'Biomarker',
    'Health_Care_and_Insurance',
    'Individual_Income',
]
df_2013 = load_wave_data(2013, wave2013_files)

# 加载 2015 结局数据 (仅需衰弱状态)
df_2015_outcome = pd.read_csv(f"{DATA_DIR}2015_Health_Status_and_Functioning.csv")
# ... 提取 Fried 相关变量


# ============================================================
# 2. 特征工程
# ============================================================

def build_frailty_features(df):
    """从 CHARLS 原始变量构建衰弱预测特征"""
    features = pd.DataFrame()
    features['ID'] = df['ID']
    
    # --- 人口学 ---
    features['age'] = df['age']  # 需确认实际变量名
    features['sex'] = df['sex']  # 1=male, 2=female → 0/1
    features['education_years'] = df['education']
    features['married'] = (df['marital_status'] == 1).astype(int)
    features['urban'] = (df['residence'] == 1).astype(int)
    features['living_alone'] = (df['household_size'] == 1).astype(int)
    
    # --- 功能 ---
    # 握力: 取优势手 2 次测量的最大值
    grip_cols = ['grip_test1', 'grip_test2']  # 需确认实际变量名
    features['grip_max_kg'] = df[grip_cols].max(axis=1)
    
    # 步速: 2.5m / 时间(秒)
    features['gait_speed_ms'] = 2.5 / df['walk_time_sec'].clip(lower=1)
    
    # ADL 依赖项数
    adl_cols = ['adl_dress', 'adl_bathe', 'adl_eat', 'adl_transfer', 'adl_toilet', 'adl_urine']
    features['adl_dependency_count'] = df[adl_cols].sum(axis=1)
    
    # --- BMI ---
    features['bmi'] = df['weight_kg'] / (df['height_m'] ** 2)
    
    # --- 多重用药 ---
    med_cols = [c for c in df.columns if c.startswith('med_')]
    features['polypharmacy'] = (df[med_cols].notna().sum(axis=1) >= 5).astype(int)
    
    # --- 认知 ---
    features['mmse_total'] = df['mmse_score']  # CHARLS 简化 MMSE
    
    # --- 抑郁 ---
    cesd_cols = [c for c in df.columns if c.startswith('cesd_')]
    features['cesd_total'] = df[cesd_cols].sum(axis=1)
    
    # --- 慢性病 ---
    chronic_cols = ['hypertension', 'diabetes', 'heart_disease', 'stroke',
                    'copd', 'arthritis', 'kidney_disease', 'cancer']
    features['chronic_disease_count'] = df[chronic_cols].sum(axis=1)
    
    # ... 更多特征 (共 ~78 个)
    
    return features

# 构建特征矩阵
X = build_frailty_features(df_2013).set_index('ID')
# y: 从 df_2015_outcome 计算 Fried 恶化 (此处简化为伪代码)
y = compute_frailty_worsening(df_2013, df_2015_outcome)

print(f"样本量: {len(X)}, 事件率: {y.mean():.2%}")

# ============================================================
# 3. Nested CV 训练
# ============================================================

# 外环: 10-fold
outer_cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
# 内环: 5-fold
inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

outer_scores = {'auc_roc': [], 'auc_pr': [], 'brier': []}

for fold, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    # --- Pipeline (特征选择在 CV 内) ---
    # ⚠️ 当前简化版; 完整版需在 CV 内做 MICE + LASSO 特征选择
    pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('clf', xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
            random_state=RANDOM_SEED,
            n_jobs=N_JOBS,
            eval_metric='logloss'
        ))
    ])
    
    pipe.fit(X_train, y_train)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    
    outer_scores['auc_roc'].append(roc_auc_score(y_test, y_prob))
    outer_scores['auc_pr'].append(average_precision_score(y_test, y_prob))
    outer_scores['brier'].append(brier_score_loss(y_test, y_prob))

print("=== 10-fold Nested CV Results ===")
for metric, values in outer_scores.items():
    print(f"{metric}: {np.mean(values):.3f} (±{np.std(values):.3f})")

# ============================================================
# 4. 完整训练 + SHAP (用于可解释性, 在全部数据上)
# ============================================================

final_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=5, learning_rate=0.05,
    subsample=0.8, scale_pos_weight=(y == 0).sum() / (y == 1).sum(),
    random_state=RANDOM_SEED, n_jobs=N_JOBS
)
final_model.fit(X, y)

# SHAP
explainer = shap.TreeExplainer(final_model)
shap_values = explainer.shap_values(X)

# --- 全局重要性 ---
shap.summary_plot(shap_values, X, show=False)
# plt.savefig('outputs/figures/shap_summary.png')

# --- Top 特征 ---
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'shap_mean': np.abs(shap_values).mean(axis=0)
}).sort_values('shap_mean', ascending=False)
print("\nTop 20 SHAP Features:")
print(feature_importance.head(20).to_string(index=False))

print("\n训练完成。")
print("下一步: 时间验证 (2015→2018), 敏感性分析, 校准评估")
```

### 关键实现提醒

1. **内存安全配置必须在 import 之前** — JOBLIB_START_METHOD=forkserver + OMP/MKL/BLAS 线程=2 + N_JOBS=2，违反可能导致系统重启
2. **Nested CV 必须手动实现** — `cross_val_score` 只有单层 CV
3. **特征选择在 CV 内** — 不要在 CV 外做 `SelectKBest` 再传入
4. **test set 只用一次** — 超参调优在 inner CV 完成
5. **scale_pos_weight** — 比 SMOTE 更适合此场景；如需 SMOTE，必须在主进程做且 n_jobs=1
6. **所有实验走 MLflow** — 记录参数、指标、artifact

---

## Example 2: LSTM 时间序列预测 — CHARLS 多波次衰弱轨迹 (DL + M4 优化)

### Input

```
任务: 使用 LSTM 预测 CHARLS 2018/2020 波次的 Fried 衰弱评分

数据:
  - 已完成时间序列数据集构建 (charls_timeseries_dataset.py)
  - 输入: 前3波次 (2011/2013/2015) 的 30 维特征
  - 输出: 后2波次 (2018/2020) 的 4 维目标 (f_score_3item, wl, exh, inactive)
  - 训练集 26228 人, 验证集 5618 人
  
硬件: MacBook Pro M4 (Apple Silicon), MPS 后端
要求: MPS 优化, 混合精度, 内存友好
```

### Output

```python
"""
CHARLS 衰弱轨迹预测 — LSTM + M4 优化
=====================================
任务: 多波次时序 → 多波次衰弱轨迹预测
模型: 2层双向 LSTM + Linear 投影
硬件: MacBook Pro M4 (MPS)
"""

# ============================================
# 内存安全配置 — 必须在 import 之前
# ============================================
import os
os.environ["JOBLIB_START_METHOD"] = "forkserver"
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.amp import autocast
import numpy as np
from tqdm import tqdm

# ============================================================
# 0. M4 设备检测
# ============================================================

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"使用设备: {device}")

# MPS 混合精度
USE_AMP = (device.type == "mps")
AMP_DTYPE = torch.float16  # MPS 支持 float16

# ============================================================
# 1. LSTM 时序预测模型
# ============================================================

class LSTMFrailtyPredictor(nn.Module):
    """
    双向 LSTM 编码器 + 线性投影解码器
    
    Args:
        input_dim: 输入特征维度
        hidden_dim: LSTM 隐藏层维度
        output_dim: 输出目标维度
        n_layers: LSTM 层数
        pred_len: 预测的波次数
        dropout: Dropout 率
    """
    def __init__(self, input_dim=30, hidden_dim=256, output_dim=4,
                 n_layers=2, pred_len=2, dropout=0.2):
        super().__init__()
        self.pred_len = pred_len
        self.output_dim = output_dim
        
        # 输入投影
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # 双向 LSTM
        self.lstm = nn.LSTM(
            hidden_dim, hidden_dim,
            num_layers=n_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if n_layers > 1 else 0
        )
        
        # 注意力池化 (代替直接取最后一步)
        self.attn = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
        
        # 解码器: 将编码表示投影到多步预测
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, pred_len * output_dim)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        for name, p in self.named_parameters():
            if 'weight' in name and p.dim() >= 2:
                nn.init.xavier_uniform_(p)
            elif 'bias' in name:
                nn.init.zeros_(p)
    
    def forward(self, x):
        """
        Args:
            x: [batch, seq_len, input_dim] 编码器输入序列
        Returns:
            pred: [batch, pred_len, output_dim] 预测序列
        """
        batch_size = x.size(0)
        
        # 输入投影
        x = self.input_proj(x)  # [B, L, H]
        
        # LSTM 编码
        lstm_out, _ = self.lstm(x)  # [B, L, 2H]
        
        # 注意力池化
        attn_weights = self.attn(lstm_out).squeeze(-1)  # [B, L]
        attn_weights = torch.softmax(attn_weights, dim=-1)  # [B, L]
        context = torch.bmm(attn_weights.unsqueeze(1), lstm_out).squeeze(1)  # [B, 2H]
        
        # 解码
        pred = self.decoder(context)  # [B, pred_len * output_dim]
        pred = pred.view(batch_size, self.pred_len, self.output_dim)
        
        return pred


# ============================================================
# 2. 训练循环 (M4 优化版)
# ============================================================

def train_epoch(model, loader, optimizer, scaler, device):
    """单轮训练 — MPS 混合精度 + 梯度裁剪"""
    model.train()
    total_loss = 0.0
    n_batches = 0
    
    for batch in tqdm(loader, desc="训练", leave=False):
        # 数据移到设备 (统一内存架构, 不需要 pin_memory)
        seq_x = batch[0].to(device)       # [B, seq_len, n_feat]
        seq_y = batch[1].to(device)       # [B, label_len+pred_len, n_target]
        
        optimizer.zero_grad()
        
        # MPS 混合精度前向
        if scaler is not None:
            with autocast(device_type="mps", dtype=AMP_DTYPE):
                pred = model(seq_x)
                # 只计算预测部分的损失 (label_len 之后)
                target = seq_y[:, -pred.size(1):, :]
                # 掩码 MSE: 只计算非零目标位置的损失
                mask = (target != 0).float()
                loss = ((pred - target) ** 2 * mask).sum() / (mask.sum() + 1e-8)
            
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            pred = model(seq_x)
            target = seq_y[:, -pred.size(1):, :]
            mask = (target != 0).float()
            loss = ((pred - target) ** 2 * mask).sum() / (mask.sum() + 1e-8)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
        
        total_loss += loss.item()
        n_batches += 1
    
    return total_loss / n_batches


@torch.inference_mode()
def evaluate(model, loader, device):
    """验证 — 计算 MSE 和 MAE"""
    model.eval()
    total_mse, total_mae = 0.0, 0.0
    n = 0
    
    for batch in loader:
        seq_x = batch[0].to(device)
        seq_y = batch[1].to(device)
        
        pred = model(seq_x)
        target = seq_y[:, -pred.size(1):, :]
        mask = (target != 0).float()
        
        mse = ((pred - target) ** 2 * mask).sum() / (mask.sum() + 1e-8)
        mae = (torch.abs(pred - target) * mask).sum() / (mask.sum() + 1e-8)
        
        total_mse += mse.item()
        total_mae += mae.item()
        n += 1
    
    return total_mse / n, total_mae / n


# ============================================================
# 3. 主训练流程
# ============================================================

def main():
    from src.data.charls_timeseries_dataset import CHARLSTimeSeriesBuilder, CHARLSSequenceDataset
    
    DATA_DIR = "{CHARLS_DATA_DIR}/analysis"
    
    # 数据
    builder = CHARLSTimeSeriesBuilder(DATA_DIR, seq_len=3, label_len=1, pred_len=2)
    wave_dfs = builder.build_all_waves()
    sequences = builder.build_sequences(wave_dfs)
    
    train_ds = CHARLSSequenceDataset(sequences, 3, 1, 2, mode='train')
    val_ds = CHARLSSequenceDataset(sequences, 3, 1, 2, mode='val')
    
    # M4: num_workers=0 (统一内存架构, 多进程反而慢)
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0)
    
    # 模型 (参数量 ~3.5M, M4 友好)
    model = LSTMFrailtyPredictor(
        input_dim=30, hidden_dim=256, output_dim=4,
        n_layers=2, pred_len=2, dropout=0.2
    ).to(device)
    
    print(f"模型参数量: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")
    
    # 优化器
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )
    scaler = torch.amp.GradScaler(device_type="mps") if USE_AMP else None
    
    # 训练
    best_val_loss = float('inf')
    patience_counter = 0
    MAX_EPOCHS = 100
    EARLY_STOP_PATIENCE = 15
    
    for epoch in range(MAX_EPOCHS):
        train_loss = train_epoch(model, train_loader, optimizer, scaler, device)
        val_mse, val_mae = evaluate(model, val_loader, device)
        
        scheduler.step(val_mse)
        
        print(f"Epoch {epoch+1:3d} | Train Loss: {train_loss:.4f} | "
              f"Val MSE: {val_mse:.4f} | Val MAE: {val_mae:.4f}")
        
        # Early stopping + 保存最佳模型
        if val_mse < best_val_loss:
            best_val_loss = val_mse
            patience_counter = 0
            # 始终保存到 CPU (跨平台兼容)
            torch.save(model.state_dict(), "outputs/models/lstm_frailty_best.pth")
            print(f"  ✓ 保存最佳模型 (Val MSE={best_val_loss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOP_PATIENCE:
                print(f"Early stopping at epoch {epoch+1}")
                break
    
    print(f"\n训练完成. 最佳 Val MSE: {best_val_loss:.4f}")


if __name__ == '__main__':
    main()
```

### 关键提醒 (DL + M4)

1. **内存安全配置**: 脚本顶部必须设置 JOBLIB_START_METHOD=forkserver + OMP/MKL/BLAS 线程=2，防止底层多线程爆炸
2. **设备检测**: 永远先用 `torch.backends.mps.is_available()` 检测, 回退到 CPU
3. **混合精度**: MPS 支持 float16 autocast, `torch.amp.GradScaler("mps")` 防止梯度 underflow
4. **num_workers=0**: 统一内存架构上多进程 DataLoader 效率不高，且每个 worker 会复制数据 → OOM
5. **内存**: M4 上 batch_size 从 32 开始, OOM 就减半 + 梯度累积；跑之前看活动监视器确认可用 RAM
6. **模型保存**: 始终 `torch.save(state_dict, path)` 不带 device, 加载时 `map_location="cpu"`
7. **baseline 对比**: DL 训练完成后, 必须跑经典 ML baseline (XGBoost/LR) 并报告性能差异，baseline 的 n_jobs=2
