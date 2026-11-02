"""Execute the migrated research notebooks in a fresh, isolated output directory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
ORDER = ("02_", "01_", "05b_", "06_", "07_", "09_", "10_")


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager

    class LoggedNotebookClient(NotebookClient):
        def process_message(self, msg, cell, cell_index):
            if msg["msg_type"] == "stream":
                message = msg["content"].get("text", "").strip()
                if message:
                    print(message, flush=True)
            return super().process_message(msg, cell, cell_index)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--resume", action="store_true", help="Resume only a failed run with unchanged source/data/environment")
    args = parser.parse_args()
    if Path(args.run_id).name != args.run_id or args.run_id in (".", ".."):
        parser.error("run-id must be a directory name")
    run = ROOT / "runs" / args.run_id
    manifest_path = run / "manifest.json"
    sources = {str(p.relative_to(ROOT)): digest(p) for folder in ("research_code", "shared_code", "notebooks")
               for p in sorted((ROOT / folder).rglob("*")) if p.suffix in (".py", ".ipynb")}
    sources["run_pipeline.py"] = digest(Path(__file__).resolve())
    sources["requirements.txt"] = digest(ROOT / "requirements.txt")
    upstream_sources = json.loads((ROOT / "history/source-provenance.json").read_text(encoding="utf-8"))["upstream_sha256"]
    data = {p.name: digest(p) for p in sorted((REPO / "data/raw").glob("*.csv"))}
    if len(data) != 7:
        raise RuntimeError("Expected the seven OULAD source CSVs")
    environment = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    identity = {"source_sha256": sources, "upstream_sha256": upstream_sources,
                "raw_sha256": data, "environment": environment}
    backend_model = REPO / "apps/backend/artifacts/model_hco_vnls_lightgbm_cutoff75.joblib"
    backend_digest = digest(backend_model)
    if args.resume:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["status"] == "completed" or any(manifest[k] != v for k, v in identity.items()):
            raise RuntimeError("Cannot resume completed run or changed inputs")
    else:
        run.mkdir(parents=True, exist_ok=False)
        manifest = {**identity, "started_at": datetime.now(timezone.utc).isoformat(),
                    "python": sys.version, "executable": sys.executable,
                    "backend_model_sha256_before": backend_digest,
                    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                    "protocol": {"split_seed": 41, "search_budget": 8, "population": 3,
                                 "alpha": .85, "threshold": .5, "search_seeds": [41, 77, 103, 211, 307],
                                 "note": "Historical protocol rerun; historical test is not a new holdout"},
                    "stages": [], "status": "running"}
    (run / "notebooks").mkdir(exist_ok=True)
    kernel_dir = run / "kernels" / "python3"
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Isolated ML rerun", "language": "python"
    }), encoding="utf-8")
    os.environ["ML_RUN_DIR"] = str(run)
    os.environ["MPLBACKEND"] = "Agg"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    def save():
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    try:
        for prefix in ORDER:
            source, = (ROOT / "notebooks").glob(prefix + "*.ipynb")
            if any(s["notebook"] == source.name and s["status"] == "completed" for s in manifest["stages"]):
                continue
            stage = {"notebook": source.name, "status": "running"}
            manifest["stages"].append(stage)
            save()
            print("START", source.name, flush=True)
            started = time.perf_counter()
            notebook = nbformat.read(source, as_version=4)
            def progress(cell, cell_index, **kwargs):
                if cell.cell_type == "code":
                    stage["current_cell"] = cell_index
                    save()
                    print(f"CELL {source.name} {cell_index}", flush=True)
            manager = KernelManager(kernel_name="python3", kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(run / "kernels")]))
            client = LoggedNotebookClient(notebook, km=manager, timeout=None, kernel_name="python3",
                                    resources={"metadata": {"path": str(ROOT)}}, on_cell_start=progress)
            try:
                client.execute(cleanup_kc=True)
            finally:
                nbformat.write(notebook, run / "notebooks" / source.name)
            stage.update(status="completed", seconds=time.perf_counter() - started)
            save()
            print("DONE", source.name, round(stage["seconds"], 2), flush=True)
        evaluate_test(run)
        if digest(backend_model) != manifest["backend_model_sha256_before"]:
            raise RuntimeError("Backend artifact changed during rerun; investigate before publishing")
        manifest["status"] = "completed"
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        manifest["output_sha256"] = {str(p.relative_to(run)): digest(p) for p in sorted(run.rglob("*"))
                                     if p.is_file() and p != manifest_path}
        save()
        print("COMPLETED", run, flush=True)
    except BaseException:
        manifest["status"] = "failed"
        manifest["error"] = traceback.format_exc()
        if manifest["stages"] and manifest["stages"][-1]["status"] == "running":
            manifest["stages"][-1]["status"] = "failed"
        save()
        raise


def evaluate_test(run):
    """Evaluate the frozen refit artifact once, without tuning on test."""
    import joblib
    import pandas as pd
    from research_code.evaluation import metric_table, risk_probability

    model_path = run / "mo_hinh/model_hco_vnls_lightgbm_cutoff75.joblib"
    artifact = joblib.load(model_path)
    frame = pd.read_csv(run / "results/du_lieu_cutoff_75.csv")
    test = frame.loc[frame.split.eq("test")].copy()
    probability = risk_probability(artifact["pipeline"], test[artifact["feature_columns"]])
    metrics = metric_table(test.risk, probability, artifact["threshold"])
    metrics.update(model_sha256=digest(model_path), scope="Historical OULAD test split, newly rerun; not an independent new holdout")
    (run / "results/test_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    test = test[["id_student", "code_module", "code_presentation", "risk"]]
    test["probability"] = probability
    test.to_csv(run / "results/test_predictions.csv", index=False)


if __name__ == "__main__":
    main()
