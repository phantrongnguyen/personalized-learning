import { StudentFeatures } from './student';

export interface HistoricalSnapshot {
  fraction: number;
  day: number;
  recent_active_days: number;
  recent_clicks: number;
  due_assessments: number;
  due_assessments_submitted: number;
  due_submission_rate: number | null;
}

export interface HistoricalCase {
  case_id: string;
  module: string;
  presentation: string;
  risk_probability: number;
  final_result: 'Pass' | 'Distinction';
  distance: number;
  matching_features: {
    feature: keyof StudentFeatures;
    current_value: number;
    historical_value: number;
    current_contribution: number;
    historical_contribution: number;
  }[];
  snapshots: HistoricalSnapshot[];
}

export interface HistoricalCasesResponse {
  status: 'available' | 'unavailable' | 'no_matches' | 'no_recoveries' | 'not_at_risk';
  message: string;
  source: string;
  cutoff_fraction: number;
  threshold: number | null;
  current_probability: number | null;
  reference_count: number;
  eligible_count: number;
  neighborhood_count: number;
  successful_count: number;
  unsuccessful_count: number;
  risk_drivers: (keyof StudentFeatures)[];
  cases: HistoricalCase[];
  limitations: string[];
}
