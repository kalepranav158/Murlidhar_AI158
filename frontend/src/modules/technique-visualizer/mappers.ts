import type { PracticeResultNormalized } from "../../types/normalized";
import type {
  TechniqueKind,
  TechniqueTransitionRow,
  TechniqueVisualizerModel,
} from "./types";

const asRecord = (value: unknown): Record<string, unknown> | null => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
};

const asObjectArray = (value: unknown): Array<Record<string, unknown>> => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map(asRecord)
    .filter((entry): entry is Record<string, unknown> => entry !== null);
};

const asNumber = (value: unknown): number | null => {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
};

const asString = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

const asScore = (value: unknown): number | null => {
  const parsed = asNumber(value);
  if (parsed === null) {
    return null;
  }

  if (parsed < 0) {
    return 0;
  }

  if (parsed > 1) {
    return 1;
  }

  return parsed;
};

const normalizeTimeRange = (
  startRaw: unknown,
  endRaw: unknown,
): { start: number | null; end: number | null } => {
  const start = asNumber(startRaw);
  const end = asNumber(endRaw);

  if (start === null && end === null) {
    return { start: null, end: null };
  }

  const fallback = start ?? end ?? 0;
  const normalizedStart = Math.min(start ?? fallback, end ?? fallback);
  const normalizedEnd = Math.max(start ?? fallback, end ?? fallback);

  return {
    start: normalizedStart,
    end: normalizedEnd,
  };
};

const numericKey = (value: number | null): string => {
  return value === null ? "na" : value.toFixed(2);
};

const resolveTechniqueKind = (
  transition: Record<string, unknown> | null,
  meend: Record<string, unknown> | null,
  gamak: Record<string, unknown> | null,
): TechniqueKind => {
  if (meend) {
    return "meend";
  }

  if (gamak) {
    return "gamak";
  }

  const transitionTechnique = asString(transition?.technique)?.toLowerCase();
  if (transitionTechnique === "meend" || transitionTechnique === "gamak") {
    return transitionTechnique;
  }

  return "unknown";
};

const buildTransitionSignature = (
  transition: Record<string, unknown> | null,
  technique: TechniqueKind,
): string => {
  const from = asString(transition?.from) ?? "na";
  const to = asString(transition?.to) ?? "na";
  const range = normalizeTimeRange(transition?.from_time, transition?.to_time);

  return [
    technique,
    from,
    to,
    numericKey(range.start),
    numericKey(range.end),
  ].join("|");
};

const buildTransitionLabel = (
  transition: Record<string, unknown> | null,
  technique: TechniqueKind,
  fallbackIndex: number,
): string => {
  const from = asString(transition?.from);
  const to = asString(transition?.to);

  if (from && to) {
    if (technique === "unknown") {
      return `${from} → ${to}`;
    }

    return `${from} → ${to} (${technique})`;
  }

  if (technique !== "unknown") {
    return `${technique} transition ${fallbackIndex + 1}`;
  }

  return `Transition ${fallbackIndex + 1}`;
};

const buildObservedSummary = (
  meend: Record<string, unknown> | null,
  gamak: Record<string, unknown> | null,
): string => {
  if (meend) {
    const direction = asString(meend.direction) ?? "unknown";
    const cents = asNumber(meend.cents_change);
    if (cents !== null) {
      return `${direction}, ${Math.abs(cents).toFixed(0)} cents`;
    }

    return direction;
  }

  if (gamak) {
    const oscillations = asNumber(gamak.oscillations);
    const amplitude = asNumber(gamak.amplitude_cents);

    if (oscillations !== null && amplitude !== null) {
      return `${Math.round(oscillations)} osc, ${Math.round(amplitude)} cents`;
    }

    if (oscillations !== null) {
      return `${Math.round(oscillations)} oscillations`;
    }

    return "Detected";
  }

  return "Not detected";
};

