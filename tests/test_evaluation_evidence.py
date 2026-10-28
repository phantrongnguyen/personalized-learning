import importlib.util
from pathlib import Path
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def test_metrics_consistency_and_tampering():
    audit=module('audit_model_evidence')
    metrics=json.loads((ROOT/'reports/model_final/verified_metrics.json').read_text())['metrics']
    result=audit.validate_metrics(metrics)
    assert result['alerts']==844 and result['actual_risk']==1172
    with pytest.raises(ValueError): audit.validate_metrics({**metrics,'tn':0})


def test_cases_distinguish_missing_partial_and_changed_evidence():
    study=module('recommendation_study'); rows=study.cases()['cases']
    assert len(rows)==10 and all(row['data_source']=='synthetic_demo' for row in rows)
    assert rows[3]['system_status']=='insufficient_data'
    assert rows[4]['system_status']=='insufficient_data'
    assert rows[-1]['system_status']=='insufficient_data'
    assert [item['rule_id'] for item in rows[5]['suggestions']]==['G02_AGGREGATE']


def test_no_experts_means_no_scores_and_duplicate_or_invalid_ratings_fail():
    study=module('recommendation_study'); ids={'C01'}
    pending=study.summarize({'ratings':[]},ids)
    assert pending['status']=='pending_expert_participation'
    assert all(value is None for value in pending['mean_scores'].values())
    row=dict(reviewer_id='R01',case_id='C01',grounding=4,appropriateness=4,feasibility=4,clarity=4)
    with pytest.raises(ValueError): study.summarize({'ratings':[row,row]},ids)
    with pytest.raises(ValueError): study.summarize({'ratings':[{**row,'clarity':0}]},ids)
    assert study.summarize({'ratings':[row]},ids)['reviewers']==1


def test_group_split_implementation_keeps_repeated_students_together():
    import numpy as np
    from experiments.hco_vnls.shared_code.thuc_nghiem import chia_nhom
    assignments=chia_nhom(np.repeat(np.arange(100),3), seed=41)
    assert len(assignments)==100 and assignments.id_student.is_unique
    assert assignments.split.value_counts().to_dict()=={'train':70,'validation':15,'test':15}
    assert assignments.equals(chia_nhom(np.repeat(np.arange(100),3), seed=41))


def test_preprocessing_is_fitted_on_training_rows_only():
    import pandas as pd
    from sklearn.tree import DecisionTreeClassifier
    from experiments.hco_vnls.research_code.models import make_pipeline, ModelConfig
    train=pd.DataFrame({'numeric':[1.,3.], 'category':['A','A']})
    validation=pd.DataFrame({'numeric':[1000.], 'category':['B']})
    pipeline=make_pipeline(train,ModelConfig('synthetic-check',DecisionTreeClassifier(random_state=41)))
    pipeline.fit(train,[0,1]); pipeline.predict_proba(validation)
    transformer=pipeline.named_steps['preprocess']
    assert transformer.named_transformers_['num'].named_steps['imputer'].statistics_[0]==2
    assert transformer.named_transformers_['cat'].named_steps['onehot'].categories_[0].tolist()==['A']
