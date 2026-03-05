import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import ScreenState from "../components/ScreenState";
import { useAnalytics } from "../hooks/useAnalytics";

export default function ProgressPage() {
  const [userId, setUserId] = useState("demo_user");
  const {
    analyticsState,
    learningDifficultyState,
    learningRecommendationState,
    trendState,
    loadProgress,
  } = useAnalytics();
  const hasLoadedOnVisitRef = useRef(false);

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  const onLoadProgress = async () => {
    try {
      await loadProgress(safeUserId);
    } catch {
      return;
    }
  };

  useEffect(() => {
    if (!safeUserId || hasLoadedOnVisitRef.current) {
      return;
    }

    hasLoadedOnVisitRef.current = true;
    void loadProgress(safeUserId).catch(() => undefined);
  }, [loadProgress, safeUserId]);

  const analytics = analyticsState.data?.data;
  const difficultyPayload = learningDifficultyState.data;
  const recommendationPayload = learningRecommendationState.data;

  const difficulty =
    difficultyPayload && !("message" in difficultyPayload)
      ? difficultyPayload
      : null;
  const recommendation =
    recommendationPayload && !("message" in recommendationPayload)
      ? recommendationPayload
      : null;

  const trendSeries =
    trendState.data && "accuracy_series" in trendState.data
      ? trendState.data.accuracy_series ?? []
      : [];

  return (
    <div className="container">
      <h1>Progress</h1>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <div className="row">
          <button onClick={onLoadProgress}>Refresh Progress</button>
        </div>
      </section>

      <section className="grid">
        <article className="result-card">
          <h3>Analytics Snapshot</h3>
          <ScreenState
            loading={analyticsState.loading}
            error={analyticsState.error}
            emptyMessage={analyticsState.data?.empty.isEmpty ? analyticsState.data.empty.message ?? undefined : undefined}
          />

          {analytics && !analyticsState.loading && !analyticsState.error && (
            <div className="stack-sm">
              <p><strong>Composite Score:</strong> {analytics.compositeScore ?? "N/A"}</p>
              <p><strong>Slope:</strong> {analytics.slope ?? "N/A"}</p>
              <p><strong>Trend:</strong> {analytics.trendLabel ?? "N/A"}</p>
              <p><strong>Consistency:</strong> {analytics.consistencyIndex ?? "N/A"}</p>
              <p><strong>Plateau:</strong> {analytics.plateau ? "Yes" : "No"}</p>
              <p><strong>Risk:</strong> {analytics.risk ? "Yes" : "No"}</p>
            </div>
          )}
        </article>

        <article className="result-card">
          <h3>Accuracy Trend Series</h3>
          <ScreenState
            loading={trendState.loading}
            error={trendState.error}
            emptyMessage={
              trendState.data && "message" in trendState.data
                ? trendState.data.message
                : trendSeries.length === 0
                  ? "No trend data."
                  : undefined
            }
          />

          {!trendState.loading && !trendState.error && trendSeries.length > 0 && (
            <ul className="plain-list">
              {trendSeries.slice(-15).map((point) => (
                <li key={point.session}>Session {point.session}: {point.accuracy}</li>
              ))}
            </ul>
          )}
        </article>

        <article className="result-card">
          <h3>Learning Guidance</h3>
          <ScreenState
            loading={learningDifficultyState.loading || learningRecommendationState.loading}
            error={learningDifficultyState.error ?? learningRecommendationState.error}
            emptyMessage={
              recommendationPayload && "message" in recommendationPayload
                ? recommendationPayload.message
                : difficultyPayload && "message" in difficultyPayload
                  ? difficultyPayload.message
                  : undefined
            }
          />

          {difficulty && recommendation && !learningDifficultyState.loading && !learningRecommendationState.loading && (
            <div className="stack-sm">
              <p><strong>Difficulty Level:</strong> {difficulty.difficulty_level ?? "N/A"}</p>
              <p><strong>Weakest Dimension:</strong> {difficulty.weakest_dimension ?? "N/A"}</p>
              <p><strong>Recommended Content Type:</strong> {difficulty.recommended_content_type ?? "N/A"}</p>
              <p><strong>Predicted Next Accuracy:</strong> {recommendation.predicted_next_accuracy ?? "N/A"}</p>
              <p><strong>Tempo Guidance:</strong> {recommendation.recommended_tempo_adjustment ?? "N/A"}</p>
              <p><strong>Practice Focus:</strong> {recommendation.practice_focus ?? "N/A"}</p>
            </div>
          )}
        </article>
      </section>
    </div>
  );
}
