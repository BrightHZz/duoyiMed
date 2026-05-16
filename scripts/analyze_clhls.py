import pyreadstat
import pandas as pd
import numpy as np
import json, os

base = "D:/database/datasets/clhls"
cross_path = os.path.join(base, "CLHLS_2018_cross_sectional_dataset_15874/clhls_2018_cross_sectional_dataset_15874.sav")

print("Loading metadata...")
_, meta = pyreadstat.read_sav(cross_path, metadataonly=True)

str_cols = [c for c, t in meta.readstat_variable_types.items() if t == 'string']
num_cols = [c for c in meta.column_names if c not in str_cols]
print(f"Numeric: {len(num_cols)}, String(skip): {len(str_cols)}")

print("Loading data...")
df, meta = pyreadstat.read_sav(cross_path, usecols=num_cols)
n = len(df)
print(f"Loaded: {n} rows x {len(df.columns)} cols")

R = {}  # Results dict

# ============ 1. OVERVIEW ============
print("\n" + "=" * 60)
print("1. DATASET OVERVIEW")
print("=" * 60)
R['dataset'] = 'CLHLS 2018 Cross-sectional'
R['total_rows'] = n
R['total_columns'] = len(df.columns)
R['numeric_columns'] = len(num_cols)
R['string_columns'] = len(str_cols)
print(f"Total: {n:,} elderly individuals, {len(df.columns)} variables")

# ============ 2. DEMOGRAPHICS ============
print("\n" + "=" * 60)
print("2. DEMOGRAPHICS")
print("=" * 60)

# Sex: 1=Male, 2=Female
sex_dist = df['a1'].value_counts().reindex([1.0, 2.0])
sex_labels = {1.0: 'Male', 2.0: 'Female'}
print(f"Sex:           Male={int(sex_dist[1.0])} ({sex_dist[1.0]/n*100:.1f}%), Female={int(sex_dist[2.0])} ({sex_dist[2.0]/n*100:.1f}%)")
R['sex'] = {'Male': int(sex_dist.get(1.0,0)), 'Female': int(sex_dist.get(2.0,0)),
            'Male_pct': round(float(sex_dist.get(1.0,0)/n*100),1)}

# Age
age = df['trueage'].dropna()
age = age[(age >= 50) & (age <= 120)]  # valid range
bins = [0, 65, 75, 85, 95, 200]
labels = ['<65', '65-74', '75-84', '85-94', '95+']
age_grp = pd.cut(age, bins=bins, labels=labels).value_counts().sort_index()
R['age'] = {
    'N': int(len(age)), 'mean': round(float(age.mean()),1),
    'median': float(age.median()), 'std': round(float(age.std()),1),
    'min': float(age.min()), 'max': float(age.max()),
    'by_group': {k: int(v) for k,v in age_grp.items()}
}
print(f"Age:           mean={age.mean():.1f}, median={age.median():.0f}, range={age.min():.0f}-{age.max():.0f}")
print(f"Age groups:    {dict(age_grp)}")

# Residence: 1=City, 2=Town, 3=Rural
res_dist = df['residenc'].value_counts().reindex([1.0,2.0,3.0])
res_labels = {1.0:'City', 2.0:'Town', 3.0:'Rural'}
R['residence'] = {res_labels[k]: int(v) for k,v in res_dist.items()}
print(f"Residence:     {dict(zip(res_labels.values(), [int(v) for v in res_dist.to_list()]))}")

# Ethnicity: 1=Han
eth_han = (df['a2'] == 1).sum()
eth_other = (df['a2'] != 1).sum()
R['ethnicity'] = {'Han': int(eth_han), 'Other': int(eth_other), 'Han_pct': round(float(eth_han/n*100),1)}
print(f"Ethnicity:     Han={eth_han} ({eth_han/n*100:.1f}%), Other={eth_other}")

