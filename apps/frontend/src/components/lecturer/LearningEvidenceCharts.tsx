import React, { useState } from 'react';
import { CourseSuggestionResponse, StudentFeatures } from '@shared/types';

type Assessment = NonNullable<CourseSuggestionResponse['assessment_details']>[number];
type Status = 'all' | 'onTime' | 'late' | 'missing';
const statusOf = (item: Assessment): Exclude<Status, 'all'> => item.submitted_day == null
  ? 'missing' : item.submitted_day > item.due_day ? 'late' : 'onTime';
const statuses = [
  { id: 'onTime', label: 'Trong hạn chung', color: 'bg-sky-400' },
  { id: 'late', label: 'Sau hạn chung', color: 'bg-amber-400' },
  { id: 'missing', label: 'Chưa ghi nhận nộp', color: 'bg-slate-500' },
] as const;
const number = (value: number) => value.toLocaleString('vi-VN', { maximumFractionDigits: 2 });
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const count = (value: unknown): value is number => finite(value) && Number.isInteger(value) && value >= 0;
const label = (item: Assessment) => `${item.type} #${item.id}`;

export function activityWindows(inputs: Partial<StudentFeatures> | null | undefined, cutoff: number | null | undefined) {
  if (!inputs || !count(cutoff) || cutoff < 30 || !count(inputs.clicks_recent_7)
    || !count(inputs.clicks_recent_30) || !count(inputs.total_clicks_to_t)
    || inputs.clicks_recent_7 > inputs.clicks_recent_30 || inputs.clicks_recent_30 > inputs.total_clicks_to_t) return null;
  return [
    { label: '23 ngày trước đó', clicks: inputs.clicks_recent_30 - inputs.clicks_recent_7, days: 23 },
    { label: '7 ngày cuối', clicks: inputs.clicks_recent_7, days: 7 },
  ].map(item => ({ ...item, average: item.clicks / item.days }));
}

const Frame: React.FC<{ title: string; note: string; children: React.ReactNode }> = ({ title, note, children }) => (
  <section className="min-w-0 rounded-xl border border-slate-700 bg-slate-950/50 p-4">
    <h6 className="text-sm font-semibold text-white">{title}</h6>
    <p className="mt-1 text-xs leading-relaxed text-slate-400">{note}</p>
    <div className="mt-4">{children}</div>
  </section>
);
const Empty: React.FC<{ children: React.ReactNode }> = ({ children }) => <p className="rounded-lg border border-dashed border-slate-600 p-3 text-xs text-slate-400">{children}</p>;

