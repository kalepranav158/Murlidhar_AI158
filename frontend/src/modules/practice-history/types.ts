export type PracticeHistoryEventKind = "improvement" | "plateau" | "unlock";

export type PracticeHistoryBadge = {
  kind: PracticeHistoryEventKind;
  label: string;
};

export type PracticeHistoryTimelineRow = {
  key: string;
  sessionId: number | null;
  sequence: number;
  timestampLabel: string;
  noteAccuracyLabel: string;
  compositeLabel: string;
  techniqueLabel: string;
  deltaLabel: string;
  badges: PracticeHistoryBadge[];
};

export type PracticeHistoryTimelineModel = {
  rows: PracticeHistoryTimelineRow[];
  sessionsShown: number;
  latestCompositeLabel: string;
  trendLabel: string;
  unlockEvents: number;
};
