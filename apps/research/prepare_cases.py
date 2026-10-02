from hashlib import sha256
from pathlib import Path

import pandas as pd

KEYS = ["id_student", "code_module", "code_presentation"]
FEATURES = [
    "code_module", "code_presentation", "gender", "highest_education", "age_band",
    "studied_credits", "date_registration", "total_clicks_to_t", "clicks_resource_to_t",
    "clicks_url_to_t", "active_days_to_t", "assessments_due_to_t",
    "assessments_submitted_to_t", "late_submissions_to_t", "last_activity_day",
    "clicks_recent_7", "clicks_recent_30",
]


def training_audit(research_root: Path, percent: int):
    source = research_root / f"NghienCuu_HCO_VNLS/ket_qua/du_lieu_cutoff_{percent}.csv"
    columns = list(dict.fromkeys(KEYS + FEATURES + ["cutoff_day", "split", "missing_submissions_to_t"]))
    frame = pd.read_csv(source, usecols=columns)
    train = frame.loc[frame.split == "train"].copy()
    assessments = pd.read_csv(research_root / "data/assessments.csv")
    submissions = pd.read_csv(research_root / "data/studentAssessment.csv",
                              usecols=["id_student", "id_assessment", "date_submitted", "is_banked"])
    assert assessments.id_assessment.is_unique
    assert not train.duplicated(KEYS).any()
    assert not submissions.duplicated(["id_student", "id_assessment"]).any()
    courses = train[["code_module", "code_presentation", "cutoff_day"]].drop_duplicates()
    schedules = assessments.merge(courses, on=["code_module", "code_presentation"], validate="many_to_one")
    due = schedules.loc[schedules.date.notna() & (schedules.date <= schedules.cutoff_day)]
    due_counts = due.groupby(["code_module", "code_presentation"]).id_assessment.nunique().rename("due_exact")
    observed = submissions.merge(assessments, on="id_assessment", validate="many_to_one")
    observed = observed.merge(train[KEYS + ["cutoff_day"]], on=KEYS, validate="many_to_one")
    observed = observed.loc[observed.date_submitted <= observed.cutoff_day]
    submitted_due = observed.loc[observed.date.notna() & (observed.date <= observed.cutoff_day)]
    counts = submitted_due.groupby(KEYS).id_assessment.nunique().rename("submitted_due_exact")
    late = observed.loc[(observed.is_banked == 0) & observed.date.notna()
                        & (observed.date_submitted > observed.date)]
    late_counts = late.groupby(KEYS).id_assessment.nunique().rename("late_unbanked_exact")
    audit = train.merge(due_counts, on=["code_module", "code_presentation"], how="left")
    audit = audit.merge(counts, on=KEYS, how="left").merge(late_counts, on=KEYS, how="left")
    audit = audit.fillna({"submitted_due_exact": 0, "late_unbanked_exact": 0, "due_exact": 0})
    assert (audit.due_exact == audit.assessments_due_to_t).all()
    audit["missing_exact"] = audit.due_exact - audit.submitted_due_exact
    return audit, assessments, submissions, source


def make_payload(row, assessments, submissions):
    schedule = assessments.loc[(assessments.code_module == row.code_module)
                               & (assessments.code_presentation == row.code_presentation)]
    observed = submissions.loc[(submissions.id_student == row.id_student)
                               & (submissions.date_submitted <= row.cutoff_day)]
    records = schedule.merge(observed.drop(columns=["id_student"]), on="id_assessment", how="left", validate="one_to_one")
    records = records.sort_values(["date", "id_assessment"], na_position="last")
    evidence_records = []
    for index, record in enumerate(records.itertuples(), 1):
        evidence_records.append({
            "assessment_id": f"B{index:02d}",
            "due_day": None if pd.isna(record.date) else int(record.date),
            "submitted_day": None if pd.isna(record.date_submitted) else int(record.date_submitted),
            "is_banked": False if pd.isna(record.is_banked) else bool(record.is_banked),
            "is_exempt": False,
        })
    features = {}
    for name in FEATURES:
        value = row[name]
        features[name] = None if pd.isna(value) else value.item() if hasattr(value, "item") else value
    return {
        "features": features,
        "evidence": {"snapshot_day": int(row.cutoff_day), "enrollment_active": True,
                     "feature_data_confirmed": True, "activity_complete": True,
                     "assessments_complete": True, "assessments": evidence_records},
    }


def build_cases(research_root: Path):
    audit, assessments, submissions, source = training_audit(research_root, 75)
    specifications = [
        ("bai-den-han", "Cần kiểm tra bài đến hạn", "Vẫn có tương tác nhưng còn bài chưa có bản ghi hoàn thành.", audit.missing_exact > 0),
        ("nop-tre", "Đã nộp đủ, từng nộp trễ", "Phân biệt thiếu bài với việc nộp sau hạn chung.", (audit.late_unbanked_exact > 0) & (audit.missing_exact == 0)),
        ("gian-doan-7", "Một tuần chưa có tương tác", "Nhìn vào cửa sổ 7 ngày, không kết luận sinh viên không học.", (audit.clicks_recent_7 == 0) & (audit.clicks_recent_30 > 0)),
        ("gian-doan-30", "Một tháng chưa có tương tác", "Có lịch sử trước đó; cần xác nhận tình trạng học hiện tại.", (audit.clicks_recent_30 == 0) & (audit.total_clicks_to_t > 0)),
        ("nop-som", "Nộp sớm không bù được bài thiếu", "Đối chiếu từng mã bài thay vì lấy tổng đến hạn trừ tổng đã nộp.", audit.missing_exact > audit.missing_submissions_to_t),
        ("khong-khop", "Chưa có tình huống cần gợi ý", "Không cố tạo lời khuyên khi bốn điều kiện không khớp.", (audit.missing_exact == 0) & (audit.late_unbanked_exact == 0) & (audit.clicks_recent_7 > 0)),
    ]
    cases = []
    for case_id, title, summary, mask in specifications:
        row = audit.loc[mask].iloc[0]
        cases.append({
            "id": case_id, "title": title, "summary": summary,
            "source_notice": "Trích rút một hồ sơ train OULAD tại cutoff 75%; bỏ mã sinh viên và kết quả cuối kỳ, đổi mã bài thành B01… Không coi là dữ liệu đã ẩn danh tuyệt đối.",
            "source_kind": "research_snapshot", "source_sha256": sha256(source.read_bytes()).hexdigest(),
            "payload": make_payload(row, assessments, submissions),
        })
    cases.append({
        "id": "thieu-bang-chung", "title": "Thiếu bằng chứng: hệ thống từ chối",
        "summary": "Tình huống kiểm thử tổng hợp, không phải một sinh viên thật.",
        "source_notice": "Sao chép đầu vào minh họa rồi bỏ xác nhận nguồn để kiểm tra trạng thái thiếu dữ liệu; không chạy dự báo.",
        "source_kind": "synthetic_test",
        "payload": {"features": dict(cases[0]["payload"]["features"]),
                    "evidence": {"snapshot_day": cases[0]["payload"]["evidence"]["snapshot_day"],
                                 "enrollment_active": None, "feature_data_confirmed": False,
                                 "activity_complete": False, "assessments_complete": False, "assessments": []}},
    })
    return cases