# Marital: 1=Married, 2=Separated, 3=Divorced, 4=Widowed, 5=Never
mar_labels = {1.0:'Married', 2.0:'Separated', 3.0:'Divorced', 4.0:'Widowed', 5.0:'Never Married'}
mar_dist = df['f41'].value_counts()
R['marital'] = {mar_labels.get(k, f'code_{k}'): int(v) for k,v in mar_dist.items()}
mar_married = mar_dist.get(1.0, 0)
print(f"Marital:       Married={mar_married} ({mar_married/n*100:.1f}%)")

# Education
edu = df['f1'].dropna()
edu = edu[(edu >= 0) & (edu <= 30)]
illit = (edu == 0).mean() * 100
R['education'] = {
    'mean_years': round(float(edu.mean()),1), 'median_years': float(edu.median()),
    'illiteracy_pct': round(float(illit),1),
    'N': int(len(edu))
}
print(f"Education:     mean={edu.mean():.1f}y, illiteracy={illit:.1f}%")

# Living arrangement (co-residence a51)
# 1=with household, 2=alone, 3=institution
if 'a51' in df.columns:
    co_res = df['a51'].value_counts()
    co_labels = {1.0:'With household', 2.0:'Alone', 3.0:'Institution'}
    living = {co_labels.get(k, f'code_{k}'): int(v) for k,v in co_res.items()}
    R['living_arrangement'] = living
    with_hh = co_res.get(1.0, 0)
    print(f"Living:        With household={with_hh} ({with_hh/n*100:.1f}%)")

# ============ 3. CHRONIC DISEASES ============
print("\n" + "=" * 60)
print("3. CHRONIC DISEASE PREVALENCE")
print("=" * 60)

disease_map = {
    'g15a1': 'Hypertension', 'g15b1': 'Diabetes', 'g15c1': 'Heart Disease',
    'g15d1': 'Stroke/CVD', 'g15e1': 'Respiratory', 'g15g1': 'Cataract',
    'g15h1': 'Glaucoma', 'g15i1': 'Cancer', 'g15k1': 'Gastric Ulcer',
    'g15l1': 'Parkinson', 'g15n1': 'Arthritis', 'g15o1': 'Dementia',
    'g15r1': 'Dyslipidemia', 'g15s1': 'Rheumatism', 'g15t1': 'Chronic Nephritis'
}
R['disease_prevalence'] = {}
for code, name in disease_map.items():
    if code in df.columns:
        s = df[code].dropna()
        s = s[s.isin([1.0, 2.0])]  # exclude 8/9=missing codes
        rate = (s == 1.0).sum() / len(s) * 100 if len(s) > 0 else 0
        R['disease_prevalence'][name] = {'rate_pct': round(float(rate),1), 'N': int(len(s))}
        print(f"  {name:20s}: {rate:5.1f}% (N={len(s):,})")

# Multimorbidity
print("\nMultimorbidity:")
dis_cols = list(disease_map.keys())
dis_binary = pd.DataFrame(index=df.index)
for c in dis_cols:
    if c in df.columns:
        dis_binary[c] = (df[c] == 1.0).astype(int)
dis_binary = dis_binary.fillna(0)
dis_count = dis_binary.sum(axis=1)
mm_dist = dis_count.value_counts().sort_index()
R['multimorbidity'] = {
    'mean_count': round(float(dis_count.mean()), 2),
    'none_pct': round(float((dis_count == 0).mean() * 100), 1),
    'ge2_pct': round(float((dis_count >= 2).mean() * 100), 1),
    'ge3_pct': round(float((dis_count >= 3).mean() * 100), 1),
    'distribution': {str(int(k)): int(v) for k,v in mm_dist.items()}
}
print(f"  Mean diseases: {dis_count.mean():.2f}")
print(f"  No disease: {(dis_count==0).mean()*100:.1f}%")
print(f"  >=2 diseases (multimorbidity): {(dis_count>=2).mean()*100:.1f}%")
print(f"  >=3 diseases: {(dis_count>=3).mean()*100:.1f}%")

