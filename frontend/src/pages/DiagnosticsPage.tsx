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
import { getPreferredUserId } from "../utils/userIdentity";

export default function DiagnosticsPage() {
  const [userId] = useState(getPreferredUserId());
  const [alankarId, setAlankarId] = useState("basic_alankar");
  const [songId, setSongId] = useState("song_1");
  const [debugPhraseInput, setDebugPhraseInput] = useState("0");

  const [debugState, setDebugState] = useState(initialAsyncState<unknown>());
  const [healthState, setHealthState] = useState(initialAsyncState<unknown>());

  const safeUserId = useMemo(() => userId.trim(), [userId]);
  const safeDebugPhraseId = useMemo(() => {
    const parsed = Number(debugPhraseInput);
    if (!Number.isFinite(parsed)) {
      return 0;
    }

    return Math.max(0, Math.floor(parsed));
  }, [debugPhraseInput]);

  const onAlankarIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setAlankarId(event.target.value);
  };

  const onSongIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSongId(event.target.value);
  };

  const onDebugPhraseIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setDebugPhraseInput(event.target.value);
  };

  const onDebugPhraseIdBlur = () => {
    setDebugPhraseInput(String(safeDebugPhraseId));
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
        getDebugPhrase(safeUserId, songId.trim(), safeDebugPhraseId),
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
        <p className="user-id-inline">
          <span className="user-id-inline-label">User ID:</span>{" "}
          <span className="user-id-inline-value">{userId}</span>
        </p>
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
          <input
            type="number"
            min={0}
            value={debugPhraseInput}
            onChange={onDebugPhraseIdChange}
            onBlur={onDebugPhraseIdBlur}
          />
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
