export interface StudentFeatures {
  code_module: string;
  gender: string;
  highest_education: string;
  age_band: string;
  studied_credits: number;
  date_registration: number;
  total_clicks_to_t: number;
  clicks_resource_to_t: number;
  clicks_url_to_t: number;
  active_days_to_t: number;
  active_day_ratio: number;
  days_since_last_activity: number;
  clicks_recent_7: number;
  clicks_recent_30: number;
  assessments_submitted_to_t: number;
  late_submissions_to_t: number;
  submission_rate: number;
}

export interface PredictionRequest {
  features: StudentFeatures;
}

export interface PredictionResponse {
  prediction: number;
  confidence: number;
  provenance?: PredictionProvenance | null;
}

export interface PredictionProvenance {
  features: StudentFeatures;
  model_version: string;
  threshold: number;
  model_sha256: string;
  model_id?: string | null;
  cutoff_fraction?: number | null;
  positive_label?: 1 | null;
}

export interface InterventionStrategy {
  id: string;
  category: 'chuyen_can' | 'hoc_thuat' | 'tien_do' | 'tam_ly';
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  targetMetric?: string;
}

export interface PredictionHistoryItem {
  id: string;
  time: string;
  date: string;
  module: string;
  age: string;
  credits: number;
  clicks: number;
  prediction: number;
  confidence: number;
  features: StudentFeatures;
  provenance?: PredictionProvenance | null;
}

export type RoleCode = 'ADMIN' | 'ADVISOR' | 'LECTURER' | 'STUDENT';

export interface UserProfile {
  name: string;
  email: string;
  role: string;
  roleCode?: RoleCode;
  initials: string;
  department?: string;
  phone?: string;
  organization?: string;
  avatarUrl?: string;
  studentCode?: string;
  lecturerCode?: string;
  academicRank?: string;
  officeLocation?: string;
}

export type FeatureGroup = 'info' | 'activity' | 'assessment';

export interface FeatureFieldDefinition {
  key: keyof StudentFeatures;
  group: FeatureGroup;
  label: string;
  hint: string;
  type: 'select' | 'number';
  options?: string[];
  default: string | number;
  step?: number;
  min?: number;
  max?: number;
}
