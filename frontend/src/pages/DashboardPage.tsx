import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import ScreenState from "../components/ScreenState";
import { useAnalytics } from "../hooks/useAnalytics";
import { useStudentProfile } from "../hooks/useStudentProfile";

export default function DashboardPage() {
  const [userId, setUserId] = useState("demo_user");
  const { profileState, streakState, loadProfile, loadStreak } = useStudentProfile();
  const { analyticsState, loadAnalytics } = useAnalytics();

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  const onLoadDashboard = async () => {
    try {
      await Promise.all([
        loadProfile(safeUserId),
        loadAnalytics(safeUserId),
        loadStreak(safeUserId),
      ]);
    } catch {
      return;
    }
  };

  const profile = profileState.data?.data;
  const analytics = analyticsState.data?.data;
  const streak = streakState.data?.data;

  return (
    <div className="container">
      <h1>Dashboard</h1>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <div className="row">
          <button onClick={onLoadDashboard}>Load Dashboard</button>
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
