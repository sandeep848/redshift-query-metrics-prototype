import pandas as pd
import pytest

from capacity_planner import analyze


def sample(**overrides):
    values = {
        "queue_seconds": [0, 2, 40, 60],
        "execution_seconds": [10, 20, 40, 80],
        "spill_mb": [0, 0, 100, 200],
        "scanned_mb": [10, 20, 100, 200],
        "concurrency": [2, 5, 40, 60],
    }
    values.update(overrides)
    return pd.DataFrame(values)


def test_high_pressure_workload_recommends_scaling():
    report = analyze(sample())
    assert report.pressure_score >= 70
    assert "Scale compute" in report.recommendation


def test_missing_columns_fail_fast():
    with pytest.raises(ValueError):
        analyze(pd.DataFrame({"queue_seconds": [1]}))
