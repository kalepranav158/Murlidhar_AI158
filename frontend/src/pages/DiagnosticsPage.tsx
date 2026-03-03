import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import {
  askGuru,
  getAnalyticsConsistency,
  getAnalyticsConsistencyDetails,
  getAnalyticsDashboard,
  getAnalyticsForecast,
  getAnalyticsPitchStabilityControl,
  getAnalyticsRadar,
  getAnalyticsRecommendationAdaptivePlan,
  getAnalyticsRisk,
  getAnalyticsSkillEvolution,
  getAnalyticsSkillLevel,
  getAnalyticsSummary,
  getAnalyticsTestDashboard,
  getAnalyticsTrend,
  getAnalyticsWeakestPhrase,
  getDebugAlankar,
  getDebugAnalytics,
  getDebugPhrase,
  getDebugSessions,
  getDebugStudent,
  getRootHealth,
} from "../api";
import ResultCard from "../components/ResultCard";
import { initialAsyncState, type AsyncState } from "../types/ui";

export default function DiagnosticsPage() {
  const [userId, setUserId] = useState("demo_user");
  const [alankarId, setAlankarId] = useState("basic_alankar");
  const [songId, setSongId] = useState("song_1");
  const [debugPhraseId, setDebugPhraseId] = useState(0);
  const [question, setQuestion] = useState("How should I improve rhythm stability?");

  const [analyticsFullState, setAnalyticsFullState] = useState(initialAsyncState<unknown>());
  const [askState, setAskState] = useState(initialAsyncState<unknown>());
  const [debugState, setDebugState] = useState(initialAsyncState<unknown>());
  const [healthState, setHealthState] = useState(initialAsyncState<unknown>());

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  const onUserIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUserId(event.target.value);
  };

  const onAlankarIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setAlankarId(event.target.value);
  };

  const onSongIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSongId(event.target.value);
  };

  const onDebugPhraseIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setDebugPhraseId(Number(event.target.value || 0));
  };

  const onQuestionChange = (event: ChangeEvent<HTMLInputElement>) => {
    setQuestion(event.target.value);
  };

  const runCall = async <T,>(setter: (next: AsyncState<T>) => void, fn: () => Promise<T>) => {
    setter({ loading: true, error: null, data: null });
    try {
      const payload = await fn();
      setter({ loading: false, error: null, data: payload });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setter({ loading: false, error: message, data: null });
    }
  };

  const onLoadAnalyticsFullSet = async () => {
    await runCall(setAnalyticsFullState, async () => {
      const [
        summary,
        trend,
        skillLevel,
        consistency,
        pitchStability,
        recommendation,
        consistencyDetails,
        dashboard,
        testDashboard,
        radar,
        skillEvolution,
        risk,
        forecast,
        weakestPhrase,
      ] = await Promise.all([
        getAnalyticsSummary(safeUserId),
        getAnalyticsTrend(safeUserId),
        getAnalyticsSkillLevel(safeUserId),
        getAnalyticsConsistency(safeUserId),
        getAnalyticsPitchStabilityControl(safeUserId),
        getAnalyticsRecommendationAdaptivePlan(safeUserId),
        getAnalyticsConsistencyDetails(safeUserId),
        getAnalyticsDashboard(safeUserId),
        getAnalyticsTestDashboard(safeUserId),
        getAnalyticsRadar(safeUserId),
        getAnalyticsSkillEvolution(safeUserId),
        getAnalyticsRisk(safeUserId),
        getAnalyticsForecast(safeUserId),
        getAnalyticsWeakestPhrase(safeUserId, songId.trim()),
      ]);

      return {
        summary,
        trend,
        skillLevel,
        consistency,
        pitchStability,
        recommendation,
        consistencyDetails,
        dashboard,
        testDashboard,
        radar,
        skillEvolution,
        risk,
        forecast,
        weakestPhrase,
      };
    });
  };

  const onAskGuru = async () => {
    await runCall(setAskState, async () =>
      askGuru(safeUserId, {
        question: question.trim(),
      }),
    );
  };

  const onLoadDebugSet = async () => {
    await runCall(setDebugState, async () => {
      const [sessions, alankar, phrase, analytics, student] = await Promise.all([
        getDebugSessions(safeUserId),
        getDebugAlankar(safeUserId, alankarId.trim()),
        getDebugPhrase(safeUserId, songId.trim(), debugPhraseId),
        getDebugAnalytics(safeUserId),
        getDebugStudent(safeUserId),
      ]);

      return {
        sessions,
        alankar,
        phrase,
        analytics,
        student,
      };
    });
  };

  const onCheckHealth = async () => {
    await runCall(setHealthState, async () => getRootHealth());
  };

  return (
    <div className="container">
      <h1>Diagnostics</h1>

      <section className="card">
        <h2>Context</h2>
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>
        <label>
          Alankar ID
          <input value={alankarId} onChange={onAlankarIdChange} />
        </label>
        <label>
          Song ID
          <input value={songId} onChange={onSongIdChange} />
        </label>
        <label>
          Debug Phrase ID
          <input type="number" min={0} value={debugPhraseId} onChange={onDebugPhraseIdChange} />
        </label>
      </section>

      <section className="card">
        <h2>Analytics Endpoint Group</h2>
        <div className="row">
          <button onClick={onLoadAnalyticsFullSet}>Load Full Analytics Set</button>
        </div>
        <section className="grid">
          <ResultCard title="Analytics (Full Set)" state={analyticsFullState} />
        </section>
      </section>

      <section className="card">
        <h2>Ask Endpoint</h2>
        <label>
          Question
          <input value={question} onChange={onQuestionChange} />
        </label>
        <div className="row">
          <button onClick={onAskGuru}>Ask Guru</button>
        </div>
        <section className="grid">
          <ResultCard title="Ask" state={askState} />
        </section>
      </section>

      <section className="card">
        <h2>Debug Endpoint Group</h2>
        <p className="muted">Works only when DEBUG_ENDPOINTS is enabled on backend.</p>
        <div className="row">
          <button onClick={onLoadDebugSet}>Load Full Debug Set</button>
          <button onClick={onCheckHealth}>Check Root Health</button>
        </div>

        <section className="grid">
          <ResultCard title="Debug" state={debugState} />
          <ResultCard title="Health" state={healthState} />
        </section>
      </section>
    </div>
  );
}
