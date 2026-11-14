"""Dataset-level metrics: ECE, AUROC, reliability bins, bootstrap CIs, agreement (kappa, alpha).

Plain numpy, no sklearn, so it runs anywhere. Unit-tested in tests/test_metrics.py.
"""

from __future__ import annotations

import itertools

import numpy as np


def brier(conf, y) -> float:
    c, y = np.asarray(conf, float), np.asarray(y, float)
    return float(np.mean((c - y) ** 2))


def reliability_bins(conf, y, n_bins: int = 10) -> list[dict]:
    c, y = np.asarray(conf, float), np.asarray(y, float)
    idx = np.minimum((c * n_bins).astype(int), n_bins - 1)
    out = []
    for b in range(n_bins):
        m = idx == b
        if m.any():
            out.append({"bin": b, "lo": b / n_bins, "hi": (b + 1) / n_bins, "n": int(m.sum()),
                        "mean_conf": float(c[m].mean()), "accuracy": float(y[m].mean())})
    return out


def ece(conf, y, n_bins: int = 10) -> float:
    n = len(conf)
    return float(sum(b["n"] / n * abs(b["accuracy"] - b["mean_conf"]) for b in reliability_bins(conf, y, n_bins)))


def auroc(conf, y) -> float | None:
    """P(confidence of a random correct answer > that of a random wrong one); ties count 1/2."""
    c, y = np.asarray(conf, float), np.asarray(y, int)
    pos, neg = c[y == 1], c[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    greater = (pos[:, None] > neg[None, :]).sum()
    ties = (pos[:, None] == neg[None, :]).sum()
    return float((greater + 0.5 * ties) / (len(pos) * len(neg)))


def bootstrap_ci(values_by_item: dict, stat, n_boot: int = 2000, seed: int = 0, alpha: float = 0.05):
    """Resample ITEMS (questions), not epochs. values_by_item: {item_id: list of per-epoch rows}.
    stat: function(list of rows) -> float."""
    rng = np.random.default_rng(seed)
    keys = list(values_by_item)
    point = stat([r for k in keys for r in values_by_item[k]])
    boots = []
    for _ in range(n_boot):
        sample = rng.choice(len(keys), size=len(keys), replace=True)
        rows = [r for i in sample for r in values_by_item[keys[i]]]
        v = stat(rows)
        if v is not None:
            boots.append(v)
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2]) if boots else (np.nan, np.nan)
    return point, float(lo), float(hi)


def cohen_kappa(a, b, weights: str | None = "quadratic", categories=(1, 2, 3, 4, 5)) -> float | None:
    """Weighted Cohen's kappa for two raters on an ordinal scale."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 2:
        return None
    cats = list(categories)
    k = len(cats)
    pos = {c: i for i, c in enumerate(cats)}
    obs = np.zeros((k, k))
    for x, y in pairs:
        obs[pos[x], pos[y]] += 1
    obs /= obs.sum()
    exp = np.outer(obs.sum(1), obs.sum(0))
    i, j = np.indices((k, k))
    w = ((i - j) / (k - 1)) ** 2 if weights == "quadratic" else (i != j).astype(float)
    denom = (w * exp).sum()
    return None if denom == 0 else float(1 - (w * obs).sum() / denom)


def krippendorff_alpha_interval(ratings: list[list[float | None]]) -> float | None:
    """Krippendorff's alpha, interval metric. ratings: one list per item, one entry per rater
    (None = missing). Items with < 2 ratings are dropped."""
    units = [[v for v in r if v is not None] for r in ratings]
    units = [u for u in units if len(u) >= 2]
    if not units:
        return None
    n = sum(len(u) for u in units)
    d_o = sum(sum((a - b) ** 2 for a, b in itertools.permutations(u, 2)) / (len(u) - 1) for u in units) / n
    allv = [v for u in units for v in u]
    d_e = sum((a - b) ** 2 for a, b in itertools.permutations(allv, 2)) / (n * (n - 1))
    return None if d_e == 0 else float(1 - d_o / d_e)
