# Aging.AI Model Analysis

## Can we extract the models from the papers?

**Short answer: No.** Neither paper publishes model weights. Both papers describe
the architecture, hyperparameters, and training procedure in enough detail to
*retrain* the models, but the actual learned weights were never released. The
aging.ai website ran inference server-side (Django backend, standard HTML form
POST) — no weights were exposed to the client.

However, the papers give us everything needed to **build an equivalent model**
if we can assemble a suitable training dataset (e.g. from NHANES, which is
public and was actually used as a validation set in the v3 paper).

---

## Model v1.0 — Putin et al. 2016

### Architecture
- **Ensemble of 21 DNNs** combined via stacked generalization (ElasticNet meta-learner)
- Best single DNN: 5 layers — **2000 → 1500 → 1000 → 500 → 1** neurons
- Actually 4 hidden layers + 1 output neuron (regression output)
- Activation: **PReLU** (Parametric ReLU) after each layer
- Optimizer: **AdaGrad**
- Loss: **MSE** (mean squared error) with regularization
- Regularization: **Dropout 0.2** after each layer, **L2 weight decay**
- **Batch normalization** after the first 2 layers
- Training stopped at ~350 epochs (plateau)
- Hardware: NVIDIA Tesla K80

### Hyperparameter search (Table S1 — R² values)

| Architecture         | ReLU/AdaDelta | ReLU/AdaGrad | PReLU/AdaGrad |
|---------------------|---------------|--------------|---------------|
| 1000-1000-500       | 0.742         | 0.770        | 0.773         |
| 1000-1000-1000-500  | 0.745         | 0.782        | 0.792         |
| 1000-1000-1000-1000 | 0.750         | 0.784        | 0.785         |
| 1500-1500-1500-1500 | 0.754         | 0.791        | 0.795         |
| **2000-1500-1000-500** | 0.755      | 0.792        | **0.805**     |
| 2500-2500-2500-2500 | 0.745         | 0.775        | 0.781         |

### Input (41 blood markers + metadata)
All values min-max normalized to [0, 1] using: X_norm = (X - X_min) / (X_max - X_min)

The 41 markers (European metric, from the form):

| # | Marker | Min | Max | Reference Range | Units |
|---|--------|-----|-----|-----------------|-------|
| 1 | Albumin | 1 | 52.25 | 35–52 | g/l |
| 2 | Glucose | 0.35 | 32 | 3.9–5.8 | mmol/l |
| 3 | Alkaline phosphatase | 1 | 4337 | 20–120 | U/l |
| 4 | Urea (BUN) | 0.7 | 84.1 | 2.5–6.4 | mmol/l |
| 5 | Erythrocytes (RBC) | 0.79 | 9.25 | 3.5–5.5 | 10⁶/µl |
| 6 | Cholesterol | 1 | 20.19 | 3.37–5.96 | mmol/l |
| 7 | RDW | 1 | 44.2 | 11.5–14.5 | % |
| 8 | Alpha-2-globulins | 1 | 20.17 | 5.1–8.5 | g/l |
| 9 | Hematocrit | 8 | 66 | 37–50 | % |
| 10 | Lymphocytes | 0 | 98 | 20–40 | % |
| 11 | Alpha-amylase | 1 | 1562 | 28–100 | U/l |
| 12 | ESR (Westergren) | 0 | 1000 | 2–30 | mm/h |
| 13 | Bilirubin total | 1 | 614.1 | 1.7–21 | µmol/l |
| 14 | Bilirubin direct | 1 | 311.1 | <4.6 | µmol/l |
| 15 | Gamma-GT | 1 | 3889 | <32 | U/ml |
| 16 | Creatinine | 1 | 1917.2 | 53–97 | mmol/l |
| 17 | Lactate dehydrogenase | 1 | 9886 | <248 | U/l |
| 18 | Protein total | 1 | 134 | 64–83 | g/l |
| 19 | Alpha-1-globulins | 0.3 | 14.87 | 2.10–3.50 | g/l |
| 20 | Beta-globulins | 1 | 99.03 | 6.0–9.4 | g/l |
| 21 | Gamma-globulins | 0.27 | 75 | 8.0–13.5 | g/l |
| 22 | Triglycerides | 0.2 | 57.04 | 0.68–1.90 | mmol/l |
| 23 | Chloride | 1 | 1047 | 101–110 | mmol/l |
| 24 | HDL Cholesterol | 0 | 14.89 | <3.3 | mmol/l |
| 25 | LDL cholesterol | 0.14 | 18.03 | 1.81–4.04 | mmol/l |
| 26 | Calcium | 0.5 | 5.08 | 2.15–2.65 | mmol/l |
| 27 | Potassium | 1 | 10 | 3.4–5.1 | mmol/l |
| 28 | Sodium | 1 | 188 | 136–146 | mmol/l |
| 29 | Iron | 0.9 | 94.39 | 7.20–25.90 | µmol/l |
| 30 | Hemoglobin | 1 | 91 | 11.7–15.5 | g/dl |
| 31 | MCH | 1 | 50.8 | 27–31 | pg/cell |
| 32 | MCHC | 1 | 41.1 | 31.5–35.7 | g/dL |
| 33 | MCV | 1 | 135.6 | 82–95 | fl |
| 34 | Platelets | 1 | 1909 | 150–450 | 10³/µl |
| 35 | Leukocytes (WBC) | 0.1 | 458.85 | 4–10 | 10³/µl |
| 36 | ALT | 1 | 5609 | <41 | U/l |
| 37 | AST | 1 | 4489 | <47 | U/l |
| 38 | Basophils | 0 | 9 | <1.0 | % |
| 39 | Eosinophils | 0 | 56 | <5.0 | % |
| 40 | Monocytes | 0 | 89 | 3–9 | % |
| 41 | Neutrophils | 0 | 871 | 45–70 | % |

