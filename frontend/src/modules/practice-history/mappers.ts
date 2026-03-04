import type {
  PracticeHistoryNormalized,
  PracticeHistorySessionNormalized,
} from "../../types/normalized";

type PracticeHistoryBadge = {
  kind: "improvement" | "plateau" | "unlock";
  label: string;
};

type PracticeHistoryTimelineRow = {
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

type PracticeHistoryTimelineModel = {
  rows: PracticeHistoryTimelineRow[];
  sessionsShown: number;
  latestCompositeLabel: string;
  trendLabel: string;
  unlockEvents: number;
};

const toUnitRange = (value: number | null): number | null => {
  if (value === null || !Number.isFinite(value)) {
    return null;
  }

  if (value <= 1) {
    return Math.max(0, value);
  }

  if (value <= 100) {
    return value / 100;
  }

  return 1;
};

const asPercentLabel = (value: number | null): string => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  if (value <= 1) {
    return `${(value * 100).toFixed(1)}%`;
  }

  return `${value.toFixed(1)}%`;
};

const asScoreLabel = (value: number | null): string => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  if (value <= 1) {
    return (value * 100).toFixed(1);
  }

  return value.toFixed(1);
};

const asDeltaLabel = (delta: number | null): string => {
  if (delta === null || !Number.isFinite(delta)) {
    return "N/A";
  }

  const sign = delta >= 0 ? "+" : "";
  return `${sign}${(delta * 100).toFixed(1)} pp`;
};

const formatTimestamp = (timestamp: string | null): string => {
  if (!timestamp) {
    return "Unknown time";
  }

  const parsed = Date.parse(timestamp);
  if (!Number.isFinite(parsed)) {
    return timestamp;
  }

  return new Date(parsed).toLocaleString();
};

const getPlateauIndexes = (sessions: PracticeHistorySessionNormalized[]): Set<number> => {
  const indexes = new Set<number>();

  for (let index = 2; index < sessions.length; index += 1) {
    const window = [
      toUnitRange(sessions[index - 2].compositeScore),
      toUnitRange(sessions[index - 1].compositeScore),
      toUnitRange(sessions[index].compositeScore),
    ];

    if (window.some((value) => value === null)) {
      continue;
    }

    const values = window as number[];
    const span = Math.max(...values) - Math.min(...values);
    if (span <= 0.015) {
      indexes.add(index);
    }
  }

  return indexes;
};

const getUnlockIndexes = (
  sessionsLength: number,
  unlockDelta: number,
): Set<number> => {
  const indexes = new Set<number>();
  const cappedUnlocks = Math.min(sessionsLength, Math.max(0, unlockDelta));

  for (let offset = 0; offset < cappedUnlocks; offset += 1) {
    indexes.add(sessionsLength - 1 - offset);
  }

  return indexes;
};

const getTrendLabel = (sessions: PracticeHistorySessionNormalized[]): string => {
  const values = sessions
    .map((session) => toUnitRange(session.compositeScore))
    .filter((value): value is number => value !== null);

  if (values.length === 0) {
    return "N/A";
  }

  if (values.length === 1) {
    return "Stable";
  }

  const delta = values[values.length - 1] - values[0];
  if (delta >= 0.02) {
    return "Improving";
  }

  if (delta <= -0.02) {
    return "Declining";
  }

  return "Stable";
};

const mapHistoryRow = (
  session: PracticeHistorySessionNormalized,
  index: number,
  sessions: PracticeHistorySessionNormalized[],
  plateauIndexes: Set<number>,
  unlockIndexes: Set<number>,
): PracticeHistoryTimelineRow => {
  const currentComposite = toUnitRange(session.compositeScore);
  const previousComposite =
    index > 0 ? toUnitRange(sessions[index - 1].compositeScore) : null;
  const delta =
    currentComposite !== null && previousComposite !== null
      ? currentComposite - previousComposite
      : null;

  const badges: PracticeHistoryBadge[] = [];

  if (delta !== null && delta >= 0.02) {
    badges.push({ kind: "improvement", label: "Improvement" });
  }

  if (plateauIndexes.has(index)) {
    badges.push({ kind: "plateau", label: "Plateau" });
  }

  if (unlockIndexes.has(index)) {
    badges.push({ kind: "unlock", label: "Unlock" });
  }

  return {
    key: session.id !== null ? `session-${session.id}` : `session-${index}-${session.timestamp ?? "na"}`,
    sessionId: session.id,
    sequence: index + 1,
    timestampLabel: formatTimestamp(session.timestamp),
    noteAccuracyLabel: asPercentLabel(session.noteAccuracy),
    compositeLabel: asScoreLabel(session.compositeScore),
    techniqueLabel: asScoreLabel(session.techniqueScore),
    deltaLabel: asDeltaLabel(delta),
    badges,
  };
};

export const mapPracticeHistoryToTimeline = (
  history: PracticeHistoryNormalized,
): PracticeHistoryTimelineModel => {
  const sessions = history.sessions;
  const plateauIndexes = getPlateauIndexes(sessions);
  const unlockIndexes = getUnlockIndexes(sessions.length, history.unlockDelta);

  const rows = sessions.map((session, index) =>
    mapHistoryRow(session, index, sessions, plateauIndexes, unlockIndexes),
  );

  const latestComposite =
    sessions.length > 0
      ? asScoreLabel(sessions[sessions.length - 1].compositeScore)
      : "N/A";

  return {
    rows,
    sessionsShown: rows.length,
    latestCompositeLabel: latestComposite,
    trendLabel: getTrendLabel(sessions),
    unlockEvents: Math.min(sessions.length, Math.max(0, history.unlockDelta)),
  };
};
