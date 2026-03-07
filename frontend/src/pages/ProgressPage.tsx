import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { getSessions } from "../api";
import ScreenState from "../components/ScreenState";
import { useAnalytics } from "../hooks/useAnalytics";
import { EChartBase } from "../modules/charts";
import {
  buildCompositeTrendOption,
  buildSkillImprovementOption,
  type ProgressAnalyticsPoint,
} from "../modules/progress-analytics/options/buildProgressAnalyticsOptions";
import type { MessagePayload, SessionsApi } from "../types/api";
import { initialAsyncState, type AsyncState } from "../types/ui";

export default function ProgressPage() {
  const [userId, setUserId] = useState("demo_user");
  const [sessionsState, setSessionsState] =
    useState<AsyncState<SessionsApi | MessagePayload>>(initialAsyncState());
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

  const loadSessions = useCallback(async (targetUserId: string) => {
    setSessionsState({ loading: true, error: null, data: null });

    try {
      const payload = await getSessions(targetUserId, 30);
      setSessionsState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setSessionsState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  const onLoadProgress = async () => {
    try {
      await Promise.all([loadProgress(safeUserId), loadSessions(safeUserId)]);
    } catch {
      return;
    }
  };

  useEffect(() => {
    if (!safeUserId || hasLoadedOnVisitRef.current) {
      return;
    }

    hasLoadedOnVisitRef.current = true;
    void Promise.all([loadProgress(safeUserId), loadSessions(safeUserId)]).catch(() => undefined);
  }, [loadProgress, loadSessions, safeUserId]);

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

  const sessions =
    sessionsState.data && !("message" in sessionsState.data)
      ? sessionsState.data.sessions ?? []
      : [];

  const toPercentScore = (value: unknown): number | null => {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      return null;
    }

    if (value <= 1) {
      return Math.round(value * 1000) / 10;
    }

    return Math.round(value * 10) / 10;
  };

  const progressChartPoints = useMemo<ProgressAnalyticsPoint[]>(() => {
    const chronologicalSessions = [...sessions].reverse();

    return chronologicalSessions.map((session, index) => ({
      label: `S${index + 1}`,
      accuracy: toPercentScore(session.note_accuracy),
      pitch: toPercentScore(session.pitch_index),
      rhythm: toPercentScore(session.rhythm_index),
      technique: toPercentScore(session.technique_score),
      composite: toPercentScore(session.composite_score),
    }));
  }, [sessions]);

  const skillImprovementOption = useMemo(
    () => (progressChartPoints.length > 0 ? buildSkillImprovementOption(progressChartPoints) : null),
    [progressChartPoints],
  );

  const compositeTrendOption = useMemo(
    () => (progressChartPoints.length > 0 ? buildCompositeTrendOption(progressChartPoints) : null),
    [progressChartPoints],
  );

  const progressChartLoading = sessionsState.loading || trendState.loading;
  const progressChartError = sessionsState.error ?? trendState.error;
  const progressChartEmptyMessage =
    sessionsState.data && "message" in sessionsState.data
      ? sessionsState.data.message
      : trendState.data && "message" in trendState.data
        ? trendState.data.message
        : progressChartPoints.length === 0
          ? "No progress chart data available."
          : undefined;

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

      <section className="card chart-card">
        <h2 className="chart-title">Learning Analytics Charts</h2>
        <ScreenState
          loading={progressChartLoading}
          error={progressChartError}
          emptyMessage={progressChartEmptyMessage}
        />

        {!progressChartLoading && !progressChartError && progressChartPoints.length > 0 && (
          <div className="progress-analytics-grid">
            <article className="chart-card">
              <h3 className="chart-title">Skill Improvement</h3>
              <EChartBase option={skillImprovementOption} height={320} renderer="canvas" />
            </article>

            <article className="chart-card">
              <h3 className="chart-title">Accuracy vs Composite</h3>
              <EChartBase option={compositeTrendOption} height={320} renderer="canvas" />
            </article>
          </div>
        )}
      </section>
    </div>
  );
}
