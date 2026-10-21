import reference from './constants/radar-reference.json';
import type { RadarDimensionItem, StudentFeatures } from './types';

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
