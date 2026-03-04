import { useEffect, useMemo, useRef } from "react";
import ScreenState from "../../components/ScreenState";
import type { PracticeResultNormalized } from "../../types/normalized";
import AdaptiveCoachDrillCards from "./components/AdaptiveCoachDrillCards";
import { useAdaptiveCoach } from "./hooks/useAdaptiveCoach";
import {
  mapPracticeToNextSteps,
  mapPracticeToCoachDrillCards,
} from "./mappers";

type AdaptiveCoachPanelProps = {
  userId: string;
  practice: PracticeResultNormalized;
};

export default function AdaptiveCoachPanel({ userId, practice }: AdaptiveCoachPanelProps) {
  const cards = useMemo(() => mapPracticeToCoachDrillCards(practice), [practice]);
  const lastAutoRecommendationKey = useRef<string | null>(null);
  const {
    recommendationState,
    loadRecommendation,
  } = useAdaptiveCoach();
  const nextSteps = useMemo(
    () => mapPracticeToNextSteps(practice, recommendationState.data),
    [practice, recommendationState.data],
  );

  const recommendationAutoKey = useMemo(
    () => [
      userId,
      practice.song ?? "na",
      practice.phraseIndex ?? "na",
      practice.noteAccuracy ?? "na",
      practice.avgPitchErrorCents ?? "na",
      practice.avgTimingErrorSec ?? "na",
      practice.recommendedTempo ?? "na",
      practice.focusPhrase ?? "na",
      practice.focusArea ?? "na",
    ].join("|"),
    [
      userId,
      practice.song,
      practice.phraseIndex,
      practice.noteAccuracy,
      practice.avgPitchErrorCents,
      practice.avgTimingErrorSec,
      practice.recommendedTempo,
      practice.focusPhrase,
      practice.focusArea,
    ],
  );

  useEffect(() => {
    if (!userId.trim()) {
      return;
    }

    if (lastAutoRecommendationKey.current === recommendationAutoKey) {
      return;
    }

    lastAutoRecommendationKey.current = recommendationAutoKey;
    void loadRecommendation(userId).catch(() => undefined);
  }, [loadRecommendation, recommendationAutoKey, userId]);

  const onLoadRecommendation = async () => {
    try {
      await loadRecommendation(userId);
    } catch {
      return;
    }
  };

  return (
    <section className="adaptive-coach-panel">
      <h3>Adaptive Coach</h3>

      <AdaptiveCoachDrillCards cards={cards} />

      <div className="row">
        <button onClick={onLoadRecommendation}>Refresh Adaptive Recommendation</button>
      </div>

      <div className="adaptive-coach-sections">
        <article className="adaptive-coach-block">
          <h4>Analytics Recommendation</h4>
          <ScreenState
            loading={recommendationState.loading}
            error={recommendationState.error}
            emptyMessage={
              !recommendationState.loading && !recommendationState.error && recommendationState.data === null
                ? "No adaptive recommendation available for this attempt."
                : undefined
            }
          />

          {recommendationState.data && !recommendationState.loading && !recommendationState.error && (
            <div className="stack-sm">
              {recommendationState.data.tempoAdjustment && (
                <p><strong>Tempo adjustment:</strong> {recommendationState.data.tempoAdjustment}</p>
              )}
              {recommendationState.data.practiceFocus && (
                <p><strong>Practice focus:</strong> {recommendationState.data.practiceFocus}</p>
              )}
              {recommendationState.data.suggestion && (
                <p><strong>Suggestion:</strong> {recommendationState.data.suggestion}</p>
              )}
            </div>
          )}
        </article>

        <article className="adaptive-coach-block">
          <h4>Next Steps</h4>
          {nextSteps.length === 0 ? (
            <p className="muted">No next steps available for this attempt.</p>
          ) : (
            <ol className="plain-list">
              {nextSteps.map((step, index) => (
                <li key={`next-step-${index}`}>{step}</li>
              ))}
            </ol>
          )}
        </article>
      </div>
    </section>
  );
}
