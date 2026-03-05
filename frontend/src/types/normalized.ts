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

export type SkillRadarNormalized = {
  pitch: number;
  rhythm: number;
  technique: number;
  consistency: number;
  progress: number;
  composite: number;
  techniqueSource: "radar" | "sessions" | "fallback";
  progressSource: "radar" | "analytics" | "fallback";
};

export type PracticeHistorySessionNormalized = {
  id: number | null;
  timestamp: string | null;
  noteAccuracy: number | null;
  compositeScore: number | null;
  pitchIndex: number | null;
  rhythmIndex: number | null;
  consistencyIndex: number | null;
  techniqueScore: number | null;
};

export type PracticeHistoryNormalized = {
  sessions: PracticeHistorySessionNormalized[];
  unlockDelta: number;
  unlockedContentCount: number;
};

export type PracticeResultNormalized = {
  contentType: string | null;
  song: string | null;
  phraseIndex: number | null;
  noteAccuracy: number | null;
  avgPitchErrorCents: number | null;
  avgTimingErrorSec: number | null;
  techniqueScore: number | null;
  adaptivePlanSummary: string | null;
  recommendedTempo: number | null;
  songRecommendedTempo: number | null;
  focusArea: string | null;
  focusPhrase: number | null;
  targetDrill: string | null;
  exerciseMode: string | null;
  variationStrategy: string | null;
  tempoFeedback: string | null;
  songRecommendation: string | null;
  unlockEvent: boolean;
  rawFeedback: unknown;
  curriculum: StudentCurriculumNormalized | null;
  detectedNotes: Array<{
    note: string;
    cents: number;
    time: number;
  }>;
  referenceNotes: Array<{
    note: string;
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