Plus metadata: weight (kg), height (cm), smoke (yes/no)

Note: The paper says 5 WBC markers (basophils, eosinophils, lymphocytes,
monocytes, neutrophils) were excluded from training due to high variability,
reducing from 46 to 41. But the form includes them. This suggests the
deployed model may differ from what was described in the paper.

### Training Data
- 62,419 records from Invitro Laboratory, Ltd (Russia)
- Routine health exam blood tests (not hospital patients)
- Split 90/10: 56,177 train / 6,242 test
- Outliers removed

### Top 5 markers by PFI importance
1. Albumin
2. Glucose
3. Alkaline phosphatase
4. Urea
5. Erythrocytes

### Descriptive statistics for top 10 markers (from Figure S1B)

| Marker | Mean | Std | Q25% | Q50% | Q75% | Min | Max |
|--------|------|-----|------|------|------|-----|-----|
| Albumin | 43.57 | 4.03 | 41.61 | 43.96 | 46.14 | 1.00 | 59.25 |
| Erythrocytes | 4.76 | 0.51 | 4.44 | 4.75 | 5.09 | 0.79 | 9.25 |
| Glucose | 5.57 | 1.26 | 4.99 | 5.36 | 5.80 | 0.35 | 32.24 |
| Alk. phosphatase | 85.96 | 78.52 | 56.00 | 70.00 | 89.00 | 1.00 | 4337.00 |
| Hematocrit | 40.89 | 4.43 | 38.20 | 40.90 | 43.90 | 8.00 | 66.00 |
| Urea | 5.17 | 2.21 | 3.90 | 4.90 | 6.00 | 0.70 | 84.10 |
| RDW | 13.71 | 1.97 | 12.70 | 13.20 | 13.90 | 1.00 | 44.20 |
| Cholesterol | 5.48 | 1.27 | 4.58 | 5.38 | 6.26 | 1.00 | 20.19 |
| Alpha-2-globulins | 7.06 | 1.31 | 6.18 | 6.86 | 7.70 | 1.00 | 20.17 |
| Lymphocytes | 35.48 | 10.07 | 29.00 | 35.00 | 41.30 | 0.00 | 98.00 |

### Performance
- Best single DNN: r=0.90, R²=0.80, MAE=6.07, ε-accuracy(10yr)=81.5%
- Full ensemble (21 DNNs + ElasticNet): r=0.91, R²=0.82, MAE=5.55, ε-accuracy=83.5%

---

## Model v2.0 — Unpublished

No paper published. Intermediate model with 33 input parameters.
The website said: "After extensive testing we may publish this multi-DNN
system in a peer-reviewed journal as we usually do."

### Input (33 markers)
Same as v1 minus: RDW, Alpha-2-globulins, Alpha-amylase, ESR, Bilirubin direct,
Alpha-1-globulins, Beta-globulins, Gamma-globulins. Added: Globulins (combined).
Replaced Chlorine→Chloride.

### Performance
- r=0.79, R²=0.63, MAE=6.2 years

---

## Model v3.0 — Mamoshina et al. 2018

### Architecture
- Single DNN (not an ensemble like v1)
- **Multilayer feed-forward** neural network (>3 layers, exact depth not specified)
- Activation: **Leaky ReLU** after each layer
- Optimizer: **EVE** (feedback-based SGD variant, Koushik & Hayashi 2016)
- Loss: **MAE** (mean absolute error) — different from v1 which used MSE
- Regularization: **Dropout 35%** after each layer
- 5-fold cross validation
- Grid search for architecture selection (specific winning architecture not stated)
- Framework: **Keras + Theano**
- Hardware: NVIDIA Titan X (Maxwell)

### Input (19 blood markers + sex + population)