# ============ 4. ADL & IADL ============
print("\n" + "=" * 60)
print("4. FUNCTIONAL STATUS")
print("=" * 60)

adl_items = {'e1':'Bathing','e2':'Dressing','e3':'Toileting','e4':'Transferring','e5':'Continence','e6':'Feeding'}
R['adl'] = {}
adl_scores = pd.Series(0.0, index=df.index)
for code, name in adl_items.items():
    if code in df.columns:
        s = df[code].dropna()
        s = s[s.isin([1.0, 2.0, 3.0])]
        indep = (s == 1.0).mean() * 100
        R['adl'][name] = {'independent_pct': round(float(indep), 1), 'N': int(len(s))}
        score = s.map({1.0:0, 2.0:1, 3.0:1}).fillna(0)
        adl_scores += score
        print(f"  {name:15s}: {indep:5.1f}% independent")

adl_any = (adl_scores >= 1).sum()
adl_dist = adl_scores.value_counts().sort_index()
R['adl']['any_disability_pct'] = round(float(adl_any/n*100), 1)
R['adl']['deficit_distribution'] = {str(int(k)): int(v) for k,v in adl_dist.items()}
print(f"  Any ADL disability: {adl_any/n*100:.1f}%")
print(f"  ADL deficit distribution: {dict(adl_dist)}")

print("\nIADL:")
iadl_map = {'e7':'Visit neighbors','e8':'Shopping','e9':'Cook','e10':'Wash clothes',
            'e11':'Walk 1km','e12':'Carry 5kg','e13':'Crouch 3x','e14':'Public transit'}
R['iadl'] = {}
for code, name in iadl_map.items():
    if code in df.columns:
        s = df[code].dropna()
        s = s[s.isin([1.0, 2.0, 3.0])]
        can_do = (s == 1.0).mean() * 100
        R['iadl'][name] = round(float(can_do), 1)
        print(f"  {name:20s}: {can_do:.1f}% can do")

# ============ 5. LIFESTYLE ============
print("\n" + "=" * 60)
print("5. LIFESTYLE FACTORS")
print("=" * 60)

# Smoking: 1=Yes, 2=No
smoke_yes = (df['d71'] == 1.0).sum()
smoke_no = (df['d71'] == 2.0).sum()
R['smoking_pct'] = round(float(smoke_yes/(smoke_yes+smoke_no)*100), 1)
print(f"  Current smoker: {smoke_yes}/{smoke_yes+smoke_no} ({R['smoking_pct']}%)")

# Drinking: 1=Yes, 2=No
drink_yes = (df['d81'] == 1.0).sum()
drink_no = (df['d81'] == 2.0).sum()
R['drinking_pct'] = round(float(drink_yes/(drink_yes+drink_no)*100), 1)
print(f"  Current drinker: {drink_yes}/{drink_yes+drink_no} ({R['drinking_pct']}%)")

# Exercise: 1=Yes, 2=No
ex_yes = (df['d91'] == 1.0).sum()
ex_no = (df['d91'] == 2.0).sum()
R['exercise_pct'] = round(float(ex_yes/(ex_yes+ex_no)*100), 1)
print(f"  Current exercise: {ex_yes}/{ex_yes+ex_no} ({R['exercise_pct']}%)")

# ============ 6. SELF-RATED HEALTH & MENTAL ============
print("\n" + "=" * 60)
print("6. SELF-RATED HEALTH & MENTAL")
print("=" * 60)

# b12: 1=Very Good, 2=Good, 3=Fair, 4=Bad, 5=Very Bad
health_s = df['b12'].dropna()
health_s = health_s[health_s.isin([1.0,2.0,3.0,4.0,5.0])]
health_good = ((health_s <= 2.0).sum()) / len(health_s) * 100
health_bad = ((health_s >= 4.0).sum()) / len(health_s) * 100
R['self_rated_health'] = {
    'good_or_better_pct': round(float(health_good), 1),
    'bad_or_worse_pct': round(float(health_bad), 1),
    'N': int(len(health_s))
}
print(f"  Self-rated health >= Good: {health_good:.1f}%")
print(f"  Self-rated health Bad/Very Bad: {health_bad:.1f}%")

