import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import ScreenState from "../components/ScreenState";
import { useAnalytics } from "../hooks/useAnalytics";

export default function ProgressPage() {
  const [userId, setUserId] = useState("demo_user");
  const { analyticsState, trendState, loadProgress } = useAnalytics();
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
      </section>
    </div>
  );
}