| # | Marker | Min (EU) | Max (EU) | Reference Range (EU) | Units (EU) |
|---|--------|----------|----------|---------------------|------------|
| 1 | Albumin | 1 | 52.25 | 35–52 | g/l |
| 2 | Glucose | 0.35 | 32 | 3.9–5.8 | mmol/l |
| 3 | Urea (BUN) | 0.7 | 84.1 | 2.5–6.4 | mmol/l |
| 4 | Cholesterol | 1 | 20.19 | 3.37–5.96 | mmol/l |
| 5 | Protein total | 1 | 134 | 64–83 | g/l |
| 6 | Sodium | 1 | 188 | 136–146 | mmol/l |
| 7 | Creatinine | 1 | 1917.2 | 53–97 | mmol/l |
| 8 | Hemoglobin | 1 | 91 | 11.7–15.5 | g/dl |
| 9 | Bilirubin total | 1 | 614.1 | 1.7–21 | µmol/l |
| 10 | Triglycerides | 0.5 | 8 | 0.68–6 | mmol/l |
| 11 | HDL Cholesterol | 0 | 14.89 | <3.3 | mmol/l |
| 12 | LDL cholesterol | 0.14 | 18.03 | 1.81–4.04 | mmol/l |
| 13 | Calcium | 0.5 | 5.08 | 2.15–2.65 | mmol/l |
| 14 | Potassium | 1 | 10 | 3.4–5.1 | mmol/l |
| 15 | Hematocrit | 8 | 66 | 37–50 | % |
| 16 | MCHC | 1 | 41.1 | 31.5–35.7 | g/dL |
| 17 | MCV | 1 | 135.6 | 82–95 | fl |
| 18 | Platelets | 1 | 1909 | 150–450 | 10³/µl |
| 19 | Erythrocytes | 0.79 | 9.25 | 3.5–5.5 | 10⁶/µl |

Plus: sex (binary), ethnicity/population (dummy variables), weight (kg),
height (cm), smoke (yes/no)

### US metric equivalents
The form supports US units. Key differences:
- Albumin: 0.1–7.23 U/L (ref 3.5–5.5)
- Glucose: 6.37–581.8 mg/dL (ref 65–99)
- Urea: 1–235.6 mg/dL (ref 6–24)
- Cholesterol: 38.6–779.5 mg/dL (ref 100–199)
- Protein total: 0.1–13.4 g/dL (ref 6.0–8.5)
- Creatinine: 0.01–21.7 mg/dL (ref 0.57–1.00)
- Bilirubin total: 0–35.9 mg/dL (ref 0.0–1.2)
- Triglycerides: 0–5047 mg/dL (ref 0–149)
- HDL: 0–574.9 mg/dL (ref >39)
- LDL: 0–696.1 mg/dL (ref 0–99)
- Calcium: 2–20.32 mg/dL (ref 8.7–10.2)

### Training Data
- 142,379 total records from 3 populations:
  - Canadian: 20,699 (Alberta Health, IRB approved)
  - South Korean: 65,760 (Gachon University Gil Medical Center)
  - Eastern European: 55,920 (Invitro Laboratory)
- Split 80/20 train/test
- Ages ≥20 only (excluded pediatric)
- 4 Canadian markers (Urea, Total Protein, Calcium, Total Bilirubin)
  reconstructed via regression for part of the dataset

### Top markers by PFI importance (combined model)
1. Albumin
2. Glucose
3. Erythrocytes
4. Population type
5. Sex
6. Hemoglobin
7. Urea

### Performance
- Combined dataset: r=0.80, R²=0.65, MAE=5.94, ε-accuracy(10yr)=83%
- Eastern European only: r=0.84, R²=0.70, MAE=6.22
- South Korean only: r=0.70, R²=0.49, MAE=5.60
- Canadian only: r=0.72, R²=0.52, MAE=6.17
- NHANES validation: r=0.71, R²=0.50, MAE=9.93

### Mortality prediction
The model predicts all-cause mortality:
- Patients predicted older (Δ≥5 years): **increased** hazard ratio
  - Canada: HR 1.858 (69.5→185.8%)
  - NHANES: HR 1.662 (32.6→66.2%)
- Patients predicted younger (Δ≤-5 years): **decreased** hazard ratio
  - Canada: HR 0.315 (49.2→31.5%)
  - NHANES: HR 0.240 (30.4→24%)

---

## Strategy for reimplementation

Since the model weights are not published, we have two options:

### Option A: Train our own model on NHANES data
The NHANES dataset is **publicly available** and contains the blood markers
needed for the v3 model. The v3 paper already validated against NHANES.

Steps:
1. Download NHANES laboratory + demographics data (1996–2016)
2. Extract the 19 blood markers + sex + age
3. Train a DNN matching the v3 architecture description
4. Validate against reported NHANES performance (R²≈0.50, MAE≈9.93)
5. Potentially achieve better performance by training ON NHANES rather
   than just validating against it

Advantages:
- Fully reproducible, open data
- No IP concerns — our own model trained on public data
- Can validate mortality prediction using NHANES linked mortality files
- US-population focus is relevant for most users

### Option B: Use a simpler published model
Several groups have published open-source blood-test age predictors:
- Levine's "PhenoAge" (2018) — 9 biomarkers, published coefficients
- Various linear models from the aging literature

For our tools site, a simpler linear model with published coefficients
would be the easiest to implement client-side in JavaScript (no server needed).

### Recommended approach
**Option A** is most faithful to aging.ai. We can:
1. Train a model on NHANES (Python, offline)
2. Export the trained weights as JSON
3. Run inference client-side in JavaScript (feed-forward DNN is just
   matrix multiplications — trivially implementable in JS)
4. Host as a single HTML file on tools.andyreagan.com