# Quality of Life (b11)
qol_s = df['b11'].dropna()
qol_s = qol_s[qol_s.isin([1.0,2.0,3.0,4.0,5.0])]
qol_good = ((qol_s <= 2.0).sum()) / len(qol_s) * 100
R['self_rated_qol'] = {
    'good_or_better_pct': round(float(qol_good), 1),
    'N': int(len(qol_s))
}
print(f"  QoL >= Good: {qol_good:.1f}%")

# Mental: 1=Always ... 5=Never, recode 1-3="often/sometimes"
for code, label in [('b33','Sad/Depressed'), ('b38','Lonely'), ('b39','Hopeless')]:
    s = df[code].dropna()
    s = s[s.isin([1.0,2.0,3.0,4.0,5.0])]
    yes = (s.isin([1.0, 2.0, 3.0])).sum()
    pct = yes / len(s) * 100
    R[f'mental_{code}'] = {'label': label, 'often_sometimes_pct': round(float(pct), 1), 'N': int(len(s))}
    print(f"  {label}: sometimes/often/always = {yes}/{len(s)} ({pct:.1f}%)")

# ============ 7. ANTHROPOMETRICS ============
print("\n" + "=" * 60)
print("7. ANTHROPOMETRICS & BLOOD PRESSURE")
print("=" * 60)

# Weight in kg (CLHLS codebook says kg), filter 999=missing
w_raw = df['g101'].copy()
h_raw = df['g1021'].copy()
# Filter: exclude 999 (missing code), keep 20-150 kg, 100-200 cm
w_clean = w_raw[(w_raw < 900) & (w_raw >= 20) & (w_raw <= 150)]
h_clean = h_raw[(h_raw < 900) & (h_raw >= 100) & (h_raw <= 200)]
common_idx = w_clean.index.intersection(h_clean.index)
weight_kg = w_clean.loc[common_idx]
height_cm = h_clean.loc[common_idx]
bmi = weight_kg / ((height_cm / 100) ** 2)
bmi_clean = bmi[(bmi >= 10) & (bmi <= 50)]
bmi_cat = pd.cut(bmi_clean, bins=[0,18.5,24,28,100], labels=['Underweight','Normal','Overweight','Obese'])
bmi_dist = bmi_cat.value_counts().sort_index()
print(f"  Weight: mean={weight_kg.mean():.1f}kg, median={weight_kg.median():.0f}kg")
print(f"  Height: mean={height_cm.mean():.1f}cm, median={height_cm.median():.0f}cm")
print(f"  BMI: mean={bmi_clean.mean():.2f}, median={bmi_clean.median():.2f}, N={len(bmi_clean)}")
print(f"  BMI categories: {dict(bmi_dist)}")
R['anthropometrics'] = {
    'weight_mean_kg': round(float(weight_kg.mean()), 1),
    'weight_median_kg': round(float(weight_kg.median()), 1),
    'weight_unit': 'kg',
    'height_mean_cm': round(float(height_cm.mean()), 1),
    'height_median_cm': round(float(height_cm.median()), 1),
    'bmi_mean': round(float(bmi_clean.mean()), 2),
    'bmi_median': round(float(bmi_clean.median()), 2),
    'bmi_N': int(len(bmi_clean)),
    'bmi_categories': {str(k): int(v) for k,v in bmi_dist.items()},
    'bmi_underweight_pct': round(float(bmi_dist.get('Underweight',0)/len(bmi_clean)*100), 1),
    'bmi_obese_pct': round(float(bmi_dist.get('Obese',0)/len(bmi_clean)*100), 1)
}

