export type StudentProfileNormalized = {
  currentLevel: string;
  unlockedContent: string[];
  masteredContent: string[];
  recommendedContent: string | null;
  compositeScore: number | null;
  reason: string | null;
};

export type StudentCurriculumNormalized = {
  currentLevel: string;
  unlockedContent: string[];
  masteredContent: string[];
  lockedContent: string[];
  recommendedContent: string | null;
  reason: string | null;
  nextGoal: string | null;
  compositeScore: number | null;
};

export type StudentStreakNormalized = {
  currentStreak: number;
  longestStreak: number;
  totalPracticeDays: number;
  lastPracticeDate: string | null;
};

export type AnalyticsSnapshotNormalized = {
  compositeTrend: number[];
  slope: number | null;
  consistencyIndex: number | null;
  compositeScore: number | null;
  streakCurrent: number | null;
  streakLongest: number | null;
  trendLabel: string | null;
  plateau: boolean;
  risk: boolean;
};

export type PracticeResultNormalized = {
  song: string | null;
  phraseIndex: number | null;
  noteAccuracy: number | null;
  avgPitchErrorCents: number | null;
  avgTimingErrorSec: number | null;
  techniqueScore: number | null;
  adaptivePlanSummary: string | null;
  unlockEvent: boolean;
  rawFeedback: unknown;
  curriculum: StudentCurriculumNormalized | null;
  detectedNotes: Array<{
    note: string;
    cents: number;
    time: number;
  }>;
  alignmentDebug: {
    dtwTranspositionShiftSemitones: number | null;
  } | null;
  techniques: Record<string, unknown> | null;
  techniqueDetails: Record<string, unknown> | null;
};

export type EmptyState = {
  isEmpty: boolean;
  message: string | null;
};

export type ApiResult<T> = {
  data: T;
  empty: EmptyState;
};
