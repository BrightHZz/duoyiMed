**Table 3.** Top 20 features ranked by XGBoost gain-based importance, with clinical domain assignment.

| Rank | Feature | Domain | Gain Importance |
|---|---|---|---|
| 1 | age | Demographics | 0.046219 |
| 2 | physical_composite | Other | 0.041305 |
| 3 | current_drinker | Lifestyle | 0.032890 |
| 4 | chair_z | Function | 0.031239 |
| 5 | fried_lowact | Frailty | 0.030617 |
| 6 | disease_hypertension | Disease | 0.029549 |
| 7 | pulse_pressure | Vital Signs | 0.027951 |
| 8 | cci | Disease | 0.027493 |
| 9 | smoke_ever | Lifestyle | 0.027161 |
| 10 | disease_diabetes | Disease | 0.026577 |
| 11 | pulse | Vital Signs | 0.024958 |
| 12 | age_x_fried | Demographics | 0.023930 |
| 13 | fried_exhaust | Frailty | 0.023793 |
| 14 | disease_memory_disease | Disease | 0.023440 |
| 15 | disease_cancer | Disease | 0.023333 |
| 16 | fried_wtloss | Frailty | 0.022824 |
| 17 | dbp | Vital Signs | 0.022586 |
| 18 | age_x_cci | Demographics | 0.022202 |
| 19 | cesd_sum | Psychological | 0.021932 |
| 20 | gait_speed | Function | 0.021885 |

Gain importance represents the average improvement in model accuracy attributable to splits on each feature. Domain assignment is based on clinical categorization of predictor variables.
