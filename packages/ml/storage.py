"""Locate archived outputs after content-identical copies have been consolidated."""
import hashlib
import json
from pathlib import Path


def resolve_run_file(run, relative):
    relative = str(relative).replace("\\", "/")
    run = Path(run).resolve()
    path = run / relative
    if path.is_file():
        return path
    index = run / "output-locations.json"
    locations = json.loads(index.read_text(encoding="utf-8")) if index.exists() else {}
    entry = locations.get(relative)
    if entry is None:
        raise FileNotFoundError(path)
    target = (run / entry["path"]).resolve()
    if not target.is_relative_to(run.parents[1]):
        raise ValueError("Archived output must stay inside packages/ml")
    if hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Consolidated output checksum differs")
    return target


def consolidate_report_copies(run, report):
    run, report = Path(run).resolve(), Path(report).resolve()
    index = run / "output-locations.json"
    locations = json.loads(index.read_text(encoding="utf-8")) if index.exists() else {}
    candidates = [("results/test_metrics.json", report / "test_metrics.json")]
    candidates += [("figures/" + p.name, p) for p in (report / "figures").glob("*.png")]
    import os
    for relative, canonical in candidates:
        original = run / relative
        if original.is_file() and original.read_bytes() == canonical.read_bytes():
            locations[relative] = {"path": os.path.relpath(canonical, run).replace("\\", "/"),
                                   "sha256": hashlib.sha256(canonical.read_bytes()).hexdigest()}
            # Persist the resolver before removing the redundant copy.
            index.write_text(json.dumps(locations, indent=2), encoding="utf-8")
            original.unlink()
    return locations
