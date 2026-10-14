import { StudentFeatures } from './student';

export interface ActionableTargetItem {
  feature: keyof StudentFeatures | string;
  label: string;
  current_value: number | string;
  target_value: number | string;
  delta: number;
  unit: string;
  importance_rank: number;
  pedagogical_rationale: string;
}

export interface SRLPhase {
  phase: 'forethought' | 'performance' | 'reflection';
  phase_name: string;
  timeframe: string;
  objective: string;
  action_items: string[];
  stakeholder: 'student' | 'advisor' | 'collaborative';
}

export interface RecourseScenario {
  id: 'quick_win' | 'sustainable';
  title: string;
  badge: string;
  target_probability: number;
  probability_reduction: number;
  features: StudentFeatures;
  targets: ActionableTargetItem[];
  srl_plan: SRLPhase[];
  summary: string;
}

export interface TheoreticalFoundations {
  frameworks: string[];
  citations: string[];
  limitations: string[];
}

export interface ActionableRecourseResponse {
  status: 'available' | 'not_at_risk' | 'no_feasible_recourse';
  message: string;
  current_probability: number;
  threshold: number;
  scenarios: RecourseScenario[];
  theoretical_foundations: TheoreticalFoundations;
}
