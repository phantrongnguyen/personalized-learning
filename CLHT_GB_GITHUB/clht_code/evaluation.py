from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, accuracy_score, brier_score_loss, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from .models import make_pipeline

def split_groups(frame, seed=42):
    groups = frame.id_student.to_numpy()
    train, holdout = next(GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=seed).split(frame, groups=groups))
    val_rel, test_rel = next(GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=seed+1).split(holdout, groups=groups[holdout]))
    return train, holdout[val_rel], holdout[test_rel]

def assert_disjoint(frame, splits):
    sets = [set(frame.iloc[i].id_student) for i in splits]
    assert not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])

def metric_table(y, probability, threshold=0.5):
    y = np.asarray(y, dtype=int); p = np.asarray(probability, dtype=float); pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    return {'accuracy': accuracy_score(y,pred), 'precision_risk': precision_score(y,pred,zero_division=0), 'recall_risk': recall_score(y,pred,zero_division=0), 'f1_risk': f1_score(y,pred,zero_division=0), 'weighted_f1': f1_score(y,pred,average='weighted',zero_division=0), 'average_precision_risk': average_precision_score(y,p), 'roc_auc': roc_auc_score(y,p), 'brier_score': brier_score_loss(y,p), 'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'alerts':int(pred.sum()),'n':len(y),'threshold':threshold}

def risk_probability(pipeline, frame):
    probs = pipeline.predict_proba(frame)
    classes = pipeline.named_steps['model'].classes_
    return probs[:, list(classes).index(1)]

def fit_score(train, y_train, valid, y_valid, config, threshold=0.5):
    pipeline = make_pipeline(train, config); pipeline.fit(train, y_train)
    result = metric_table(y_valid, risk_probability(pipeline, valid), threshold)
    result['model'] = config.name
    return pipeline, result

def group_cv_score(frame, y, groups, config, selected=None):
    selected = selected or list(frame.columns)
    scores=[]
    for train, valid in GroupKFold(n_splits=3).split(frame, y, groups):
        pipe=make_pipeline(frame.iloc[train][selected], config); pipe.fit(frame.iloc[train][selected], y[train])
        scores.append(average_precision_score(y[valid], risk_probability(pipe, frame.iloc[valid][selected])))
    return float(np.mean(scores))

