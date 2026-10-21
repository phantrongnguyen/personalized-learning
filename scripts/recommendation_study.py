"""Prepare synthetic expert cases and summarize only actual submitted ratings."""
import argparse
import json
from pathlib import Path
import sys
from datetime import datetime, date, timezone
from types import SimpleNamespace
from uuid import uuid5, NAMESPACE_URL

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
from services.support_evidence import snapshot_digest, REVIEW_VERSION
from services.support_suggestions import evaluate_suggestions, RULE_VERSION

RUBRIC = ('grounding', 'appropriateness', 'feasibility', 'clarity')


def cases():
    result = []
    variants = [({}, 'G02 và G03'), ({'clicks_recent_30': 0, 'days_since_last_activity': 30}, 'G02 và G04'),
        ({'late_submissions_to_t': 0, 'clicks_recent_7': 2, 'days_since_last_activity': 1}, 'Không có tín hiệu phù hợp'),
        ({'missing_review': True}, 'Thiếu xác nhận'), ({'aggregate_only': True}, 'Chỉ kiểm tra số tổng hợp'),
        ({'activity_complete': False}, 'Chỉ xác nhận bài đánh giá'),
        ({'assessments_complete': False}, 'Chỉ xác nhận hoạt động'),
        ({'clicks_recent_7': 10}, 'Click mâu thuẫn với số ngày gián đoạn'),
        ({'late_submissions_to_t': 5}, 'Bài trễ vượt tổng đã nộp'),
        ({'changed_after_review': True}, 'Chỉ số thay đổi sau xác nhận')]
    for index, (changes, purpose) in enumerate(variants, 1):
        changes = changes.copy(); case_id = f'C{index:02d}'
        special = {key: changes.pop(key, False) for key in ('missing_review', 'aggregate_only', 'changed_after_review')}
        complete = {key: changes.pop(key, True) for key in ('activity_complete', 'assessments_complete')}
        snapshot = SimpleNamespace(id=uuid5(NAMESPACE_URL, case_id), enrollment_id=uuid5(NAMESPACE_URL, case_id+'-enrollment'),
            cutoff_stage='CUTOFF_75', created_at=datetime(2026,10,20,tzinfo=timezone.utc),
            total_clicks_to_t=12, clicks_resource_to_t=4, clicks_url_to_t=2, active_days_to_t=3,
            active_day_ratio=.04, days_since_last_activity=7, clicks_recent_7=0, clicks_recent_30=4,
            assessments_submitted_to_t=4, late_submissions_to_t=1, submission_rate=.8,
            raw_features_json={'data_source': 'synthetic_demo'})
        for key,value in changes.items(): setattr(snapshot,key,value)
        presentation = SimpleNamespace(id=uuid5(NAMESPACE_URL,'study-presentation'), start_date=date(2026,7,1), module_presentation_length=100)
        review = dict(review_version=REVIEW_VERSION, review_scope='aggregate_only' if special['aggregate_only'] else 'demonstration',
            confirmed_by_user_id=str(uuid5(NAMESPACE_URL,'synthetic-reviewer')), confirmed_at='2026-10-20T00:00:00+00:00',
            source='Synthetic expert-study case, not real LMS', snapshot_day=75,
            snapshot_sha256=snapshot_digest(snapshot,presentation), **complete)
        if special['aggregate_only']: review.update(activity_complete=False, assessments_complete=False)
        if not special['missing_review']: snapshot.raw_features_json['support_evidence']=review
        if special['changed_after_review']: snapshot.total_clicks_to_t+=1
        state, suggestions, warnings, cutoff = evaluate_suggestions(snapshot,presentation,today=date(2026,10,21))
        result.append({'case_id':case_id,'data_source':'synthetic_demo','purpose':purpose,
            'features':{key:getattr(snapshot,key) for key in ('total_clicks_to_t','days_since_last_activity','clicks_recent_7','clicks_recent_30','assessments_submitted_to_t','late_submissions_to_t','submission_rate')},
            'cutoff_date':str(cutoff) if cutoff else None, 'system_status':state,
            'suggestions':suggestions,'warnings':warnings})
    return {'rule_version':RULE_VERSION,'case_type':'synthetic_protocol_examples','cases':result}


def summarize(document, case_ids):
    rows = document.get('ratings')
    if not isinstance(rows,list): raise ValueError('ratings must be a list of submitted expert ratings')
    seen=set(); totals={key:[] for key in RUBRIC}
    for row in rows:
        if not isinstance(row,dict): raise ValueError('Each rating must be an object')
        reviewer=row.get('reviewer_id')
        identity=(reviewer.strip() if isinstance(reviewer,str) else reviewer, row.get('case_id'))
        if not isinstance(identity[0],str) or not identity[0].strip() or identity[1] not in case_ids or identity in seen:
            raise ValueError('Unknown case, missing reviewer or duplicate rating')
        seen.add(identity)
        for key in RUBRIC:
            value=row.get(key)
            if type(value) is not int or not 1 <= value <= 5: raise ValueError('Scores must be integers from 1 to 5')
            totals[key].append(value)
        if any(row[key]<=2 for key in RUBRIC) and (not isinstance(row.get('comment'),str) or not row['comment'].strip()):
            raise ValueError('Low scores require an explanatory comment')
    import statistics
    coverage = {case:sum(key[1] == case for key in seen) for case in sorted(case_ids)}
    return {'status':'pending_expert_participation' if not rows else 'descriptive_expert_ratings',
        'ratings':len(rows),'reviewers':len({key[0] for key in seen}),
        'cases_reviewed':len({key[1] for key in seen}), 'cases_total':len(case_ids),
        'mean_scores':{key:sum(values)/len(values) if values else None for key,values in totals.items()},
        'median_scores':{key:statistics.median(values) if values else None for key,values in totals.items()},
        'score_distributions':{key:{str(score):values.count(score) for score in range(1,6)} for key,values in totals.items()},
        'case_rating_counts':coverage, 'cases_with_two_or_more_raters':sum(count >= 2 for count in coverage.values()),
        'limitation':'Expert ratings describe perceived suitability; they do not establish learning impact.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ratings',type=Path)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'reports/evaluation')
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    bundle=cases()
    (args.output_dir/'expert-cases.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    participant = {**bundle, 'cases':[{key:value for key,value in row.items() if key != 'purpose'} for row in bundle['cases']]}
    (args.output_dir/'participant-cases.json').write_text(json.dumps(participant,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    ratings=json.loads(args.ratings.read_text(encoding='utf-8')) if args.ratings else {'ratings':[]}
    summary=summarize(ratings,{row['case_id'] for row in bundle['cases']})
    (args.output_dir/'expert-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Synthetic cases prepared. Submitted expert ratings:',summary['ratings'])