# Blood pressure
sbp_avg = df[['g511','g521']].mean(axis=1)
sbp_avg = sbp_avg[(sbp_avg < 900) & (sbp_avg >= 70) & (sbp_avg <= 250)]
sbp_htn = (sbp_avg >= 140).mean() * 100
sbp_high_norm = ((sbp_avg >= 130) & (sbp_avg < 140)).mean() * 100
print(f"  Systolic BP: mean={sbp_avg.mean():.1f}mmHg, >=140: {sbp_htn:.1f}%")
R['blood_pressure'] = {
    'systolic_mean_mmHg': round(float(sbp_avg.mean()), 1),
    'sbp_ge140_pct': round(float(sbp_htn), 1),
    'sbp_130_139_pct': round(float(sbp_high_norm), 1),
    'N': int(len(sbp_avg.dropna()))
}

# ============ 8. FALL HISTORY ============
print("\n" + "=" * 60)
print("8. FALL HISTORY")
print("=" * 60)

if 'g4c1' in df.columns:
    fall_yes = (df['g4c1'] == 1.0).sum()
    fall_no = (df['g4c1'] == 2.0).sum()
    R['fall'] = {
        'past_year_pct': round(float(fall_yes/(fall_yes+fall_no)*100), 1),
        'N': int(fall_yes+fall_no)
    }
    print(f"  Fall in past year: {fall_yes}/{fall_yes+fall_no} ({R['fall']['past_year_pct']}%)")

# ============ 9. MISSING DATA ============
print("\n" + "=" * 60)
print("9. MISSING DATA SUMMARY")
print("=" * 60)

missing = (df.isnull().sum() / n * 100).sort_values(ascending=False)
R['missing_data'] = {
    'complete_vars': int((missing == 0).sum()),
    'le_5pct_missing': int((missing <= 5).sum()),
    'le_10pct_missing': int((missing <= 10).sum()),
    'gt_50pct_missing': int((missing > 50).sum()),
}
print(f"  Complete (0%): {R['missing_data']['complete_vars']} vars")
print(f"  <=5% missing: {R['missing_data']['le_5pct_missing']} vars")
print(f"  <=10% missing: {R['missing_data']['le_10pct_missing']} vars")
print(f"  >50% missing: {R['missing_data']['gt_50pct_missing']} vars")

# ============ SAVE ============
out_dir = "D:/agentProjects/duoyi/obsidian/datasets"
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "clhls_2018_analysis.json"), "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=2)
print(f"\nJSON saved to {out_dir}/clhls_2018_analysis.json")

# ============ ALSO OUTPUT KEY STATS FOR MD DOC ============
print("\n\n========== SUMMARY STATS FOR KNOWLEDGE BASE ==========")
print(f"Sample size: {n:,}")
print(f"Age: {age.mean():.1f} ± {age.std():.1f} (range {age.min():.0f}-{age.max():.0f})")
print(f"Female: {sex_dist.get(2.0,0)/n*100:.1f}%")
print(f"Rural: {res_dist.get(3.0,0)/n*100:.1f}%")
print(f"Han: {eth_han/n*100:.1f}%")
print(f"Illiteracy: {illit:.1f}%")
print(f"Married: {mar_married/n*100:.1f}%")
print(f"Top 3 diseases: Hypertension({R['disease_prevalence']['Hypertension']['rate_pct']}%), "
      f"Heart Disease({R['disease_prevalence']['Heart Disease']['rate_pct']}%), "
      f"Cataract({R['disease_prevalence']['Cataract']['rate_pct']}%)")
print(f"Multimorbidity (>=2): {(dis_count>=2).mean()*100:.1f}%")
print(f"ADL disability: {adl_any/n*100:.1f}%")
print(f"Current smoker: {R['smoking_pct']}%")
print(f"BMI < 18.5 (underweight): {bmi_dist.get('Underweight',0)/len(bmi_clean)*100:.1f}%")
print(f"Self-rated health bad: {health_bad:.1f}%")
print(f"Fall in past year: {R['fall']['past_year_pct']}%")

print("\n=== Analysis Complete ===")
