import { useEffect, useMemo, useRef, useState } from "react";
import ScreenState from "../components/ScreenState";
import { useAnalytics } from "../hooks/useAnalytics";
import { useStudentProfile } from "../hooks/useStudentProfile";
import { getPreferredUserId } from "../utils/userIdentity";

export default function DashboardPage() {
  const [userId] = useState(getPreferredUserId());
  const { profileState, streakState, loadProfile, loadStreak } = useStudentProfile();
  const {
    analyticsState,
    learningDifficultyState,
    learningModelState,
    learningRecommendationState,
    loadAnalytics,
    loadLearningIntelligence,
  } = useAnalytics();
  const hasLoadedOnVisitRef = useRef(false);

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  const onLoadDashboard = async () => {
    try {
      await Promise.all([
        loadProfile(safeUserId),
        loadAnalytics(safeUserId),
        loadLearningIntelligence(safeUserId),
        loadStreak(safeUserId),
      ]);
    } catch {
      return;
    }
  };

  useEffect(() => {
    if (!safeUserId || hasLoadedOnVisitRef.current) {
      return;
    }

    hasLoadedOnVisitRef.current = true;
    void Promise.all([
      loadProfile(safeUserId),
      loadAnalytics(safeUserId),
      loadLearningIntelligence(safeUserId),
      loadStreak(safeUserId),
    ]).catch(() => undefined);
  }, [loadAnalytics, loadLearningIntelligence, loadProfile, loadStreak, safeUserId]);

  const profile = profileState.data?.data;
  const analytics = analyticsState.data?.data;
  const streak = streakState.data?.data;
  const difficultyPayload = learningDifficultyState.data;
  const recommendationPayload = learningRecommendationState.data;
  const modelPayload = learningModelState.data;

  const difficulty =
    difficultyPayload && !("message" in difficultyPayload)
      ? difficultyPayload
      : null;
  const recommendation =
    recommendationPayload && !("message" in recommendationPayload)
      ? recommendationPayload
      : null;
  const modelStatus =
    modelPayload && !("message" in modelPayload)
      ? modelPayload
      : null;

  return (
    <div className="container">
      <section className="venora-banner" aria-label="Project banner">
        <p className="venora-banner-kicker">Hey there...!</p>
        <h1 className="venora-banner-title">VENORA</h1>
        <p className="venora-banner-subtitle">AI-Powered Flute Learning Dashboard</p>
      </section>

      <h2 className="dashboard-page-title">Dashboard</h2>

      <section className="card">
        <p className="user-id-inline">
          <span className="user-id-inline-label">User ID:</span>{" "}
          <span className="user-id-inline-value">{userId}</span>
        </p>
        <div className="row">
          <button onClick={onLoadDashboard}>Refresh Dashboard</button>
        </div>
      </section>

      <section className="grid">
        <article className="result-card">
          <h3>Student Snapshot</h3>
          <ScreenState
            loading={profileState.loading}
            error={profileState.error}
            emptyMessage={profileState.data?.empty.isEmpty ? profileState.data.empty.message ?? undefined : undefined}
          />
          {profile && !profileState.loading && !profileState.error && (
            <div className="stack-sm">
              <p><strong>Current Level:</strong> {profile.currentLevel}</p>
              <p><strong>Composite Score:</strong> {profile.compositeScore ?? "N/A"}</p>
              <p><strong>Recommended Content:</strong> {profile.recommendedContent ?? "N/A"}</p>
            </div>
          )}
        </article>

        <article className="result-card">
          <h3>Streak</h3>
          <ScreenState
            loading={streakState.loading}
            error={streakState.error}
            emptyMessage={streakState.data?.empty.isEmpty ? streakState.data.empty.message ?? undefined : undefined}
          />
          {streak && !streakState.loading && !streakState.error && (
            <div className="stack-sm">
              <p><strong>Current:</strong> {streak.currentStreak}</p>
              <p><strong>Longest:</strong> {streak.longestStreak}</p>
              <p><strong>Total Practice Days:</strong> {streak.totalPracticeDays}</p>
            </div>
          )}
        </article>

        <article className="result-card">
          <h3>Analytics</h3>
          <ScreenState
            loading={analyticsState.loading}
            error={analyticsState.error}
            emptyMessage={analyticsState.data?.empty.isEmpty ? analyticsState.data.empty.message ?? undefined : undefined}
          />
          {analytics && !analyticsState.loading && !analyticsState.error && (
            <div className="stack-sm">
              <p><strong>Trend Label:</strong> {analytics.trendLabel ?? "N/A"}</p>
              <p><strong>Slope:</strong> {analytics.slope ?? "N/A"}</p>
              <p><strong>Consistency:</strong> {analytics.consistencyIndex ?? "N/A"}</p>
              <p><strong>Composite:</strong> {analytics.compositeScore ?? "N/A"}</p>
            </div>
          )}
        </article>

        <article className="result-card">
          <h3>Learning Recommendation</h3>
          <ScreenState
            loading={learningRecommendationState.loading || learningDifficultyState.loading}
            error={learningRecommendationState.error ?? learningDifficultyState.error}
            emptyMessage={
              recommendationPayload && "message" in recommendationPayload
                ? recommendationPayload.message
                : difficultyPayload && "message" in difficultyPayload
                  ? difficultyPayload.message
                  : undefined
            }
          />
          {recommendation && difficulty && !learningRecommendationState.loading && !learningDifficultyState.loading && (
            <div className="stack-sm">
              <p><strong>Difficulty:</strong> {difficulty.difficulty_level ?? "N/A"}</p>
              <p><strong>Predicted Next Accuracy:</strong> {recommendation.predicted_next_accuracy ?? "N/A"}</p>
              <p><strong>Tempo:</strong> {recommendation.recommended_tempo_adjustment ?? "N/A"}</p>
              <p><strong>Focus:</strong> {recommendation.practice_focus ?? "N/A"}</p>
              <p><strong>Recommended Content Type:</strong> {recommendation.recommended_content_type ?? "N/A"}</p>
            </div>
          )}
        </article>

        <article className="result-card">
          <h3>Learning Model</h3>
          <ScreenState
            loading={learningModelState.loading}
            error={learningModelState.error}
            emptyMessage={
              modelPayload && "message" in modelPayload
                ? modelPayload.message
                : undefined
            }
          />
          {modelStatus && !learningModelState.loading && !learningModelState.error && (
            <div className="stack-sm">
              <p><strong>Source:</strong> {modelStatus.source ?? "N/A"}</p>
              <p><strong>Sample Pairs:</strong> {modelStatus.sample_pairs ?? "N/A"}</p>
              <p><strong>MAE:</strong> {modelStatus.mae ?? "N/A"}</p>
              <p><strong>Reason:</strong> {modelStatus.reason ?? "N/A"}</p>
            </div>
          )}
        </article>
      </section>

      {profile && (
        <section className="card">
          <h2>Content Status</h2>
          <div className="grid">
            <article className="result-card">
              <h3>Unlocked</h3>
              {profile.unlockedContent.length === 0 ? (
                <p className="muted">No unlocked content.</p>
              ) : (
                <ul className="plain-list">
                  {profile.unlockedContent.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
            </article>
            <article className="result-card">
              <h3>Mastered</h3>
              {profile.masteredContent.length === 0 ? (
                <p className="muted">No mastered content yet.</p>
              ) : (
                <ul className="plain-list">
                  {profile.masteredContent.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
            </article>
          </div>
        </section>
      )}
    </div>
  );
}
