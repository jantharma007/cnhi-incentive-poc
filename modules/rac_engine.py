"""Risk-Adjusted Capitation calculation engine."""

import numpy as np
import pandas as pd

from config.defaults import AGE_SEX_ADJUSTMENTS, DISEASE_WEIGHTS, COMORBIDITY_TERMS


def _age_to_band(age: int) -> str:
    if age <= 14:
        return "0-14"
    elif age <= 29:
        return "15-29"
    elif age <= 44:
        return "30-44"
    elif age <= 59:
        return "45-59"
    elif age <= 74:
        return "60-74"
    else:
        return "75+"


def calculate_risk_scores(
    population: pd.DataFrame,
    age_sex_adj: dict | None = None,
    disease_weights: dict | None = None,
    comorbidity_terms: dict | None = None,
) -> pd.Series:
    """Calculate risk score for every patient.

    Parameters allow overriding default weights (for sidebar sliders).
    Returns a Series of risk scores aligned with the population index.
    """
    if age_sex_adj is None:
        age_sex_adj = AGE_SEX_ADJUSTMENTS
    if disease_weights is None:
        disease_weights = DISEASE_WEIGHTS
    if comorbidity_terms is None:
        comorbidity_terms = COMORBIDITY_TERMS

    n = len(population)
    scores = np.ones(n, dtype=float)  # base score = 1.0

    # Age-sex adjustment
    age_bands = population["age"].apply(_age_to_band)
    for (sex, band), adj in age_sex_adj.items():
        mask = (population["sex"] == sex) & (age_bands == band)
        scores[mask.values] += adj

    # Chronic disease weights
    condition_cols = {
        "diabetes": "has_diabetes",
        "cvd": "has_cvd",
        "respiratory": "has_respiratory",
        "mental_health": "has_mental_health",
        "obesity": "has_obesity",
    }
    for condition, col in condition_cols.items():
        weight = disease_weights.get(condition, 0)
        scores[population[col].values] += weight

    # Comorbidity interaction
    comorb = population["comorbidity_count"].values
    for threshold in sorted(comorbidity_terms.keys()):
        term = comorbidity_terms[threshold]
        if threshold == max(comorbidity_terms.keys()):
            mask = comorb >= threshold
        else:
            mask = comorb == threshold
        scores[mask] += term

    # Floor at 0.1 to avoid negative/zero scores
    scores = np.maximum(scores, 0.1)

    # Normalize so the population-wide mean risk score equals 1.0
    # This is standard practice in HCC risk adjustment (CMS applies a similar step)
    pop_mean = scores.mean()
    if pop_mean > 0:
        scores = scores / pop_mean

    return pd.Series(scores, index=population.index, name="risk_score")


def calculate_rac_payments(
    population: pd.DataFrame,
    risk_scores: pd.Series,
    base_pmpm: float,
) -> pd.DataFrame:
    """Calculate annual RAC payments per patient and summarise by provider.

    Returns a summary DataFrame with one row per provider.
    """
    annual_payment = base_pmpm * risk_scores * 12

    df = population[["provider_id"]].copy()
    df["risk_score"] = risk_scores
    df["annual_payment"] = annual_payment

    summary = df.groupby("provider_id").agg(
        panel_size=("risk_score", "count"),
        avg_risk_score=("risk_score", "mean"),
        total_rac_payment=("annual_payment", "sum"),
    ).reset_index()

    summary["per_capita_payment"] = summary["total_rac_payment"] / summary["panel_size"]

    return summary