const mapFoundTransitionRows = (
  foundTransitions: Array<Record<string, unknown>>,
): {
  rows: TechniqueTransitionRow[];
  signatures: Set<string>;
} => {
  const signatures = new Set<string>();

  const rows = foundTransitions.map((entry, index) => {
    const transition = asRecord(entry.transition);
    const meend = asRecord(entry.meend);
    const gamak = asRecord(entry.gamak);
    const technique = resolveTechniqueKind(transition, meend, gamak);

    const expectedRange = normalizeTimeRange(transition?.from_time, transition?.to_time);
    const observedRange = normalizeTimeRange(
      meend?.start_time ?? gamak?.start_time,
      meend?.end_time ?? gamak?.end_time,
    );

    const signature = buildTransitionSignature(transition, technique);
    signatures.add(signature);

    return {
      key: `found-${index}-${signature}`,
      label: buildTransitionLabel(transition, technique, index),
      technique,
      expectedStart: expectedRange.start,
      expectedEnd: expectedRange.end,
      observedStart: observedRange.start,
      observedEnd: observedRange.end,
      observedSummary: buildObservedSummary(meend, gamak),
      positionScore: asScore(entry.position_score),
      directionScore: asScore(entry.direction_score),
      strengthScore: asScore(entry.strength_score),
      clarityScore: asScore(entry.clarity_score),
      compositeScore: asScore(entry.composite_score),
      matched: true,
    } as TechniqueTransitionRow;
  });

  return {
    rows,
    signatures,
  };
};

const mapMissingExpectedRows = (
  expectedTransitions: Array<Record<string, unknown>>,
  matchedSignatures: Set<string>,
): TechniqueTransitionRow[] => {
  return expectedTransitions
    .map((transition, index) => {
      const technique = resolveTechniqueKind(transition, null, null);
      const signature = buildTransitionSignature(transition, technique);

      if (matchedSignatures.has(signature)) {
        return null;
      }

      const expectedRange = normalizeTimeRange(transition.from_time, transition.to_time);

      return {
        key: `expected-${index}-${signature}`,
        label: buildTransitionLabel(transition, technique, index),
        technique,
        expectedStart: expectedRange.start,
        expectedEnd: expectedRange.end,
        observedStart: null,
        observedEnd: null,
        observedSummary: "Not detected",
        positionScore: null,
        directionScore: null,
        strengthScore: null,
        clarityScore: null,
        compositeScore: null,
        matched: false,
      } as TechniqueTransitionRow;
    })
    .filter((entry): entry is TechniqueTransitionRow => entry !== null);
};

export const mapPracticeToTechniqueVisualizer = (
  practice: PracticeResultNormalized,
): TechniqueVisualizerModel | null => {
  const details = asRecord(practice.techniqueDetails);
  const expectedTransitions = asObjectArray(details?.expected_transitions);
  const foundTransitions = asObjectArray(details?.found_transitions);

  const detectedMeend = asObjectArray(practice.techniques?.meend).length;
  const detectedGamak = asObjectArray(practice.techniques?.gamak).length;

  if (
    expectedTransitions.length === 0 &&
    foundTransitions.length === 0 &&
    detectedMeend === 0 &&
    detectedGamak === 0
  ) {
    return null;
  }

  const found = mapFoundTransitionRows(foundTransitions);
  const missingExpected = mapMissingExpectedRows(expectedTransitions, found.signatures);

  const rows = [...found.rows, ...missingExpected].sort((left, right) => {
    const leftStart = left.expectedStart ?? left.observedStart ?? Number.MAX_SAFE_INTEGER;
    const rightStart = right.expectedStart ?? right.observedStart ?? Number.MAX_SAFE_INTEGER;

    if (leftStart !== rightStart) {
      return leftStart - rightStart;
    }

    return left.label.localeCompare(right.label);
  });

  const matchedTransitions = rows.filter((row) => row.matched).length;

  const times = rows
    .flatMap((row) => [row.expectedStart, row.expectedEnd, row.observedStart, row.observedEnd])
    .filter((value): value is number => value !== null && Number.isFinite(value));

  const rawTimeMin = times.length > 0 ? Math.min(...times) : 0;
  const rawTimeMax = times.length > 0 ? Math.max(...times) : 1;

  const timeMin = Math.min(0, rawTimeMin);
  const timeMax = rawTimeMax > timeMin ? rawTimeMax : timeMin + 1;

  return {
    rows,
    timeMin,
    timeMax,
    detectedMeend,
    detectedGamak,
    expectedTransitions: expectedTransitions.length,
    matchedTransitions,
  };
};
