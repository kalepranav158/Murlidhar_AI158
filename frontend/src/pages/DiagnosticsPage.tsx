import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import {
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
        <p className="muted">Analytics charts are available in the dedicated Analytics page. Diagnostics stays debug-only.</p>
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
