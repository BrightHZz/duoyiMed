# PIC 数据库 (Pediatric Intensive Care)

## 概述

PIC（儿科重症监护数据库）是一个单中心儿科重症监护临床数据库，收录了浙江大学医学院附属儿童医院2010年11月至2018年12月期间PICU/NICU/CCU住院患者的临床数据。

- **版本**: 1.2.0
- **患者数**: ~12,881
- **住院数**: ~13,449
- **ICU 停留数**: ~13,941
- **数据年限**: 2010/11 - 2018/12
- **MySQL 连接**: `mysql -u duoyi -p Aa123456 -h localhost PIC`

## 表一览

| 表名 | 说明 | 行数 | 字段数 |
|------|------|------|--------|
| [[pic-admissions]] | 住院记录 | 13,449 | 19 |
| [[pic-chartevents]] | 生命体征/图表事件 | 2,278,978 | 10 |
| [[pic-d_icd_diagnoses]] | ICD诊断字典 | 25,379 | 5 |
| [[pic-d_items]] | 图表事件项目字典 | 479 | 7 |
| [[pic-d_labitems]] | 检验项目字典 | 832 | 7 |
| [[pic-diagnoses_icd]] | 诊断ICD编码 | 22,712 | 6 |
| [[pic-emr_symptoms]] | 电子病历症状 | 402,142 | 8 |
| [[pic-icustays]] | ICU停留记录 | 13,941 | 11 |
| [[pic-inputevents]] | 入量记录 | 26,884 | 8 |
| [[pic-labevents]] | 检验结果 | 10,094,117 | 9 |
| [[pic-microbiologyevents]] | 微生物培养结果 | 183,869 | 14 |
| [[pic-or_exam_reports]] | 检查报告 | 183,809 | 8 |
| [[pic-outputevents]] | 出量记录 | 39,891 | 9 |
| [[pic-patients]] | 患者基本信息 | 12,881 | 6 |
| [[pic-prescriptions]] | 处方记录 | 1,256,591 | 13 |
| [[pic-surgery_info]] | 手术信息 | 7,488 | 12 |
| [[pic-surgery_vital_signs]] | 术中生命体征 | 1,944,187 | 9 |

## 表分类

### 患者与住院管理
- [[pic-patients]] — 患者基本信息（性别、出生日期、死亡标记）
- [[pic-admissions]] — 住院记录（入院/出院时间、科室、保险等）
- [[pic-icustays]] — ICU停留记录（入ICU/出ICU时间、LOS）

### 临床事件
- [[pic-chartevents]] — 生命体征与图表事件（最大表之一）
- [[pic-emr_symptoms]] — 电子病历症状记录
- [[pic-inputevents]] — 入量记录（输液等）
- [[pic-outputevents]] — 出量记录（尿量等）

### 检验与微生物
- [[pic-labevents]] — 检验结果（最大表，~1000万行）
- [[pic-microbiologyevents]] — 微生物培养与药敏结果

### 诊断与检查
- [[pic-diagnoses_icd]] — 诊断ICD编码
- [[pic-d_icd_diagnoses]] — ICD诊断字典
- [[pic-or_exam_reports]] — 检查报告

### 字典表
- [[pic-d_items]] — 图表事件项目字典
- [[pic-d_labitems]] — 检验项目字典

### 用药与手术
- [[pic-prescriptions]] — 处方记录（~125万行）
- [[pic-surgery_info]] — 手术信息（手术名称、麻醉方式）
- [[pic-surgery_vital_signs]] — 术中生命体征（~194万行）

## 时间字段说明

- **CHARTTIME vs STORETIME**：CHARTTIME 记录观察发生的时间，通常是数据实际被测量的最近似时间。STORETIME 记录观察被临床工作人员手动输入或手动验证的时间，逻辑上在 CHARTTIME 之后，通常晚几个小时。
- **LABEVENTS 的 CHARTTIME** 例外：是体液**采集**时间（不是结果出来的时间），且该表没有 STORETIME（因数据未经临床人员验证）。
- **ADMITTIME / DISCHTIME / DEATHTIME**：入院/出院/院内死亡时间
- **INTIME / OUTTIME**：患者进入/离开ICU的时间
- **STARTTIME / ENDTIME**：时间段开始/结束，如输液期间
- **DOB / DOD**：出生/死亡日期（已偏移）
- **EXAMTIME / REPORTTIME**：检查执行/报告生成时间（or_exam_reports）
- **RECORDTIME**：病历记录时间（emr_symptoms）
- **MONITORTIME**：监护仪记录时间（surgery_vital_signs）
- **ANES_START_TIME / ANES_END_TIME**：麻醉开始/结束时间（surgery_info）
- **SURGERY_START_TIME / SURGERY_END_TIME**：手术开始/结束时间（surgery_info）

## ER 图

核心关联：
```
PATIENTS (SUBJECT_ID)
  └── ADMISSIONS (SUBJECT_ID, HADM_ID)
        ├── ICUSTAYS (SUBJECT_ID, HADM_ID, ICUSTAY_ID)
        ├── DIAGNOSES_ICD (SUBJECT_ID, HADM_ID)
        ├── CHARTEVENTS (SUBJECT_ID, HADM_ID, ICUSTAY_ID)
        ├── LABEVENTS (SUBJECT_ID, HADM_ID)
        ├── MICROBIOLOGYEVENTS (SUBJECT_ID, HADM_ID)
        ├── INPUTEVENTS (SUBJECT_ID, HADM_ID, ICUSTAY_ID)
        ├── OUTPUTEVENTS (SUBJECT_ID, HADM_ID, ICUSTAY_ID)
        ├── PRESCRIPTIONS (SUBJECT_ID, HADM_ID, ICUSTAY_ID)
        ├── EMR_SYMPTOMS (SUBJECT_ID, HADM_ID)
        ├── OR_EXAM_REPORTS (SUBJECT_ID, HADM_ID)
        ├── SURGERY_INFO (SUBJECT_ID, HADM_ID)
        └── SURGERY_VITAL_SIGNS (SUBJECT_ID, HADM_ID)
```