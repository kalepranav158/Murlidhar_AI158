import type {
  AnalyticsRecommendationApi,
  MessagePayload,
} from "../../types/api";
import type { PracticeResultNormalized } from "../../types/normalized";
import type {
  AdaptiveCoachDrillCard,
  AdaptiveCoachRecommendation,
} from "./types";

const asRecord = (value: unknown): Record<string, unknown> | null => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
};

const asText = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

const addCard = (
  cards: AdaptiveCoachDrillCard[],
  title: string,
  value: string | null,
  detail: string | null,
) => {
  if (!value) {
    return;
  }

  cards.push({
    title,
    value,
    detail,
  });
};

export const mapPracticeToCoachDrillCards = (
  practice: PracticeResultNormalized,
): AdaptiveCoachDrillCard[] => {
  const cards: AdaptiveCoachDrillCard[] = [];
  const feedback = asRecord(practice.rawFeedback);
  const feedbackTechnicalAssessment = asText(feedback?.technical_assessment);
  const feedbackCorrectiveGuidance = asText(feedback?.corrective_guidance);
  const feedbackTempoRecommendation = asText(feedback?.tempo_adjustment_recommendation);

  addCard(
    cards,
    "Phrase Focus",
    practice.focusPhrase !== null ? `Phrase ${practice.focusPhrase}` : null,
    practice.songRecommendation,
  );

  addCard(
    cards,
    "Tempo Target",
    practice.recommendedTempo !== null ? `${practice.recommendedTempo} BPM` : null,
    practice.tempoFeedback ?? feedbackTempoRecommendation,
  );

  addCard(
    cards,
    "Practice Drill",
    practice.targetDrill,
    practice.exerciseMode,
  );

  addCard(
    cards,
    "Repeat Guidance",
    practice.variationStrategy,
    null,
  );

  addCard(
    cards,
    "Focus Instruction",
    practice.focusArea ?? feedbackCorrectiveGuidance,
    practice.adaptivePlanSummary ?? feedbackTechnicalAssessment,
  );

  addCard(
    cards,
    "Corrective Guidance",
    feedbackCorrectiveGuidance,
    null,
  );

  return cards;
};

const addNextStep = (steps: string[], value: string | null) => {
  if (!value) {
    return;
  }

  const normalized = value.trim();
  if (!normalized) {
    return;
  }

  const duplicate = steps.some((entry) => entry.toLowerCase() === normalized.toLowerCase());
  if (!duplicate) {
    steps.push(normalized);
  }
};

export const mapPracticeToNextSteps = (
  practice: PracticeResultNormalized,
  recommendation: AdaptiveCoachRecommendation | null,
): string[] => {
  const steps: string[] = [];
  const feedback = asRecord(practice.rawFeedback);

  const focusInstruction =
    practice.focusArea ??
    asText(feedback?.corrective_guidance) ??
    recommendation?.practiceFocus ??
    null;

  const tempoInstruction =
    practice.tempoFeedback ??
    asText(feedback?.tempo_adjustment_recommendation) ??
    recommendation?.tempoAdjustment ??
    null;

  const targetTempo = practice.recommendedTempo ?? practice.songRecommendedTempo;

  if (practice.focusPhrase !== null && targetTempo !== null) {
    addNextStep(
      steps,
      `Repeat phrase ${practice.focusPhrase} at ${targetTempo} BPM for 5 focused repetitions.`,
    );
  } else if (practice.focusPhrase !== null) {
    addNextStep(steps, `Repeat phrase ${practice.focusPhrase} for 5 focused repetitions.`);
  }

  if (practice.targetDrill) {
    addNextStep(steps, `Run drill: ${practice.targetDrill}.`);
  }

  if (practice.variationStrategy) {
    addNextStep(steps, `Apply repeat guidance: ${practice.variationStrategy}.`);
  }

  if (focusInstruction) {
    addNextStep(steps, `Prioritize focus: ${focusInstruction}.`);
  }

  if (tempoInstruction) {
    addNextStep(steps, `Tempo action: ${tempoInstruction}.`);
  }

  if (recommendation?.suggestion) {
    addNextStep(steps, `Coach note: ${recommendation.suggestion}.`);
  }

  if (steps.length === 0) {
    addNextStep(
      steps,
      "Reattempt the same phrase and target steadier pitch and rhythm than the previous run.",
    );
  }

  return steps;
};

export const mapAnalyticsRecommendationToCoach = (
  payload: AnalyticsRecommendationApi | MessagePayload | null | undefined,
): AdaptiveCoachRecommendation | null => {
  const entry = asRecord(payload);
  if (!entry) {
    return null;
  }

  const recommendation: AdaptiveCoachRecommendation = {
    tempoAdjustment: asText(entry.recommended_tempo_adjustment),
    practiceFocus: asText(entry.practice_focus),
    suggestion: asText(entry.suggestion),
  };

  if (!recommendation.tempoAdjustment && !recommendation.practiceFocus && !recommendation.suggestion) {
    return null;
  }

  return recommendation;
};
