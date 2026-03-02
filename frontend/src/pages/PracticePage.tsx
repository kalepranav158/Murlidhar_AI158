import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import {
  API_BASE_URL,
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
  getStudentAnalytics,
  getStudentCurriculum,
  getStudentProfile,
  getStudentStreak,
  submitAlankarPractice,
} from "../api";
import ResultCard from "../components/ResultCard";
import { initialAsyncState, type AsyncState } from "../types/ui";

export default function PracticePage() {
  const [userId, setUserId] = useState("demo_user");
  const [alankarId, setAlankarId] = useState("basic_alankar");
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [songId, setSongId] = useState("song_1");
  const [debugPhraseId, setDebugPhraseId] = useState(0);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("How should I improve rhythm stability?");

  const [profileState, setProfileState] = useState(initialAsyncState<unknown>());
  const [curriculumState, setCurriculumState] = useState(initialAsyncState<unknown>());
  const [analyticsState, setAnalyticsState] = useState(initialAsyncState<unknown>());
  const [streakState, setStreakState] = useState(initialAsyncState<unknown>());
  const [practiceState, setPracticeState] = useState(initialAsyncState<unknown>());
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

  const onPhraseIndexChange = (event: ChangeEvent<HTMLInputElement>) => {
    setPhraseIndex(Number(event.target.value || 0));
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

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setAudioFile(event.target.files?.[0] ?? null);
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

  const onLoadProfile = async () => {
    await runCall(setProfileState, async () => getStudentProfile(safeUserId));
  };

  const onLoadCurriculum = async () => {
    await runCall(setCurriculumState, async () => getStudentCurriculum(safeUserId));
  };

  const onLoadAnalytics = async () => {
    await runCall(setAnalyticsState, async () => getStudentAnalytics(safeUserId));
  };

  const onLoadStreak = async () => {
    await runCall(setStreakState, async () => getStudentStreak(safeUserId));
  };

  const onPracticeAlankar = async () => {
    if (!audioFile) {
      setPracticeState({ loading: false, error: "Select a WAV file first.", data: null });
      return;
    }

    await runCall(setPracticeState, async () =>
      submitAlankarPractice({
        userId: safeUserId,
        alankarId,
        phraseIndex,
        audioFile,
      }),
    );
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
      <h1>Frontend Integration Smoke Test</h1>
      <p className="muted">Base URL: {API_BASE_URL}</p>

      <section className="card">
        <h2>Request Context</h2>
        <label>
          User ID
          <input value={userId} onChange={onUserIdChange} />
        </label>

        <div className="row">
          <button onClick={onLoadProfile}>Load Profile</button>
          <button onClick={onLoadCurriculum}>Load Curriculum</button>
          <button onClick={onLoadAnalytics}>Load Analytics</button>
          <button onClick={onLoadStreak}>Load Streak</button>
        </div>

        <section className="grid">
          <ResultCard title="Profile" state={profileState} />
          <ResultCard title="Curriculum" state={curriculumState} />
          <ResultCard title="Analytics" state={analyticsState} />
          <ResultCard title="Streak" state={streakState} />
        </section>
      </section>

      <section className="card">
        <h2>Practice (WAV Upload)</h2>
        <label>
          Alankar ID
          <input value={alankarId} onChange={onAlankarIdChange} />
        </label>
        <label>
          Phrase Index
          <input
            type="number"
            min={0}
            value={phraseIndex}
            onChange={onPhraseIndexChange}
          />
        </label>
        <label>
          Song ID (for analytics weakest-phrase & debug phrase)
          <input value={songId} onChange={onSongIdChange} />
        </label>
        <label>
          Debug Phrase ID
          <input type="number" min={0} value={debugPhraseId} onChange={onDebugPhraseIdChange} />
        </label>
        <label>
          WAV File
          <input
            type="file"
            accept="audio/wav,.wav"
            onChange={onFileChange}
          />
        </label>

        <div className="row">
          <button onClick={onPracticeAlankar}>Submit Alankar Practice</button>
        </div>

        <section className="grid">
          <ResultCard title="Practice" state={practiceState} />
        </section>
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
