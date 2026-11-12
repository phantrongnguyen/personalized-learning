"""Regression checks for broken references and misattributed model evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("check_docs", Path(__file__).resolve().parents[1] / "scripts/check_docs.py")
docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(docs)


class DocumentationChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def put(self, name, text):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def copy_metric_evidence(self):
        for name in (
            docs.THESIS,
            "reports/model_final/verified_metrics.json",
            "apps/backend/artifacts/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json",
            "apps/backend/artifacts/model_hco_vnls_lightgbm_cutoff75.joblib",
            "packages/ml/reports/rerun-20261025/test_metrics.json",
            "packages/ml/reports/rerun-20261025/provenance.json",
        ):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(docs.ROOT / name, target)

    def test_links_accept_unicode_heading_directory_and_ignore_fenced_examples(self):
        self.put("guide.md", "[ok](target.md#cấu-hình)\n[dir](assets/)\n```md\n[example](missing.md)\n```\n")
        self.put("target.md", "# Cấu hình\n")
        (self.root / "assets").mkdir()
        errors = []
        with patch.object(docs, "ROOT", self.root):
            self.assertEqual(docs.check_links("guide.md", errors), 2)
        self.assertEqual(errors, [])

    def test_links_reject_missing_file_stale_anchor_and_repository_escape(self):
        self.put("guide.md", "[missing](gone.md)\n[anchor](target.md#old)\n[out](../outside.md)\n")
        self.put("target.md", "# New\n")
        errors = []
        with patch.object(docs, "ROOT", self.root):
            docs.check_links("guide.md", errors)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("missing heading" in error for error in errors))
        self.assertTrue(any("escapes repository" in error for error in errors))

    def test_duplicate_heading_anchors_are_numbered(self):
        self.assertEqual(docs.anchors("# Same\n# Same\n"), {"same", "same-1"})

    def test_stale_metric_table_fails_then_can_be_regenerated(self):
        self.copy_metric_evidence()
        target = self.root / docs.THESIS
        target.write_text(target.read_text(encoding="utf-8").replace("0.861909", "0.999999", 1), encoding="utf-8")
        with patch.object(docs, "ROOT", self.root):
            errors = []
            docs.check_metrics(errors, False)
            self.assertTrue(any("Metric table is stale" in error for error in errors))
            errors = []
            docs.check_metrics(errors, True)
            docs.check_metrics(errors, False)
            self.assertEqual(errors, [])

    def test_relabeling_rerun_as_app_is_rejected_even_when_table_is_refreshed(self):
        self.copy_metric_evidence()
        target = self.root / "packages/ml/reports/rerun-20261025/test_metrics.json"
        metric = json.loads(target.read_text(encoding="utf-8"))
        metric["model_sha256"] = docs.load("reports/model_final/verified_metrics.json")["model_sha256"]
        target.write_text(json.dumps(metric), encoding="utf-8")
        with patch.object(docs, "ROOT", self.root):
            errors = []
            docs.check_metrics(errors, True)
        self.assertTrue(any("identities unexpectedly coincide" in error for error in errors))
        self.assertTrue(any("checksum differs" in error for error in errors))

    def test_missing_npm_script_is_rejected(self):
        errors = []
        with patch.object(docs, "COMMANDS", {"README.md": ["npm --prefix apps/frontend run nonexistent-docs-check"]}):
            docs.check_commands(errors)
        self.assertTrue(any("Unknown npm script" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
