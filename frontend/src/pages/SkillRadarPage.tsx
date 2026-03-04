import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import ScreenState from "../components/ScreenState";
import { SkillRadarPanel, useSkillRadar } from "../modules/skill-radar";
import {
  getLatestPracticeRefreshSignal,
  isPracticeRefreshPending,
  markPracticeRefreshHandled,
  subscribePracticeRefreshSignal,
  type PracticeRefreshSignal,
} from "../utils/practiceRefreshSignal";

export default function SkillRadarPage() {
  const [userId, setUserId] = useState("demo_user");
  const { radarState, loadSkillRadar } = useSkillRadar();
  const hasLoadedOnVisitRef = useRef(false);

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  const onLoadRadar = async () => {
    try {
      await loadSkillRadar(safeUserId);
    } catch {
      return;
    }
  };

  useEffect(() => {
    if (!safeUserId || hasLoadedOnVisitRef.current) {
      return;
    }

    const latestSignal = getLatestPracticeRefreshSignal();
    if (latestSignal && isPracticeRefreshPending("skill-radar", latestSignal, safeUserId)) {
      return;
    }

    hasLoadedOnVisitRef.current = true;
    void loadSkillRadar(safeUserId).catch(() => undefined);
  }, [loadSkillRadar, safeUserId]);

  useEffect(() => {
    if (!safeUserId) {
      return;
    }

    const maybeAutoRefresh = async (signal: PracticeRefreshSignal | null) => {
      if (!signal || !isPracticeRefreshPending("skill-radar", signal, safeUserId)) {
        return;
      }

      try {
        await loadSkillRadar(safeUserId);
        markPracticeRefreshHandled("skill-radar", signal);
      } catch {
        return;
      }
    };

    void maybeAutoRefresh(getLatestPracticeRefreshSignal());

    const unsubscribe = subscribePracticeRefreshSignal((signal) => {
      void maybeAutoRefresh(signal);
    });

    return unsubscribe;
  }, [loadSkillRadar, safeUserId]);

  return (
    <div className="container">
      <h1>Skill Radar</h1>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <div className="row">
          <button onClick={onLoadRadar}>Refresh Skill Radar</button>
        </div>
      </section>

      <article className="result-card">
        <h3>Skill Balance</h3>
        <ScreenState
          loading={radarState.loading}
          error={radarState.error}
          emptyMessage={radarState.data?.empty.isEmpty ? radarState.data.empty.message ?? undefined : undefined}
        />

        {!radarState.loading && !radarState.error && radarState.data && !radarState.data.empty.isEmpty && (
          <SkillRadarPanel radar={radarState.data.data} />
        )}
      </article>
    </div>
  );
}
