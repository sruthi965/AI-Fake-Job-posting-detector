# Experiment notes

Record each training run here so results can be compared later.

| Date | Dataset | Model | Precision | Recall | F1 | Notes |
| ---- | ------- | ----- | --------- | ----- | -- | ----- |
|      |         |       |           |       |    |       |

## Setup

- Features: TF-IDF (1-2 grams, min_df=2, max 50,000 features, English stop words) over title, description, requirements and presence flags for company, salary and employment type
- Models compared: Logistic Regression and Random Forest, both with balanced class weights
- Split: 80/20 stratified, fixed seed, exact duplicates removed first
- Selection rule: highest F1 on the fraudulent class, ties broken by recall

## Ideas to try

- Tune the decision threshold for higher recall (missing a scam costs more than a false alarm)
- Character n-grams and handcrafted features (fee keywords, free email domains)
- Cross-validation, and a time-based split to test generalization to newer postings
- Calibrate probabilities (`CalibratedClassifierCV`) so the percentage shown to users is more trustworthy
- Error analysis: read the false negatives and add rules or data for them

## Caveats

Metrics on `sample_job_postings.csv` come from synthetic template data and must not be reported as real performance.
