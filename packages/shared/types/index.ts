export * from './student';

// -------------------------------------------------------------
// AUTH & USER INTERFACES
// -------------------------------------------------------------
export interface AuthRole {
  id: number;
  code: 'ADMIN' | 'ADVISOR' | 'LECTURER' | 'STUDENT';
  name: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface BackendUser {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string | null;
  phone_number?: string | null;
  is_active: boolean;
  roles: AuthRole[];
  student_profile?: {
    id: string;
    student_code: string;
    gender: string;
    highest_education: string;
    age_band: string;
    imd_band?: string | null;
    region?: string | null;
    disability: string;
  } | null;
  advisor_profile?: {
    id: string;
    department: string;
    office_location?: string | null;
  } | null;
  lecturer_profile?: {
    id: string;
    lecturer_code: string;
    department: string;
    academic_rank: string;
  } | null;
  created_at: string;
}

// -------------------------------------------------------------
// ADVISOR INTERFACES
// -------------------------------------------------------------
export interface AdvisorClassSummary {
  class_name: string;
  academic_year: string;
  total_students: number;
  high_risk_count: number;
  safe_count: number;
}

export interface AdvisorStudentItem {
  student_id: string;
  student_code: string;
  full_name: string;
  gender: string;
  class_name: string;
  risk_probability: number;
  risk_level: 'SAFE' | 'HIGH_RISK';
  has_active_plan: boolean;
  uncompleted_tasks_count: number;
}

export interface CreateInterventionTaskPayload {
  category: 'CHUYEN_CAN' | 'HOC_THUAT' | 'TIEN_DO' | 'TAM_LY';
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  target_metric: string;
}

export interface CreateInterventionPlanPayload {
  student_id: string;
  target_completion_date?: string;
  advisor_note_summary?: string;
  tasks: CreateInterventionTaskPayload[];
}

// -------------------------------------------------------------
// LECTURER INTERFACES
// -------------------------------------------------------------
export interface LecturerCourseItem {
  presentation_id: string;
  code_module: string;
  course_name: string;
  code_presentation: string;
  module_length: number;
  role_in_course: string;
  total_students: number;
}

export interface CourseStudentRiskItem {
  student_id: string;
  student_code: string;
  full_name: string;
  enrollment_id: string;
  total_clicks: number;
  late_submissions: number;
  submission_rate: number;
  risk_probability: number;
  risk_status: 'SAFE' | 'HIGH_RISK';
}

// -------------------------------------------------------------
// STUDENT INTERFACES
// -------------------------------------------------------------
export interface StudentCourseItem {
  enrollment_id: string;
  code_module: string;
  course_name: string;
  code_presentation: string;
  studied_credits: number;
  final_result?: string | null;
}

export interface StudentRiskPrediction {
  enrollment_id: string;
  code_module: string;
  cutoff_stage: string;
  risk_probability: number;
  risk_level: 'SAFE' | 'HIGH_RISK';
  model_version: string;
  predicted_at: string;
  pedagogical_recommendations: string[];
}

export interface RadarDimensionItem {
  metric: string;
  student_value: number;
  benchmark_value: number;
  percentile: number;
}

export interface StudentRadarData {
  enrollment_id: string;
  code_module: string;
  dimensions: RadarDimensionItem[];
}

export interface StudentTaskItem {
  id: string;
  plan_id: string;
  category: string;
  priority: string;
  title: string;
  description: string;
  target_metric: string;
  is_completed: boolean;
  completed_at?: string | null;
  student_feedback?: string | null;
}

export interface StudentHelpRequestItem {
  id: string;
  target_role: string;
  subject: string;
  content: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'RESOLVED';
  response_note?: string | null;
  created_at: string;
  updated_at: string;
}
