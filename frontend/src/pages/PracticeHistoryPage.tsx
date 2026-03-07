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
import { getPreferredUserId } from "../utils/userIdentity";

export default function PracticeHistoryPage() {
  const [userId] = useState(getPreferredUserId());
  const [limitInput, setLimitInput] = useState("20");
  const { historyState, loadPracticeHistory } = usePracticeHistory();
  const hasLoadedOnVisitRef = useRef(false);

  const safeUserId = useMemo(() => userId.trim(), [userId]);
  const safeLimit = useMemo(() => {
    const parsed = Number(limitInput);
    if (!Number.isFinite(parsed)) {
      return 20;
    }

    return Math.max(1, Math.min(100, Math.floor(parsed)));
  }, [limitInput]);

  const onLimitChange = (event: ChangeEvent<HTMLInputElement>) => {
    setLimitInput(event.target.value);
  };

  const onLimitBlur = () => {
    setLimitInput(String(safeLimit));
  };

  const onLoadHistory = async () => {
    try {
      await loadPracticeHistory(safeUserId, safeLimit);
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
    void loadPracticeHistory(safeUserId, safeLimit).catch(() => undefined);
  }, [loadPracticeHistory, safeLimit, safeUserId]);

  useEffect(() => {
    if (!safeUserId) {
      return;
    }

    const maybeAutoRefresh = async (signal: PracticeRefreshSignal | null) => {
      if (!signal || !isPracticeRefreshPending("practice-history", signal, safeUserId)) {
        return;
      }

      try {
        await loadPracticeHistory(safeUserId, safeLimit);
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
  }, [loadPracticeHistory, safeLimit, safeUserId]);

  return (
    <div className="container">
      <h1>Practice History</h1>

      <section className="card">
        <p className="user-id-inline">
          <span className="user-id-inline-label">User ID:</span>{" "}
          <span className="user-id-inline-value">{userId}</span>
        </p>
        <label>
          Session Limit
          <input
            type="number"
            min={1}
            max={100}
            value={limitInput}
            onChange={onLimitChange}
            onBlur={onLimitBlur}
          />
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
