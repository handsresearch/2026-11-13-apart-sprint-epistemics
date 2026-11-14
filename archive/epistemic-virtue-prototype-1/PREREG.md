# Pre-registration

Committed before the full run. Pilot results (3 epochs, ~20 items per condition) may inform data
cleaning and prompt fixes only; hypotheses below are fixed.

## Manipulation checks (positive controls; if these fail, the metric is broken, not the models)

- **C1.** `sycophantic` has a higher bad-flip rate under `assert_wrong` than `neutral`, for every model.
- **C2.** `overconfident` has a worse stated-confidence Brier score and a higher overconfidence rate than `neutral`.
- **C3.** `overconfident` has a lower status-match rate on contested/forecast/unknowable questions than `neutral`.

## Hypotheses

- **H1 (pressure).** Under `neutral`, the bad-flip rate after 3 rounds of `assert_wrong` exceeds the
  `neutral_reask` baseline for at least 3 of 4 models.
- **H2 (pressure).** Flip rates rise with each rebuttal round (turn 1 < turn 2 < turn 3).
- **H3 (calibration).** Stated confidence is worse calibrated (higher Brier) than consistency
  confidence for at least 3 of 4 models.
- **H4 (graders, headline).** Agreement between graders on the 1–5 rubric is at most moderate
  (Krippendorff's alpha < 0.67), and lower on contested/forecast questions than on settled ones.
- **H5 (graders).** The automatic status-match signal correlates positively with mean grader score.
- **H6 (intervention, exploratory).** `careful` lowers bad flips and overconfidence relative to `neutral`.

## Analysis plan

- Unit of resampling: questions (epochs stay together); 95% bootstrap CIs, 2000 resamples.
- Report public and private splits separately, plus parse-failure and format-retry rates per model.
- Agreement: Krippendorff's alpha (interval) across graders; pairwise quadratic-weighted Cohen's kappa;
  50 disagreements hand-labelled independently by both authors, with human–human kappa as the ceiling.
- No multiple-comparison correction for C1–C3 (checks); H1–H5 are reported with CIs, H6 as exploratory.
