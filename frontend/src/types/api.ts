export type MessagePayload = {
  status?: "no_data" | "error";
  message: string;
  error?: string;
  data?: unknown;
};

export type StudentProfileApi = {
  current_level?: string;
  unlocked_content?: string[];
  mastered_content?: string[];
  recommended_content?: string | null;
  composite_score?: number | null;
  reason?: string | null;
};

export type StudentCurriculumApi = {
  current_level?: string;
  unlocked_content?: string[];
  mastered_content?: string[];
  skill_snapshot?: {
    accuracy?: number;
    rhythm_index?: number;
    technique_score?: number;
    composite_score?: number;
  };
  recommended_content?: string | null;
  reason?: string | null;
  locked?: string[];
  next_goal?: string | null;
};

export type StudentAnalyticsApi = {
  summary?: {
    average_accuracy?: number;
    average_pitch_error?: number;
    average_timing_error?: number;
    best_accuracy?: number;
    worst_accuracy?: number;
  };
  trend?: {
    slope?: number;
    classification?: string;
  };
  indices?: {
    pitch_index?: number;
    rhythm_index?: number;
    consistency_index?: number;
    composite_score?: number;
  };
  prediction?: {
    next_accuracy?: number;
  };
  flags?: {
    plateau?: boolean;
    risk?: boolean;
  };
  volatility?: number;
};

export type AnalyticsSummaryApi = {
  total_sessions?: number;
  average_note_accuracy?: number;
  average_pitch_error?: number;
  average_timing_error?: number;
  best_note_accuracy?: number;
  worst_note_accuracy?: number;
};

export type AnalyticsTrendApi = {
  accuracy_series?: Array<{
    session: number;
    accuracy: number;
  }>;
};

export type AnalyticsRadarApi = {
  pitch?: number;
  rhythm?: number;
  consistency?: number;
  composite?: number;
  technique?: number;
  progress?: number;
};

export type AnalyticsSkillLevelApi = {
  skill_level?: string;
  average_note_accuracy?: number;
  average_pitch_error?: number;
  average_timing_error?: number;
};

export type AnalyticsConsistencyApi = {
  accuracy_standard_deviation?: number;
  consistency_level?: string;
};

export type AnalyticsPitchStabilityApi = {
  average_pitch_error?: number;
  mean_pitch_error?: number;
  pitch_variation?: number;
  pitch_control_level?: string;
};

export type AnalyticsRecommendationApi = {
  recommended_tempo_adjustment?: string;
  practice_focus?: string;
  suggestion?: string;
};

export type AnalyticsConsistencyDetailsApi = {
  accuracy_variation?: number;
  pitch_variation?: number;
  timing_variation?: number;
  primary_instability_source?: string;
};

export type AnalyticsWeakestPhraseApi = {
  phrase_id?: number;
  avg_accuracy?: number;
  attempts?: number;
};

export type LearningDifficultyApi = {
  difficulty_level?: string;
  recommended_content_type?: string;
  weakest_dimension?: string;
  composite_score?: number;
  confidence?: string;
  total_sessions_analyzed?: number;
};

export type LearningRecommendationApi = {
  predicted_next_accuracy?: number;
  recommended_tempo_adjustment?: string;
  practice_focus?: string;
  recommendation?: string;
  recommended_content_type?: string;
  difficulty_level?: string;
  model_source?: string;
};

export type LearningModelStatusApi = {
  loaded?: boolean;
  source?: string;
  artifact_path?: string;
  trained_at?: string;
  sample_pairs?: number;
  mae?: number | null;
  reason?: string;
};

export type StudentStreakApi = {
  user_id?: string;
  current_streak?: number;
  longest_streak?: number;
  total_practice_days?: number;
  last_practice_logical_date?: string | null;
  last_practice_date?: string | null;
};

export type SessionsApi = {
  count?: number;
  sessions?: Array<{
    id?: number;
    timestamp?: string;
    note_accuracy?: number;
    avg_pitch_error?: number;
    avg_timing_error?: number;
    composite_score?: number;
    pitch_index?: number;
    rhythm_index?: number;
    consistency_index?: number;
    technique_score?: number;
  }>;
};

export type SongListItemApi = {
  song_id: string;
  title?: string;
  tempo?: number | null;
  phrases?: number;
  content_type?: "alankar" | "song" | "melody" | string;
};

export type SongPhraseReferenceApi = {
  song_id?: string;
  title?: string;
  content_type?: "alankar" | "song" | "melody" | string;
  phrase_index?: number;
  phrase_id?: number;
  phrase_section?: string | null;
  phrase_count?: number;
  reference_tempo?: number | null;
  notes?: Array<{
    note?: string;
    time?: number;
  }>;
};

export type PracticeApi = {
  content_type?: "alankar" | "song" | "melody" | string;
  song?: string;
  phrase_index?: number;
  dtw_cost?: number;
  full_song_unlocked?: boolean;
  evaluation?: {
    note_accuracy?: number;
    avg_pitch_error_cents?: number | null;
    avg_timing_error_sec?: number | null;
    mistakes?: unknown[];
    feedback?: unknown;
  };
  adaptive_plan?: Record<string, unknown>;
  song_adaptive_plan?: Record<string, unknown>;
  techniques?: Record<string, unknown>;
  technique_score?: number | null;
  technique_details?: Record<string, unknown>;
  curriculum?: StudentCurriculumApi;
  played_notes?: Array<{
    note?: string;
    cents?: number;
    time?: number;
  }>;
  detected_notes?: Array<{
    note?: string;
    cents?: number;
    time?: number;
  }>;
  reference_notes?: Array<{
    note?: string;
    time?: number;
  }>;
  alignment_debug?: {
    dtw_transposition_shift_semitones?: number;
  };
};

export type AskRequestApi = {
  question: string;
};

export type AskResponseApi = {
  mode?: string;
  description?: string;
  confidence_score?: number;
  [key: string]: unknown;
};

export type DebugSessionsApi = {
  user_id?: string;
  total_returned?: number;
  sessions?: Array<Record<string, unknown>>;
  timestamp?: string;
};

export type RootHealthApi = {
  message?: string;
};
