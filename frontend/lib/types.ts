export interface PersonaInfo {
  persona_id: string;
  name: string;
  role: string;
}

export interface Scenario {
  scenario_id: string;
  background: string;
  task_message: string;
  personas: PersonaInfo[];
  assets: { cs_logs_csv: string; dashboard_md: string };
  brief_template: string;
}

export interface SessionView {
  session_id: string;
  scenario_id: string;
  state: string;
  submissions: number;
  revisions_used: number;
  completed: boolean;
  passed: boolean;
  rejections: string[];
}

export interface CriterionScore {
  id: string;
  score: number;
  evidence: string;
}

export interface Evaluation {
  weighted_total: number;
  passed: boolean;
  scores: CriterionScore[];
  overall_comment: string;
}

export interface SubmitResult {
  state: string;
  rejection: string | null;
  evaluation: Evaluation;
}

export interface StarAnswer {
  question: string;
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface AnticipatedQuestion {
  question: string;
  suggested_angle: string;
}

export interface Weapons {
  document_artifact: string;
  star_arsenal: {
    star_answers: StarAnswer[];
    anticipated_questions: AnticipatedQuestion[];
  };
  process_record: string;
}
