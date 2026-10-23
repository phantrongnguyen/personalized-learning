import reference from './constants/radar-reference.json';
import type { StudentFeatures } from './types';

type RadarDimensionItem = { metric: string; student_value: number | null; benchmark_value: number; reference_score: number | null; unit: string };

export const RADAR_REFERENCE = reference;

/** Display-only score capped at 100. Missing/invalid data stays unknown. */
export function calculateRadar(features: Partial<StudentFeatures>): RadarDimensionItem[] {
  const validNumber = (value: unknown): value is number =>
    typeof value === 'number' && Number.isFinite(value) && value >= 0;
  return reference.dimensions.map(spec => {
    const key = spec.key as keyof StudentFeatures;
    const raw = features[key];
    let value: number | null = validNumber(raw) ? raw : null;
    if ((key === 'active_day_ratio' || key === 'submission_rate') && value !== null && value > 1) value = null;
    if (key === 'late_submissions_to_t') {
      const submitted = features.assessments_submitted_to_t;
      value = value !== null && validNumber(submitted) && submitted > 0 && value <= submitted
        ? Math.max(0, 1 - value * reference.late_submission_penalty) * 100 : null;
    }
    return {
      metric: spec.metric, student_value: value, benchmark_value: spec.reference, unit: spec.unit,
      reference_score: value === null ? null : Math.round(Math.min(100, Math.max(0, value / spec.reference * 100)) * 10) / 10,
    };
  });
}

/** Illustrative display threshold only; never a model risk classification. */
export const RADAR_LOW_SCORE = 25;
export const RADAR_COLOR_NOTE = 'Đỏ: có chỉ số dưới 25% mốc minh họa; ngưỡng hiển thị, không phải phân loại rủi ro.';
export function radarAppearance(scores: (number | null)[]) {
  const known = scores.filter((score): score is number => score !== null && Number.isFinite(score) && score >= 0);
  const low = known.some(score => score < RADAR_LOW_SCORE);
  return low
    ? { stroke: '#f87171', fill: 'rgba(248,113,113,0.22)', text: 'text-red-400', svgText: 'fill-red-400', bar: 'bg-red-400', low }
    : { stroke: '#22d3ee', fill: 'rgba(34,211,238,0.2)', text: 'text-cyan-400', svgText: 'fill-cyan-400', bar: 'bg-cyan-400', low };
}
