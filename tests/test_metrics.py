import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))
from metrics import auroc, brier, cohen_kappa, ece, krippendorff_alpha_interval  # noqa: E402


def test_basic_metrics():
    assert brier([1, 0], [1, 0]) == 0
    assert ece([0.9] * 10, [1] * 9 + [0]) < 1e-9
    assert auroc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == 1.0
    assert auroc([0.5, 0.5], [1, 0]) == 0.5


def test_agreement():
    assert abs(cohen_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1) < 1e-9
    assert abs(krippendorff_alpha_interval([[1, 1], [3, 3], [5, 5]]) - 1) < 1e-9
    assert krippendorff_alpha_interval([[1, 5], [5, 1], [3, 3]]) < 0.3
