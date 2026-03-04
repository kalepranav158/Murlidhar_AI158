import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import ScreenState from "../components/ScreenState";
import { PracticeHistoryPanel, usePracticeHistory } from "../modules/practice-history";
import {
  getLatestPracticeRefreshSignal,
  isPracticeRefreshPending,
  markPracticeRefreshHandled,
  subscribePracticeRefreshSignal,
  type PracticeRefreshSignal,
} from "../utils/practiceRefreshSignal";

export default function PracticeHistoryPage() {
  const [userId, setUserId] = useState("demo_user");
  const [limit, setLimit] = useState(20);
  const { historyState, loadPracticeHistory } = usePracticeHistory();
  const hasLoadedOnVisitRef = useRef(false);

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  const onLimitChange = (event: ChangeEvent<HTMLInputElement>) => {
    setLimit(Number(event.target.value || 20));
  };

  const onLoadHistory = async () => {
    try {
      await loadPracticeHistory(safeUserId, limit);
    } catch {
      return;
    }
  };

  useEffect(() => {
    if (!safeUserId || hasLoadedOnVisitRef.current) {
      return;
    }

    const latestSignal = getLatestPracticeRefreshSignal();
    if (latestSignal && isPracticeRefreshPending("practice-history", latestSignal, safeUserId)) {
      return;
    }

    hasLoadedOnVisitRef.current = true;
    void loadPracticeHistory(safeUserId, limit).catch(() => undefined);
  }, [limit, loadPracticeHistory, safeUserId]);

  useEffect(() => {
    if (!safeUserId) {
      return;
    }

    const maybeAutoRefresh = async (signal: PracticeRefreshSignal | null) => {
      if (!signal || !isPracticeRefreshPending("practice-history", signal, safeUserId)) {
        return;
      }

      try {
        await loadPracticeHistory(safeUserId, limit);
        markPracticeRefreshHandled("practice-history", signal);
      } catch {
        return;
      }
    };

    void maybeAutoRefresh(getLatestPracticeRefreshSignal());

    const unsubscribe = subscribePracticeRefreshSignal((signal) => {
      void maybeAutoRefresh(signal);
    });

    return unsubscribe;
  }, [limit, loadPracticeHistory, safeUserId]);

  return (
    <div className="container">
      <h1>Practice History</h1>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <label>
          Session Limit
          <input type="number" min={1} max={100} value={limit} onChange={onLimitChange} />
        </label>
        <div className="row">
          <button onClick={onLoadHistory}>Refresh Practice History</button>
        </div>
      </section>

      <article className="result-card">
        <h3>Learning Timeline</h3>
        <ScreenState
          loading={historyState.loading}
          error={historyState.error}
          emptyMessage={historyState.data?.empty.isEmpty ? historyState.data.empty.message ?? undefined : undefined}
        />

        {!historyState.loading && !historyState.error && historyState.data && !historyState.data.empty.isEmpty && (
          <PracticeHistoryPanel history={historyState.data.data} />
        )}
      </article>
    </div>
  );
}
