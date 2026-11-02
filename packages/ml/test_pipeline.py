import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from research_code.optimizers import run_search_budgeted
from research_code.data import create_asof
from shared_code.thuc_nghiem import chia_nhom, chon_dac_trung
from storage import consolidate_report_copies, resolve_run_file


class ProtocolTests(unittest.TestCase):
    def test_consolidated_outputs_keep_checksums_and_reject_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "runs/example"
            report = root / "reports/example"
            (run / "results").mkdir(parents=True)
            report.mkdir(parents=True)
            (report / "figures").mkdir()
            original = run / "results/test_metrics.json"
            canonical = report / "test_metrics.json"
            original.write_bytes(b'{"accuracy": 0.8}')
            canonical.write_bytes(original.read_bytes())
            locations = consolidate_report_copies(run, report)
            self.assertEqual(len(locations), 1)
            self.assertFalse(original.exists())
            self.assertEqual(resolve_run_file(run, "results/test_metrics.json"), canonical.resolve())
            self.assertEqual(resolve_run_file(run, "results\\test_metrics.json"), canonical.resolve())
            canonical.write_bytes(b'{"accuracy": 0.9}')
            with self.assertRaises(ValueError):
                resolve_run_file(run, "results/test_metrics.json")

    def test_different_results_are_not_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run, report = root / "runs/example", root / "reports/example"
            (run / "results").mkdir(parents=True)
            report.mkdir(parents=True)
            original = run / "results/test_metrics.json"
            original.write_bytes(b"old")
            (report / "test_metrics.json").write_bytes(b"new")
            self.assertEqual(consolidate_report_copies(run, report), {})
            self.assertEqual(original.read_bytes(), b"old")

    def test_asof_excludes_future_activity_and_withdrawn_enrollment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = {
                "studentInfo": {"id_student": [1, 2], "code_module": ["A", "A"],
                                "code_presentation": ["P", "P"], "final_result": ["Fail", "Withdrawn"]},
                "studentRegistration": {"id_student": [1, 2], "code_module": ["A", "A"],
                                        "code_presentation": ["P", "P"], "date_registration": [0, 0],
                                        "date_unregistration": [np.nan, 40]},
                "courses": {"code_module": ["A"], "code_presentation": ["P"], "module_presentation_length": [100]},
                "vle": {"id_site": [10], "activity_type": ["resource"]},
                "studentVle": {"id_student": [1, 1], "code_module": ["A", "A"],
                               "code_presentation": ["P", "P"], "id_site": [10, 10],
                               "date": [20, 90], "sum_click": [3, 999]},
                "assessments": {"id_assessment": [11, 12], "code_module": ["A", "A"],
                                "code_presentation": ["P", "P"], "date": [25, 90]},
                "studentAssessment": {"id_student": [1, 1], "id_assessment": [11, 12], "date_submitted": [30, 95]},
            }
            for name, values in sources.items():
                pd.DataFrame(values).to_csv(root / (name + ".csv"), index=False)
            frame = create_asof(root, .5)
            self.assertEqual(frame.id_student.tolist(), [1])
            self.assertEqual(frame.total_clicks_to_t.tolist(), [3])
            self.assertEqual(frame.assessments_submitted_to_t.tolist(), [1])
            self.assertEqual(frame.assessments_due_to_t.tolist(), [1])
            self.assertEqual(frame.risk.tolist(), [1])

    def test_group_assignment_is_unique_and_repeatable(self):
        ids = pd.Series(list(range(100)) * 3)
        a = chia_nhom(ids, seed=41)
        pd.testing.assert_frame_equal(a, chia_nhom(ids.sample(frac=1), seed=41))
        self.assertTrue(a.id_student.is_unique)
        self.assertEqual(a.split.value_counts().to_dict(), {"train": 70, "validation": 15, "test": 15})

    def test_features_exclude_labels_identity_and_partition(self):
        frame = pd.DataFrame(columns=["id_student", "risk", "final_result", "split", "split_extra",
                                      "cutoff", "cutoff_mode", "score_policy", "progress_fraction",
                                      "module_presentation_length", "clicks_recent_7"])
        self.assertEqual(chon_dac_trung(frame), ["clicks_recent_7"])

    def test_search_respects_uncached_budget(self):
        class Objective:
            frame = pd.DataFrame(columns=list("abcdefgh"))
            def __init__(self):
                self.calls = 0
                self.cache_hits = 0
                self.cache = {}
            def __call__(self, mask):
                key = tuple(mask)
                if key not in self.cache:
                    self.calls += 1
                    self.cache[key] = (float(np.mean(mask)), float(np.mean(mask)))
                else:
                    self.cache_hits += 1
                return self.cache[key]
        for method in ("HCO", "VNLS", "HCO-VNLS"):
            with self.subTest(method=method):
                result = run_search_budgeted(method, Objective(), seed=41, budget=8, population=3)
                self.assertLessEqual(result["objective_calls"], 8)
                self.assertGreater(result["selected_count"], 0)

    def test_run_directory_routes_outputs_without_changing_raw_source(self):
        source = Path(__file__).parent / "shared_code/thuc_nghiem.py"
        old = os.environ.get("ML_RUN_DIR")
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.environ["ML_RUN_DIR"] = directory
                spec = importlib.util.spec_from_file_location("isolated_paths", source)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(module.KET_QUA, Path(directory).resolve() / "results")
                self.assertEqual(module.DATA, Path(__file__).resolve().parents[2] / "data/raw")
        finally:
            if old is None:
                os.environ.pop("ML_RUN_DIR", None)
            else:
                os.environ["ML_RUN_DIR"] = old


if __name__ == "__main__":
    unittest.main()
