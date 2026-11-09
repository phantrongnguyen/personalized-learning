import React, { useEffect, useRef, useState } from 'react';
import { SnapshotInspection, SnapshotReviewPayload } from '@shared/types';
import { inspectSnapshotApi, reviewSnapshotApi } from '../../services/api';

interface Props {
  apiBase: string;
  presentationId: string;
  studentId: string;
  snapshotId: string;
  onReviewed: () => void;
}

const labels: Record<string, string> = {
  total_clicks_to_t: 'Tổng click', clicks_resource_to_t: 'Click tài liệu', clicks_url_to_t: 'Click liên kết',
  active_days_to_t: 'Ngày có hoạt động', active_day_ratio: 'Tỷ lệ ngày hoạt động',
  days_since_last_activity: 'Ngày không có click đến cutoff', clicks_recent_7: 'Click 7 ngày',
  clicks_recent_30: 'Click 30 ngày', assessments_submitted_to_t: 'Bài đã nộp',
  late_submissions_to_t: 'Bài trễ', submission_rate: 'Tỷ lệ nộp',
};

export const SnapshotEvidenceReview: React.FC<Props> = props => {
  const [preview, setPreview] = useState<SnapshotInspection | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [scope, setScope] = useState<SnapshotReviewPayload['review_scope']>('aggregate_only');
  const [source, setSource] = useState('');
  const [note, setNote] = useState('');
  const [activity, setActivity] = useState(false);
  const [assessments, setAssessments] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);

  const load = async () => {
    setBusy(true); setError('');
    try {
      const data = await inspectSnapshotApi(props.apiBase, props.presentationId, props.studentId, props.snapshotId);
      if (alive.current) setPreview(data);
    } catch (err) { if (alive.current) setError((err as Error).message); }
    finally { if (alive.current) setBusy(false); }
  };
  const submit = async () => {
    if (!preview || !acknowledged) return;
    setBusy(true); setError('');
    try {
      await reviewSnapshotApi(props.apiBase, props.presentationId, props.studentId, props.snapshotId, {
        snapshot_sha256: preview.snapshot_sha256, review_scope: scope,
        source_reference: source.trim(), review_note: note.trim(),
        activity_complete: scope === 'aggregate_only' ? false : activity,
        assessments_complete: scope === 'aggregate_only' ? false : assessments,
        acknowledged_limitations: true,
      });
      if (alive.current) props.onReviewed();
    } catch (err) { if (alive.current) setError((err as Error).message); }
    finally { if (alive.current) setBusy(false); }
  };
  return <details className="text-xs border border-slate-700 rounded-xl p-3 mb-4">
    <summary className="cursor-pointer text-slate-200">Rà soát và xác nhận nguồn snapshot</summary>
    <p className="text-slate-400 my-2">Giảng viên phụ trách chịu trách nhiệm đối chiếu nguồn. Kiểm tra các số trong database không chứng minh log LMS đầy đủ.</p>
    {!preview && <button type="button" disabled={busy} onClick={load} className="text-cyan-300 underline">Đọc snapshot từ database</button>}
    {error && <p role="alert" className="text-rose-300 my-2">{error}</p>}
    {preview && <div className="space-y-3">
      <p className="text-amber-300">Nguồn: {preview.data_source || 'Chưa xác nhận'} · Mốc quan sát: {preview.cutoff_date || 'Chưa rõ'}. Ngày ghi DB không thay thế ngày quan sát.</p>
      <dl className="grid grid-cols-2 gap-2 text-slate-300">{Object.entries(preview.features).map(([key, value]) =>
        <div key={key}><dt>{labels[key] || key}</dt><dd>{value}</dd></div>)}</dl>
      {preview.issues.map(issue => <p key={issue} className="text-rose-300">{issue}</p>)}
      <label className="block text-slate-300">Phạm vi rà soát
        <select value={scope} onChange={e => { setScope(e.target.value as typeof scope); setActivity(false); setAssessments(false); }} className="block w-full bg-slate-950 p-2 rounded mt-1">
          <option value="aggregate_only">Chỉ kiểm tra số liệu tổng hợp — chưa đủ căn cứ</option>
          <option value="demonstration">Kiểm chứng luồng bằng dữ liệu minh họa</option>
          {preview.data_source !== 'synthetic_demo' && <option value="source_verified">Đã đối chiếu nguồn và phạm vi dữ liệu</option>}
        </select>
      </label>
      <label className="block text-slate-300">Tham chiếu nguồn đã kiểm tra
        <input value={source} maxLength={500} onChange={e => setSource(e.target.value)} className="block w-full bg-slate-950 p-2 rounded mt-1" placeholder="Mã bản ghi, biên bản hoặc nguồn đối chiếu; không nhập mật khẩu" />
      </label>
      <label className="block text-slate-300">Nội dung đã đối chiếu và giới hạn còn lại (ít nhất 20 ký tự)
        <textarea value={note} maxLength={2000} onChange={e => setNote(e.target.value)} className="block w-full bg-slate-950 p-2 rounded mt-1" />
      </label>
      {scope !== 'aggregate_only' && <div className="space-y-2 text-slate-300">
        <label className="block"><input type="checkbox" checked={activity} onChange={e => setActivity(e.target.checked)} /> Đã đối chiếu log hoạt động đầy đủ đến mốc quan sát</label>
        <label className="block"><input type="checkbox" checked={assessments} onChange={e => setAssessments(e.target.checked)} /> Đã đối chiếu phạm vi bài đánh giá đầy đủ đến mốc quan sát</label>
      </div>}
      {scope === 'demonstration' && <p className="text-amber-300">Bản mới sẽ mang nhãn minh họa; không xác nhận đây là nguồn LMS thực.</p>}
      <label className="block text-slate-300"><input type="checkbox" checked={acknowledged} onChange={e => setAcknowledged(e.target.checked)} /> Tôi chịu trách nhiệm về nội dung xác nhận và hiểu hệ thống không tự kiểm toán nguồn gốc hay bài/hạn nộp riêng.</label>
      <p className="text-slate-400">Lưu bản snapshot mới và người xác nhận vào audit; không sửa lịch sử cũ, không tự chạy dự báo hoặc tạo nhiệm vụ.</p>
      <button type="button" onClick={submit} disabled={busy || !acknowledged || note.trim().length < 20 || source.trim().length < 5 || preview.issues.length > 0 || (scope === 'source_verified' && !activity && !assessments)} className="px-3 py-2 rounded bg-cyan-800 text-white disabled:opacity-40">Lưu xác nhận</button>
    </div>}
  </details>;
};
