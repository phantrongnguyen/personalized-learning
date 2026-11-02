"""Audit frozen model evidence without fitting, tuning or exporting student rows."""
import argparse
import hashlib
import json
from pathlib import Path
import math
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''): value.update(block)
    return value.hexdigest()


def validate_metrics(metrics):
    tn, fp, fn, tp = (metrics[key] for key in ('tn', 'fp', 'fn', 'tp'))
    if any(type(value) is not int or value < 0 for value in (tn, fp, fn, tp)):
        raise ValueError('Invalid confusion counts')
    total = tn + fp + fn + tp
    if total <= 0 or metrics['test_rows'] != total: raise ValueError('Confusion counts disagree with test size')
    computed = {'accuracy': (tn + tp) / total, 'precision_risk': tp / (tp + fp),
        'recall_risk': tp / (tp + fn), 'f1_risk': 2 * tp / (2 * tp + fp + fn)}
    if any(not math.isclose(metrics[key], value, abs_tol=1e-10) for key, value in computed.items()):
        raise ValueError('Published count-based metrics disagree')
    return {**computed, 'miss_rate_risk': fn / (tp + fn), 'alerts': tp + fp, 'actual_risk': tp + fn}


def audit(feature_path=None):
    import pandas as pd
    model = ROOT / 'apps/backend/artifacts/model_hco_vnls_lightgbm_cutoff75.joblib'
    metadata_path = model.with_name('THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json')
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    published = json.loads((ROOT / 'reports/model_final/verified_metrics.json').read_text(encoding='utf-8'))
    if digest(model) != metadata['model_sha256'] or digest(model) != published['model_sha256']:
        raise ValueError('Frozen artifact hash differs')
    import sys
    sys.path.insert(0, str(ROOT))
    from reports.model_final.generate_charts import metadata_hash_matches
    if not metadata_hash_matches(metadata_path, published['metadata_sha256']): raise ValueError('Metadata content differs')
    validation = pd.read_csv(ROOT / 'packages/ml/history/results/hco_vnls_lightgbm_validation.csv')
    selected = validation.loc[(validation.cutoff == .75) & (validation.method == 'HCO-VNLS')].iloc[0]
    if selected.selected_columns.split('|') != metadata['feature_columns']: raise ValueError('Selected mask differs')
    if set(metadata['feature_columns']) & {'id_student', 'risk', 'final_result', 'split'}: raise ValueError('Target/identity leakage in selected columns')
    candidates = [feature_path] if feature_path else [ROOT / 'packages/ml/history/results/du_lieu_cutoff_75.csv']
    dataset = next((path for path in candidates if path and path.is_file()), None)
    source = {'available': dataset is not None, 'checksum_matches': None, 'split_disjoint_rechecked': False}
    if dataset:
        source['checksum_matches'] = digest(dataset) == metadata['data_sha256']
        if not source['checksum_matches']: raise ValueError('Feature source hash differs; do not attribute it to the frozen artifact')
        frame = pd.read_csv(dataset, usecols=['id_student', 'split'])
        if set(frame.split) != {'train', 'validation', 'test'}: raise ValueError('Unexpected split names')
        groups = {part: set(frame.loc[frame.split == part, 'id_student']) for part in ('train', 'validation', 'test')}
        overlap = {f'{a}_{b}': len(groups[a] & groups[b]) for a, b in [('train','validation'),('train','test'),('validation','test')]}
        if any(overlap.values()): raise ValueError('Students overlap between splits')
        source.update(split_disjoint_rechecked=True, overlap_counts=overlap, rows=frame.groupby('split').size().to_dict())
    notebooks = []
    origin = json.loads((ROOT / 'packages/ml/history/source-provenance.json').read_text(encoding='utf-8'))
    for name in ('05b_hco_vnls_lightgbm.ipynb','09_kiem_chung_dac_trung_hco_vnls.ipynb','10_dong_goi_model_hco_vnls_lightgbm_75.ipynb'):
        original = f"{origin['git_commit']}:{origin['original_root']}/notebooks/{name}"
        cells = json.loads(subprocess.check_output(['git', 'show', original], cwd=ROOT))['cells']
        code = '\n'.join(''.join(cell.get('source', [])) for cell in cells if cell['cell_type'] == 'code')
        notebooks.append({'name': name, 'code_sha256': hashlib.sha256(code.encode()).hexdigest(),
            'review_scope': 'source inspection only; notebook was not re-executed'})
    return {'status': 'source_rechecked' if dataset else 'partial_source_audit',
        'model_sha256': digest(model), 'metadata_sha256': digest(metadata_path),
        'historical_metadata_sha256': published['metadata_sha256'],
        'metadata_bytes_match': digest(metadata_path) == published['metadata_sha256'],
        'metadata_content_matches_allowing_only_line_endings': True,
        'feature_count': len(metadata['feature_columns']), 'threshold': metadata['threshold'],
        'count_metrics_recomputed': validate_metrics(published['metrics']),
        'feature_source': source, 'notebooks': notebooks,
        'refitted': False, 'threshold_changed': False,
        'limitations': ['AP/ROC-AUC are historical published values, not recomputed without archived row-level scores.',
            'Static notebook inspection does not prove the historical execution or independent unseen test use.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/test-results/priority3-model-audit.json')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit(args.features), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Frozen model and aggregate evidence audited; no fitting or tuning.')