export const LearningEvidenceCharts: React.FC<{
  detail: CourseSuggestionResponse;
  inputs: Partial<StudentFeatures> | null | undefined;
  group: 'assessment' | 'activity';
}> = ({ detail, inputs, group }) => {
  const [selected, setSelected] = useState<Status>('all');
  const records = detail.assessment_details ?? [];
  const cutoff = detail.cutoff_day;
  const validRecords = records.length > 0 && count(cutoff)
    && new Set(records.map(item => item.id)).size === records.length
    && records.every(item => count(item.id) && count(item.due_day) && item.due_day <= cutoff
      && (item.submitted_day === null || (count(item.submitted_day) && item.submitted_day <= cutoff)));
  const windows = activityWindows(inputs, cutoff);
  const ratio = inputs?.active_day_ratio;
  const activeDays = inputs?.active_days_to_t;
  const validActivity = finite(ratio) && ratio >= 0 && ratio <= 1 && count(activeDays);
  const filtered = records.filter(item => selected === 'all' || statusOf(item) === selected);
  const scores = records.filter(item => item.submitted_day != null && finite(item.score) && item.score >= 0 && item.score <= 100);

  if (group === 'activity') return <div className="mt-4 grid gap-4 lg:grid-cols-2">
    <Frame title="Nhịp tương tác gần mốc đánh giá" note="Hai khoảng không chồng lấn; so sánh lượt tương tác trung bình/ngày, không phải thời gian học.">
      {windows ? <div>
        <div className="flex h-44 items-end justify-around gap-4 border-b border-slate-600 px-3" role="img"
          aria-label={windows.map(item => `${item.label}: ${number(item.average)} lượt/ngày`).join('; ')}>
          {windows.map((item, index) => <div key={item.label} className="flex h-full w-1/2 max-w-36 flex-col justify-end text-center">
            <span className="mb-2 text-xs font-semibold tabular-nums text-white">{number(item.average)}</span>
            <div className={`mx-auto w-2/3 rounded-t-md ${index === 0 ? 'bg-sky-500' : 'bg-violet-400'}`}
              style={{ height: `${item.average / Math.max(...windows.map(window => window.average), 0.001) * 75}%` }} />
          </div>)}
        </div>
        <div className="mt-2 grid grid-cols-2 gap-4 text-center text-xs">{windows.map(item => <div key={item.label}>
          <p className="font-medium text-slate-200">{item.label}</p>
          <p className="mt-1 text-slate-400">{number(item.clicks)} lượt / {item.days} ngày</p>
        </div>)}</div>
        <p className="mt-3 text-xs text-slate-400">Đơn vị: lượt/ngày. Kết thúc tại ngày thứ {cutoff} của học phần; không phản ánh hoạt động hiện tại.</p>
      </div> : <Empty>Chưa đủ cửa sổ 30 ngày hoặc số liệu tương tác thiếu/không nhất quán.</Empty>}
    </Frame>
    <Frame title="Tỷ lệ ngày có hoạt động" note="Tỷ lệ trong khoảng quan sát của dữ liệu nguồn; không phải tỷ lệ chuyên cần hoặc mức hiểu bài.">
      {validActivity ? <div>
        <p className="text-3xl font-semibold tabular-nums text-white">{number(ratio * 100)}<span className="text-lg text-slate-400">%</span></p>
        <div className="mt-4 h-5 overflow-hidden rounded-full bg-slate-700" role="meter" aria-label="Tỷ lệ ngày có hoạt động" aria-valuemin={0} aria-valuemax={100} aria-valuenow={ratio * 100}>
          <div className="h-full rounded-full bg-sky-400" style={{ width: `${ratio * 100}%` }} />
        </div>
        <div className="mt-1 flex justify-between text-xs text-slate-400"><span>0%</span><span>100%</span></div>
        <p className="mt-4 text-xs text-slate-300">Ghi nhận hoạt động trong <strong>{number(activeDays)} ngày</strong>.</p>
        <p className="mt-2 text-xs text-slate-400">Không tự suy ra số ngày vắng học từ phần còn lại.</p>
      </div> : <Empty>Chưa có số ngày hoạt động và tỷ lệ hợp lệ.</Empty>}
    </Frame>
  </div>;

  return <div className="mt-4 space-y-4">
    <Frame title="Trạng thái nộp bài đến mốc đánh giá" note="Chỉ gồm các bài đến hạn được xác nhận. Chọn một nhóm để lọc danh sách; hạn riêng hoặc miễn bài cần đối chiếu thêm.">
      {validRecords ? <>
        <div className="flex h-9 overflow-hidden rounded-lg bg-slate-800" aria-label="Phân bố trạng thái nộp bài">
          {statuses.map(status => {
            const amount = records.filter(item => statusOf(item) === status.id).length;
            return amount > 0 && <button key={status.id} type="button" aria-pressed={selected === status.id}
              aria-label={`${status.label}: ${amount}/${records.length} bài, ${number(amount / records.length * 100)}%`}
              title={`${status.label}: ${amount} bài`} onClick={() => setSelected(selected === status.id ? 'all' : status.id)}
              className={`${status.color} min-w-0 text-xs font-bold text-slate-950 focus-visible:z-10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white`}
              style={{ width: `${amount / records.length * 100}%` }}><span className="sr-only">{amount} bài</span></button>;
          })}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" aria-pressed={selected === 'all'} onClick={() => setSelected('all')} className={`rounded-lg border px-3 py-2 text-xs ${selected === 'all' ? 'border-brand-400 text-white' : 'border-slate-600 text-slate-300'}`}>Tất cả ({records.length})</button>
          {statuses.map(status => {
            const amount = records.filter(item => statusOf(item) === status.id).length;
            return <button key={status.id} type="button" aria-pressed={selected === status.id} onClick={() => setSelected(status.id)}
              className={`rounded-lg border px-3 py-2 text-xs ${selected === status.id ? 'border-brand-400 text-white' : 'border-slate-600 text-slate-300'}`}>
              <span className={`mr-2 inline-block h-2 w-2 rounded-full ${status.color}`} />{status.label}: {amount} ({number(amount / records.length * 100)}%)
            </button>;
          })}
        </div>
        <ul className="mt-3 max-h-48 space-y-2 overflow-y-auto" aria-label="Bài đánh giá theo trạng thái" aria-live="polite">
          {filtered.map(item => <li key={item.id} className="flex flex-wrap justify-between gap-2 rounded-lg bg-slate-800/60 px-3 py-2 text-xs text-slate-300">
            <strong className="text-white">{label(item)}</strong><span>Hạn: ngày {item.due_day} · {item.submitted_day == null ? 'Chưa ghi nhận nộp' : `Nộp: ngày ${item.submitted_day}`}</span>
          </li>)}
          {!filtered.length && <li className="text-xs text-slate-400">Không có bài trong nhóm này.</li>}
        </ul>
      </> : <Empty>Chưa có danh sách bài đến hạn hợp lệ để phân loại; không suy ra số bài thiếu từ tỷ lệ tổng hợp.</Empty>}
    </Frame>
    <details className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-white">Dòng thời gian từng bài</summary>
      <p className="mt-2 text-xs leading-relaxed text-slate-400">● Hạn chung · ◆ Ngày nộp · đường nét đứt: mốc đánh giá. Ngày tính tương đối trong học phần.</p>
      {validRecords ? <div className="mt-4 overflow-x-auto">
        <svg viewBox={`0 0 640 ${55 + records.length * 38}`} className="w-full min-w-[520px]" role="img" aria-label="Hạn chung và ngày nộp từng bài đến mốc đánh giá">
          <title>Dòng thời gian bài đánh giá đến ngày {cutoff}</title>
          {(() => {
            const x = (day: number) => 145 + day / Math.max(cutoff, 1) * 445;
            return <>
              <line x1={x(cutoff)} x2={x(cutoff)} y1={27} y2={40 + records.length * 38} stroke="#a78bfa" strokeDasharray="4 4" />
              <text x={145} y={16} fill="#94a3b8" fontSize={11}>Ngày 0</text>
              <text x={590} y={16} fill="#c4b5fd" fontSize={11} textAnchor="end">Mốc đánh giá: {cutoff}</text>
              {records.map((item, index) => {
                const y = 43 + index * 38;
                return <g key={item.id}><title>{label(item)}: hạn ngày {item.due_day}; {item.submitted_day == null ? 'chưa ghi nhận nộp' : `nộp ngày ${item.submitted_day}`}</title>
                  <text x={0} y={y + 4} fill="#cbd5e1" fontSize={11}>{label(item)}</text>
                  <line x1={145} x2={590} y1={y} y2={y} stroke="#334155" />
                  {item.submitted_day != null && <line x1={x(item.due_day)} x2={x(item.submitted_day)} y1={y} y2={y} stroke={statusOf(item) === 'late' ? '#fbbf24' : '#38bdf8'} strokeWidth={3} />}
                  <circle cx={x(item.due_day)} cy={y} r={5} fill="#cbd5e1" />
                  {item.submitted_day != null && <path d={`M ${x(item.submitted_day)} ${y - 6} l 6 6 l -6 6 l -6 -6 Z`} fill={statusOf(item) === 'late' ? '#fbbf24' : '#38bdf8'} />}
                </g>;
              })}
            </>;
          })()}
        </svg>
      </div> : <div className="mt-3"><Empty>Chưa có mốc đánh giá hoặc dữ liệu từng bài hợp lệ.</Empty></div>}
    </details>
    <Frame title="Điểm ghi nhận theo bài" note="Thang điểm 0–100 của dữ liệu nguồn. Các bài có thể khác loại và trọng số; không suy ra chủ đề yếu hoặc điểm tổng kết.">
      {validRecords && scores.length > 0 ? <>
        <div className="flex justify-between text-xs text-slate-400"><span>Điểm / 100</span><span>{scores.length}/{records.length} bài có điểm hợp lệ</span></div>
        <ul className="mt-3 max-h-64 space-y-3 overflow-y-auto">{scores.map(item => <li key={item.id} className="grid grid-cols-[90px_minmax(0,1fr)_45px] items-center gap-3 text-xs">
          <span className="text-slate-300">{label(item)}</span>
          <div className="h-4 overflow-hidden rounded bg-slate-700" role="meter" aria-label={`Điểm ${label(item)}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={item.score!}>
            <div className="h-full rounded bg-violet-400" style={{ width: `${item.score}%` }} />
          </div><strong className="text-right tabular-nums text-white">{number(item.score!)}</strong>
        </li>)}</ul>
        <p className="mt-3 text-xs text-slate-400">Bài chưa có điểm được bỏ khỏi biểu đồ, không quy thành 0.</p>
      </> : <Empty>Chưa có điểm từng bài hợp lệ. Không thay bằng xác suất nguy cơ hoặc tỷ lệ nộp bài.</Empty>}
    </Frame>
  </div>;
};
