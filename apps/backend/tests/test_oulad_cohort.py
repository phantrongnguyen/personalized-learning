"""Cohort selection does not use final outcomes or current model scores."""
import sys
from pathlib import Path

import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from load_oulad_cohort import eligible_ids


def test_cohort_selection_is_enrolled_at_cutoff_and_deterministic(monkeypatch, tmp_path):
    tables = {
        "studentInfo": pd.DataFrame({"id_student": [10, 20, 30, 40, 50],
                                     "final_result": ["Fail", "Pass", "Pass", "Withdrawn", "Fail"]}),
        "studentRegistration": pd.DataFrame({"id_student": [10, 20, 30, 40, 50],
            "date_registration": [-10, -10, 61, -10, -10],
            "date_unregistration": [None, None, None, 45, None]}),
        "courses": pd.DataFrame({"module_presentation_length": [80]}),
    }
    monkeypatch.setattr(pd, "read_parquet", lambda path, **kwargs: tables[path.stem])
    first = eligible_ids(tmp_path, "AAA", "2013J", 2, 42, "first")
    random_sample = eligible_ids(tmp_path, "AAA", "2013J", 2, 42, "random")
    assert first == [10, 20]
    assert random_sample == eligible_ids(tmp_path, "AAA", "2013J", 2, 42, "random")
    assert len(random_sample) == 2 and set(random_sample) <= {10, 20, 50}
