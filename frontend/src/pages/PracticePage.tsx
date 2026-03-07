import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import {
  API_BASE_URL,
  getSongPhraseReference,
  listSongs,
} from "../api";
import { usePracticeSession } from "../hooks/usePracticeSession";
import { useStudentProfile } from "../hooks/useStudentProfile";
import ScreenState from "../components/ScreenState";
import type { SongPhraseReferenceApi } from "../types/api";
import { initialAsyncState, type AsyncState } from "../types/ui";
import { convertBlobToWavFile } from "../utils/audioToWav";
import { emitPracticeRefreshSignal } from "../utils/practiceRefreshSignal";
import { getPreferredUserId } from "../utils/userIdentity";
import { PracticeStudioPanel } from "../modules/practice-studio";

type ContentOption = {
  id: string;
  label: string;
  phraseCount: number | null;
};

type PhraseOption = {
  value: number;
  label: string;
};

type ReferenceNoteView = {
  note: string;
  time: number;
};

type ReferenceStepView = {
  key: string;
  stepNumber: number;
  note: string;
  beat: number;
  durationBeats: number | null;
  durationMs: number | null;
  progress: number;
};

const COUNT_IN_BEATS = 4;

const formatBeatNumber = (value: number) => {
  const normalized = Math.round(value * 100) / 100;
  return Number.isInteger(normalized) ? normalized.toFixed(0) : normalized.toFixed(2);
};

const toTitleToken = (value: string) => {
  return value
    .split(/[\s_-]+/)
    .filter((token) => token.length > 0)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
};

const formatScorePercent = (value: number | null) => {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "N/A";
  }

  if (value <= 1) {
    return `${Math.round(value * 100)}%`;
  }

  return `${Math.round(value)}%`;
};

export default function PracticePage() {
  const [userId] = useState(getPreferredUserId());
  const [mode, setMode] = useState<"alankar" | "song" | "melody">("alankar");
  const [inputMethod, setInputMethod] = useState<"upload" | "record">("upload");
  const [alankarId, setAlankarId] = useState("alankar_1");
  const [songId, setSongId] = useState("song_1");
  const [melodyId, setMelodyId] = useState("melody_1");
  const [alankarOptions, setAlankarOptions] = useState<ContentOption[]>([]);
  const [songOptions, setSongOptions] = useState<ContentOption[]>([]);
  const [melodyOptions, setMelodyOptions] = useState<ContentOption[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [phraseIndexInput, setPhraseIndexInput] = useState("0");
  const [tempoInput, setTempoInput] = useState("60");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [recordedWavFile, setRecordedWavFile] = useState<File | null>(null);
  const [recordedRawFile, setRecordedRawFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [recordingPreviewUrl, setRecordingPreviewUrl] = useState<string | null>(null);
  const [referenceState, setReferenceState] = useState<AsyncState<SongPhraseReferenceApi>>(initialAsyncState());
  const [metronomeRunning, setMetronomeRunning] = useState(false);
  const [metronomeMuted, setMetronomeMuted] = useState(false);
  const [metronomePositionBeats, setMetronomePositionBeats] = useState(0);
  const [metronomeTickCount, setMetronomeTickCount] = useState(0);
  const [isCountInActive, setIsCountInActive] = useState(false);
  const [countInRemaining, setCountInRemaining] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const metronomeFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const metronomeMutedRef = useRef(metronomeMuted);
  const { practiceState, submitAlankar, submitSong, submitMelody } = usePracticeSession();
  const { curriculumState, loadCurriculum } = useStudentProfile();

  useEffect(() => {
    metronomeMutedRef.current = metronomeMuted;
  }, [metronomeMuted]);

  const safeUserId = useMemo(() => userId.trim(), [userId]);
  const safePhraseIndex = useMemo(() => {
    const parsed = Number(phraseIndexInput);
    if (!Number.isFinite(parsed)) {
      return 0;
    }

    return Math.max(0, Math.floor(parsed));
  }, [phraseIndexInput]);
  const safeTempo = useMemo(() => {
    const parsed = Number(tempoInput);
    if (!Number.isFinite(parsed)) {
      return 60;
    }

    return Math.max(20, Math.min(220, Math.floor(parsed)));
  }, [tempoInput]);
  const selectedContentId = useMemo(() => {
    if (mode === "alankar") {
      return alankarId.trim();
    }

    if (mode === "song") {
      return songId.trim();
    }

    return melodyId.trim();
  }, [alankarId, melodyId, mode, songId]);
  const selectedContentLabel = useMemo(() => {
    if (mode === "alankar") {
      return "Alankar";
    }

    if (mode === "song") {
      return "Song";
    }

    return "Melody";
  }, [mode]);

  const selectedContentOption = useMemo(() => {
    const options = mode === "alankar" ? alankarOptions : mode === "song" ? songOptions : melodyOptions;
    return options.find((option) => option.id === selectedContentId) ?? null;
  }, [alankarOptions, melodyOptions, mode, selectedContentId, songOptions]);

  const selectedPhraseCount = useMemo(() => {
    const fromOption = selectedContentOption?.phraseCount;
    if (typeof fromOption === "number" && Number.isFinite(fromOption) && fromOption > 0) {
      return Math.max(1, Math.floor(fromOption));
    }

    const fromReference = referenceState.data?.phrase_count;
    if (typeof fromReference === "number" && Number.isFinite(fromReference) && fromReference > 0) {
      return Math.max(1, Math.floor(fromReference));
    }

    return 1;
  }, [referenceState.data?.phrase_count, selectedContentOption?.phraseCount]);

  const phraseOptions = useMemo<PhraseOption[]>(() => {
    const options: PhraseOption[] = [];

    for (let index = 0; index < selectedPhraseCount; index += 1) {
      const isCombinedPhrase = mode === "alankar" && index === selectedPhraseCount - 1;
      options.push({
        value: index,
        label: isCombinedPhrase ? "Combined Phrase" : `Phrase ${index + 1}`,
      });
    }

    return options;
  }, [mode, selectedPhraseCount]);

  useEffect(() => {
    if (safePhraseIndex >= selectedPhraseCount) {
      setPhraseIndexInput("0");
    }
  }, [safePhraseIndex, selectedPhraseCount]);

  useEffect(() => {
    return () => {
      if (recordingPreviewUrl) {
        URL.revokeObjectURL(recordingPreviewUrl);
      }

      if (metronomeFrameRef.current !== null) {
        cancelAnimationFrame(metronomeFrameRef.current);
        metronomeFrameRef.current = null;
      }

      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => undefined);
        audioContextRef.current = null;
      }

      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, [recordingPreviewUrl]);

  useEffect(() => {
    let disposed = false;

    const mapOptions = (
      catalog: Array<{ song_id: string; title?: string; phrases?: number }>,
    ): ContentOption[] => {
      return catalog
        .map((item) => {
          const id = typeof item.song_id === "string" ? item.song_id.trim() : "";
          if (!id) {
            return null;
          }

          const title = typeof item.title === "string" ? item.title.trim() : "";
          const label =
            title.length > 0 && title.toLowerCase() !== id.toLowerCase()
              ? `${title} (${id})`
              : id;

          const phraseCount =
            typeof item.phrases === "number" && Number.isFinite(item.phrases) && item.phrases > 0
              ? Math.max(1, Math.floor(item.phrases))
              : null;

          return {
            id,
            label,
            phraseCount,
          };
        })
        .filter((item): item is ContentOption => item !== null)
        .sort((left, right) => left.label.localeCompare(right.label, undefined, { sensitivity: "base" }));
    };

    const loadContentCatalog = async () => {
      setCatalogLoading(true);
      setCatalogError(null);

      try {
        const [alankarCatalog, songCatalog, melodyCatalog] = await Promise.all([
          listSongs({ contentType: "alankar" }),
          listSongs({ contentType: "song" }),
          listSongs({ contentType: "melody" }),
        ]);

        const nextAlankarOptions = mapOptions(alankarCatalog);
        const nextSongOptions = mapOptions(songCatalog);
        const nextMelodyOptions = mapOptions(melodyCatalog);

        if (disposed) {
          return;
        }

        setAlankarOptions(nextAlankarOptions);
        setSongOptions(nextSongOptions);
        setMelodyOptions(nextMelodyOptions);

        setAlankarId((current) =>
          nextAlankarOptions.some((option) => option.id === current)
            ? current
            : (nextAlankarOptions[0]?.id ?? current),
        );

        setSongId((current) =>
          nextSongOptions.some((option) => option.id === current) ? current : (nextSongOptions[0]?.id ?? current),
        );

        setMelodyId((current) =>
          nextMelodyOptions.some((option) => option.id === current)
            ? current
            : (nextMelodyOptions[0]?.id ?? current),
        );

        if (
          nextAlankarOptions.length === 0 &&
          nextSongOptions.length === 0 &&
          nextMelodyOptions.length === 0
        ) {
          setCatalogError("No content IDs available in the content catalog.");
        }
      } catch (error) {
        if (disposed) {
          return;
        }

        const message = error instanceof Error ? error.message : "Failed to load content catalog.";
        setCatalogError(message);
      } finally {
        if (!disposed) {
          setCatalogLoading(false);
        }
      }
    };

    void loadContentCatalog();

    return () => {
      disposed = true;
    };
  }, []);

  useEffect(() => {
    let disposed = false;

    const loadPhraseReference = async () => {
      if (!selectedContentId) {
        setReferenceState({
          loading: false,
          error: null,
          data: null,
        });
        return;
      }

      setReferenceState({
        loading: true,
        error: null,
        data: null,
      });

      try {
        const payload = await getSongPhraseReference({
          songId: selectedContentId,
          phraseIndex: safePhraseIndex,
        });

        if (disposed) {
          return;
        }

        setReferenceState({
          loading: false,
          error: null,
          data: payload,
        });
      } catch (error) {
        if (disposed) {
          return;
        }

        const message = error instanceof Error ? error.message : "Failed to load reference notes.";
        setReferenceState({
          loading: false,
          error: message,
          data: null,
        });
      }
    };

    void loadPhraseReference();

    return () => {
      disposed = true;
    };
  }, [safePhraseIndex, selectedContentId]);

  const referenceNotes = useMemo<ReferenceNoteView[]>(() => {
    if (!referenceState.data || !Array.isArray(referenceState.data.notes)) {
      return [];
    }

    return referenceState.data.notes
      .map((entry) => {
        if (typeof entry?.note !== "string" || typeof entry?.time !== "number") {
          return null;
        }

        return {
          note: entry.note,
          time: entry.time,
        };
      })
      .filter((entry): entry is ReferenceNoteView => entry !== null);
  }, [referenceState.data]);

  const referenceTempo = useMemo(() => {
    const value = referenceState.data?.reference_tempo;
    if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
      return 60;
    }

    return Math.max(20, Math.min(240, Math.round(value)));
  }, [referenceState.data?.reference_tempo]);

  const referenceSteps = useMemo<ReferenceStepView[]>(() => {
    if (referenceNotes.length === 0) {
      return [];
    }

    const sorted = [...referenceNotes]
      .map((entry) => ({
        note: entry.note,
        time: entry.time,
        beat: (entry.time * referenceTempo) / 60,
      }))
      .sort((left, right) => left.time - right.time);

    const firstBeat = sorted[0]?.beat ?? 0;
    const normalized = sorted.map((entry) => ({
      ...entry,
      beat: Math.max(0, entry.beat - firstBeat),
    }));

    const positiveDiffs: number[] = [];
    for (let index = 0; index < normalized.length - 1; index += 1) {
      const diff = normalized[index + 1].beat - normalized[index].beat;
      if (diff > 0) {
        positiveDiffs.push(diff);
      }
    }

    const fallbackBeatDiff =
      positiveDiffs.length > 0
        ? positiveDiffs.reduce((sum, value) => sum + value, 0) / positiveDiffs.length
        : 1;

    const normalizedFallback = Math.max(0.25, fallbackBeatDiff);
    const lastBeat = normalized[normalized.length - 1]?.beat ?? 0;
    const phraseSpan = Math.max(0.5, lastBeat + normalizedFallback);

    return normalized.map((entry, index) => {
      const nextBeat = index < normalized.length - 1 ? normalized[index + 1].beat : null;
      const durationBeats =
        typeof nextBeat === "number" && nextBeat > entry.beat
          ? nextBeat - entry.beat
          : null;
      const durationMs =
        typeof durationBeats === "number"
          ? Math.max(40, Math.round((durationBeats * 60000) / safeTempo))
          : null;

      return {
        key: `${entry.note}-${entry.time}-${index}`,
        stepNumber: index + 1,
        note: entry.note,
        beat: Math.round(entry.beat * 100) / 100,
        durationBeats:
          typeof durationBeats === "number"
            ? Math.round(durationBeats * 100) / 100
            : null,
        durationMs,
        progress: Math.max(0, Math.min(1, entry.beat / phraseSpan)),
      };
    });
  }, [referenceNotes, referenceTempo, safeTempo]);

  const metronomeCycleBeats = useMemo(() => {
    if (referenceSteps.length === 0) {
      return 4;
    }

    const last = referenceSteps[referenceSteps.length - 1];
    const fallbackSpan = referenceSteps.find((step) => typeof step.durationBeats === "number")?.durationBeats ?? 1;
    const phraseSpan = last.beat + Math.max(0.25, fallbackSpan ?? 1);

    return Math.max(1, Math.round(phraseSpan * 1000) / 1000);
  }, [referenceSteps]);

  const metronomeSubdivisionBeats = useMemo(() => {
    const positiveDurations = referenceSteps
      .map((step) => step.durationBeats)
      .filter((value): value is number => typeof value === "number" && value > 0);

    if (positiveDurations.length === 0) {
      return 1;
    }

    const minDuration = Math.min(...positiveDurations);
    const quantized = Math.round(minDuration * 4) / 4;
    return Math.max(0.25, Math.min(1, quantized || 1));
  }, [referenceSteps]);

  const metronomeKhaliBeat = useMemo(() => {
    const roundedCycle = Math.round(metronomeCycleBeats);
    if (roundedCycle < 4) {
      return null;
    }

    const halfCycle = Math.floor(roundedCycle / 2);
    if (halfCycle <= 0 || halfCycle >= roundedCycle) {
      return null;
    }

    return halfCycle;
  }, [metronomeCycleBeats]);

  const metronomeKhaliProgressPercent = useMemo(() => {
    if (metronomeKhaliBeat === null || metronomeCycleBeats <= 0) {
      return null;
    }

    return Math.max(1, Math.min(99, (metronomeKhaliBeat / metronomeCycleBeats) * 100));
  }, [metronomeCycleBeats, metronomeKhaliBeat]);

  const playMetronomeClick = (kind: "sam" | "khali" | "primary" | "sub") => {
    if (
      metronomeMutedRef.current ||
      typeof window === "undefined" ||
      typeof window.AudioContext === "undefined"
    ) {
      return;
    }

    const context = audioContextRef.current ?? new window.AudioContext();
    audioContextRef.current = context;

    if (context.state === "suspended") {
      context.resume().catch(() => undefined);
    }

    const oscillator = context.createOscillator();
    const gainNode = context.createGain();
    const now = context.currentTime;

    oscillator.type = "triangle";
    const clickProfile =
      kind === "sam"
        ? { frequency: 1480, gain: 0.26, decay: 0.1 }
        : kind === "khali"
          ? { frequency: 620, gain: 0.08, decay: 0.07 }
          : kind === "primary"
            ? { frequency: 1040, gain: 0.16, decay: 0.08 }
            : { frequency: 760, gain: 0.11, decay: 0.06 };

    oscillator.frequency.value = clickProfile.frequency;

    gainNode.gain.setValueAtTime(0.0001, now);
    gainNode.gain.linearRampToValueAtTime(clickProfile.gain, now + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, now + clickProfile.decay);

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    oscillator.start(now);
    oscillator.stop(now + clickProfile.decay + 0.01);
  };

  useEffect(() => {
    if (!metronomeRunning) {
      if (metronomeFrameRef.current !== null) {
        cancelAnimationFrame(metronomeFrameRef.current);
        metronomeFrameRef.current = null;
      }
      return;
    }

    if (referenceSteps.length === 0) {
      setMetronomeRunning(false);
      return;
    }

    const loopSubdivisionBeats = isCountInActive ? 1 : metronomeSubdivisionBeats;
    const loopCycleBeats = isCountInActive ? COUNT_IN_BEATS : metronomeCycleBeats;
    const beatDurationMs = 60000 / safeTempo;
    const subdivisionMs = Math.max(40, beatDurationMs * loopSubdivisionBeats);
    const cycleDurationMs = Math.max(1, beatDurationMs * loopCycleBeats);
    const startTime = typeof performance !== "undefined" ? performance.now() : Date.now();
    let lastTick = 0;
    let lastVisualUpdate = startTime;

    setMetronomeTickCount(0);
    setMetronomePositionBeats(0);
    playMetronomeClick("sam");

    const runFrame = () => {
      const now = typeof performance !== "undefined" ? performance.now() : Date.now();
      const elapsedMs = Math.max(0, now - startTime);
      const elapsedTicks = Math.floor(elapsedMs / subdivisionMs);
      const hasAdvancedTicks = elapsedTicks > lastTick;

      if (hasAdvancedTicks) {
        // Cap catch-up replay so tab sleep/background resume does not flood queued clicks.
        const replayCount = Math.min(8, elapsedTicks - lastTick);
        const replayStart = elapsedTicks - replayCount + 1;

        for (let nextTick = replayStart; nextTick <= elapsedTicks; nextTick += 1) {
          const beat = Number(((nextTick * loopSubdivisionBeats) % loopCycleBeats).toFixed(4));
          const isCycleStart = beat < loopSubdivisionBeats / 2;
          const isPrimaryBeat = Math.abs(beat - Math.round(beat)) < 0.001;
          const beatIndex = Math.round(beat);
          const isKhaliBeat =
            !isCountInActive && metronomeKhaliBeat !== null && isPrimaryBeat && beatIndex === metronomeKhaliBeat;

          playMetronomeClick(
            isCycleStart
              ? "sam"
              : isCountInActive
                ? "primary"
                : isKhaliBeat
                  ? "khali"
                  : isPrimaryBeat
                    ? "primary"
                    : "sub",
          );
        }

        lastTick = elapsedTicks;
        setMetronomeTickCount(elapsedTicks);
      }

      if (now - lastVisualUpdate >= 32 || hasAdvancedTicks) {
        const cycleElapsedMs = elapsedMs % cycleDurationMs;
        const beatPosition = Number((cycleElapsedMs / beatDurationMs).toFixed(4));
        setMetronomePositionBeats(beatPosition >= loopCycleBeats ? 0 : beatPosition);
        lastVisualUpdate = now;
      }

      metronomeFrameRef.current = requestAnimationFrame(runFrame);
    };

    metronomeFrameRef.current = requestAnimationFrame(runFrame);

    return () => {
      if (metronomeFrameRef.current !== null) {
        cancelAnimationFrame(metronomeFrameRef.current);
        metronomeFrameRef.current = null;
      }
    };
  }, [
    isCountInActive,
    metronomeCycleBeats,
    metronomeKhaliBeat,
    metronomeRunning,
    metronomeSubdivisionBeats,
    referenceSteps.length,
    safeTempo,
  ]);

  const metronomeActiveStepIndex = useMemo(() => {
    if (!metronomeRunning || isCountInActive || referenceSteps.length === 0) {
      return -1;
    }

    const position = metronomePositionBeats;
    let active = 0;

    for (let index = 0; index < referenceSteps.length; index += 1) {
      const current = referenceSteps[index];
      const next = referenceSteps[index + 1];
      const start = current.beat;
      const end = next ? next.beat : metronomeCycleBeats;

      if (position >= start && position < end) {
        return index;
      }

      if (position >= start) {
        active = index;
      }
    }

    return active;
  }, [isCountInActive, metronomeCycleBeats, metronomePositionBeats, metronomeRunning, referenceSteps]);

  const metronomeDisplayCycleBeats = useMemo(() => {
    return isCountInActive ? COUNT_IN_BEATS : metronomeCycleBeats;
  }, [isCountInActive, metronomeCycleBeats]);

  const metronomeDisplaySubdivisionBeats = useMemo(() => {
    return isCountInActive ? 1 : metronomeSubdivisionBeats;
  }, [isCountInActive, metronomeSubdivisionBeats]);

  const metronomeProgressPercent = useMemo(() => {
    if (metronomeDisplayCycleBeats <= 0) {
      return 0;
    }

    return Math.max(0, Math.min(100, (metronomePositionBeats / metronomeDisplayCycleBeats) * 100));
  }, [metronomeDisplayCycleBeats, metronomePositionBeats]);

  const metronomeBeatLabel = useMemo(() => {
    const beatValue = metronomePositionBeats + 1;
    const decimalPlaces = metronomeDisplaySubdivisionBeats < 1 ? 2 : 0;
    return beatValue.toFixed(decimalPlaces);
  }, [metronomeDisplaySubdivisionBeats, metronomePositionBeats]);

  const metronomeDisplayStepIndex = useMemo(() => {
    if (referenceSteps.length === 0) {
      return -1;
    }

    return metronomeActiveStepIndex >= 0 ? metronomeActiveStepIndex : 0;
  }, [metronomeActiveStepIndex, referenceSteps.length]);

  const metronomeCurrentStep = useMemo(() => {
    if (metronomeDisplayStepIndex < 0) {
      return null;
    }

    return referenceSteps[metronomeDisplayStepIndex] ?? null;
  }, [metronomeDisplayStepIndex, referenceSteps]);

  const metronomeNextStepIndex = useMemo(() => {
    if (metronomeDisplayStepIndex < 0 || referenceSteps.length === 0) {
      return -1;
    }

    return (metronomeDisplayStepIndex + 1) % referenceSteps.length;
  }, [metronomeDisplayStepIndex, referenceSteps.length]);

  const metronomeNextStep = useMemo(() => {
    if (metronomeNextStepIndex < 0) {
      return null;
    }

    return referenceSteps[metronomeNextStepIndex] ?? null;
  }, [metronomeNextStepIndex, referenceSteps]);

  const metronomeBeatsUntilNext = useMemo(() => {
    if (!metronomeCurrentStep) {
      return null;
    }

    if (!metronomeRunning) {
      return metronomeCurrentStep.durationBeats;
    }

    if (metronomeDisplayStepIndex < 0) {
      return null;
    }

    const nextBeatBoundary =
      metronomeDisplayStepIndex < referenceSteps.length - 1
        ? referenceSteps[metronomeDisplayStepIndex + 1].beat
        : metronomeCycleBeats;

    let delta = nextBeatBoundary - metronomePositionBeats;
    if (delta <= 0) {
      delta += metronomeCycleBeats;
    }

    return Math.round(Math.max(0, delta) * 100) / 100;
  }, [
    metronomeCurrentStep,
    metronomeCycleBeats,
    metronomeDisplayStepIndex,
    metronomePositionBeats,
    metronomeRunning,
    referenceSteps,
  ]);

  useEffect(() => {
    if (!isCountInActive) {
      return;
    }

    const elapsedBeats = metronomeTickCount;
    const remainingBeats = Math.max(0, COUNT_IN_BEATS - elapsedBeats);
    const nextRemaining = Math.max(0, Math.ceil(remainingBeats));
    setCountInRemaining((current) => (current === nextRemaining ? current : nextRemaining));

    if (elapsedBeats + 0.001 < COUNT_IN_BEATS) {
      return;
    }

    const recorder = mediaRecorderRef.current;
    setIsCountInActive(false);
    setCountInRemaining(0);
    setMetronomeTickCount(0);
    setMetronomePositionBeats(0);
    setMetronomeRunning(false);

    const startTakeAtSam = () => {
      setMetronomeRunning(true);
      if (recorder && recorder.state === "inactive") {
        recorder.start();
        setRecording(true);
      }
    };

    if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
      window.requestAnimationFrame(startTakeAtSam);
      return;
    }

    startTakeAtSam();
  }, [isCountInActive, metronomeTickCount]);

  const referenceEmptyMessage = useMemo(() => {
    if (!selectedContentId) {
      return "Select content to load phrase reference notes.";
    }

    if (!referenceState.loading && !referenceState.error && referenceNotes.length === 0) {
      return "No reference notes available for this phrase.";
    }

    return undefined;
  }, [referenceNotes.length, referenceState.error, referenceState.loading, selectedContentId]);

  const hasRecordedClip =
    recordedWavFile !== null || recordedRawFile !== null || recordingPreviewUrl !== null;

  const clearRecordedAudioState = () => {
    setRecordedWavFile(null);
    setRecordedRawFile(null);
    setRecordingPreviewUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }

      return null;
    });
  };

  const onClearRecording = () => {
    if (recording || isCountInActive) {
      return;
    }

    clearRecordedAudioState();
    setRecordingError(null);
  };

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setAudioFile(event.target.files?.[0] ?? null);
    setRecordingError(null);
  };

  const startRecording = async () => {
    setRecordingError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const preferredMime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType: preferredMime });
      mediaRecorderRef.current = recorder;
      recordedChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        try {
          const sourceBlob = new Blob(recordedChunksRef.current, {
            type: recorder.mimeType || "audio/webm",
          });
          const rawExt = (recorder.mimeType || "audio/webm").includes("ogg") ? "ogg" : "webm";
          const rawFile = new File([sourceBlob], `live-recording.${rawExt}`, {
            type: recorder.mimeType || "audio/webm",
          });

          setRecordedRawFile(rawFile);

          try {
            const wavFile = await convertBlobToWavFile(sourceBlob, "live-recording.wav");
            setRecordedWavFile(wavFile);
            setRecordingPreviewUrl((current) => {
              if (current) {
                URL.revokeObjectURL(current);
              }

              return URL.createObjectURL(wavFile);
            });
          } catch {
            setRecordedWavFile(null);
            setRecordingPreviewUrl((current) => {
              if (current) {
                URL.revokeObjectURL(current);
              }

              return URL.createObjectURL(rawFile);
            });

            setRecordingError(
              "Browser WAV conversion failed. Using raw recording file; backend will convert/process it.",
            );
          }

          setAudioFile(null);
        } catch (error) {
          const message = error instanceof Error ? error.message : "Failed to process recorded audio.";
          setRecordingError(message);
        } finally {
          setRecording(false);
          setIsCountInActive(false);
          setCountInRemaining(0);
          mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
          mediaStreamRef.current = null;
        }
      };

      clearRecordedAudioState();
      setAudioFile(null);

      if (referenceSteps.length === 0) {
        recorder.start();
        setRecording(true);
        return;
      }

      setIsCountInActive(true);
      setCountInRemaining(COUNT_IN_BEATS);
      setMetronomeTickCount(0);
      setMetronomePositionBeats(0);
      setMetronomeRunning(false);

      if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
        window.requestAnimationFrame(() => {
          setMetronomeRunning(true);
        });
      } else {
        setMetronomeRunning(true);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Microphone access failed.";
      setRecordingError(message);
    }
  };

  const stopRecording = () => {
    if (isCountInActive) {
      setIsCountInActive(false);
      setCountInRemaining(0);
      setMetronomeRunning(false);
      setMetronomeTickCount(0);
      setMetronomePositionBeats(0);
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
      mediaRecorderRef.current = null;
      recordedChunksRef.current = [];
      return;
    }

    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== "recording") {
      return;
    }

    mediaRecorderRef.current.stop();
    setRecording(false);
    setMetronomeRunning(false);
  };

  const onSubmitPractice = async () => {
    const selectedFile = inputMethod === "record" ? (recordedWavFile ?? recordedRawFile) : audioFile;

    if (!selectedFile) {
      setRecordingError("Provide an upload file or record live audio before submitting.");
      return;
    }

    if (mode === "alankar") {
      try {
        await submitAlankar({
          userId: safeUserId,
          alankarId: alankarId.trim(),
          phraseIndex: safePhraseIndex,
          tempo: safeTempo,
          audioFile: selectedFile,
        });
        emitPracticeRefreshSignal(safeUserId);
      } catch {
        return;
      }
      return;
    }

    if (mode === "song") {
      try {
        await submitSong({
          userId: safeUserId,
          songId: songId.trim(),
          phraseIndex: safePhraseIndex,
          tempo: safeTempo,
          audioFile: selectedFile,
        });
        emitPracticeRefreshSignal(safeUserId);
      } catch {
        return;
      }
      return;
    }

    try {
      await submitMelody({
        userId: safeUserId,
        melodyId: melodyId.trim(),
        phraseIndex: safePhraseIndex,
        tempo: safeTempo,
        audioFile: selectedFile,
      });
      emitPracticeRefreshSignal(safeUserId);
    } catch {
      return;
    }
  };

  const onLoadCurriculum = async () => {
    try {
      await loadCurriculum(safeUserId);
    } catch {
      return;
    }
  };

  const onTempoBlur = () => {
    setTempoInput(String(safeTempo));
  };

  const curriculumSnapshot = curriculumState.data?.data ?? null;
  const curriculumSnapshotEmptyMessage =
    curriculumState.data?.empty.isEmpty
      ? curriculumState.data.empty.message ?? undefined
      : undefined;

  return (
    <div className="container">
      <h1>Practice Studio</h1>
      <p className="muted">Base URL: {API_BASE_URL}</p>

      <section className="card practice-control-card">
        <div className="practice-controls-grid">
          <div className="practice-control-item user-id-inline">
            <span className="user-id-inline-label">User ID:</span>{" "}
            <span className="user-id-inline-value">{userId}</span>
          </div>

          <label className="practice-control-item">
            Mode
            <select
              value={mode}
              onChange={(event) => setMode(event.target.value as "alankar" | "song" | "melody")}
            >
              <option value="alankar">Alankar Practice</option>
              <option value="song">Song Practice</option>
              <option value="melody">Melody Practice</option>
            </select>
          </label>

          {mode === "alankar" ? (
            <label className="practice-control-item practice-content-id-control">
              Alankar ID
              <select
                value={alankarOptions.some((option) => option.id === alankarId) ? alankarId : ""}
                onChange={(event) => setAlankarId(event.target.value)}
                disabled={catalogLoading || alankarOptions.length === 0}
              >
                {catalogLoading && <option value="">Loading content...</option>}
                {!catalogLoading && alankarOptions.length === 0 && <option value="">No alankars available</option>}
                {alankarOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          ) : mode === "song" ? (
            <label className="practice-control-item practice-content-id-control">
              Song ID
              <select
                value={songOptions.some((option) => option.id === songId) ? songId : ""}
                onChange={(event) => setSongId(event.target.value)}
                disabled={catalogLoading || songOptions.length === 0}
              >
                {catalogLoading && <option value="">Loading content...</option>}
                {!catalogLoading && songOptions.length === 0 && <option value="">No songs available</option>}
                {songOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <label className="practice-control-item practice-content-id-control">
              Melody ID
              <select
                value={melodyOptions.some((option) => option.id === melodyId) ? melodyId : ""}
                onChange={(event) => setMelodyId(event.target.value)}
                disabled={catalogLoading || melodyOptions.length === 0}
              >
                {catalogLoading && <option value="">Loading content...</option>}
                {!catalogLoading && melodyOptions.length === 0 && <option value="">No melodies available</option>}
                {melodyOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          )}

          <label className="practice-control-item">
            Phrase
            <select
              value={String(safePhraseIndex)}
              onChange={(event) => {
                const parsed = Number(event.target.value);
                const nextValue = Number.isFinite(parsed) ? Math.max(0, Math.floor(parsed)) : 0;
                setPhraseIndexInput(String(nextValue));
              }}
              disabled={catalogLoading || phraseOptions.length === 0}
            >
              {phraseOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="practice-control-item">
            Tempo
            <input
              type="number"
              min={20}
              max={220}
              value={tempoInput}
              onChange={(event) => setTempoInput(event.target.value)}
              onBlur={onTempoBlur}
            />
          </label>

          <label className="practice-control-item">
            Input Method
            <select
              value={inputMethod}
              onChange={(event) => {
                setInputMethod(event.target.value as "upload" | "record");
                setRecordingError(null);
              }}
            >
              <option value="upload">Upload audio file</option>
              <option value="record">Record live audio</option>
            </select>
          </label>
        </div>

        {catalogError && <p className="error">{catalogError}</p>}

        <section className="reference-notes-panel">
          <h3>{mode === "alankar" ? "Alankar Step Guide" : "Phrase Step Guide"}</h3>
          <p className="muted">Tempo-synced steps update as BPM changes. Raw timestamps are hidden for cleaner practice flow.</p>
          <p className="muted reference-note-meta">
            {selectedContentLabel}: <strong>{selectedContentId || "-"}</strong> | Phrase Index: <strong>{safePhraseIndex}</strong>
            {referenceState.data?.phrase_count ? (
              <>
                {" "}| Available Phrases: <strong>{referenceState.data.phrase_count}</strong>
              </>
            ) : null}
          </p>

          <ScreenState
            loading={referenceState.loading}
            error={referenceState.error}
            emptyMessage={referenceEmptyMessage}
          />

          {!referenceState.loading && !referenceState.error && referenceSteps.length > 0 && (
            <>
              <div className="reference-pill-row">
                <span className="reference-pill">Reference Tempo {referenceTempo} BPM</span>
                <span className="reference-pill strong">Practice Tempo {safeTempo} BPM</span>
                <span className="reference-pill">{referenceSteps.length} Steps</span>
              </div>

              <section className="metronome-panel">
                <div className="metronome-visual">
                  <div className={metronomeRunning ? "metronome-pulse active" : "metronome-pulse"}>
                    <span className="metronome-beat-label">{metronomeBeatLabel}</span>
                    <span className="metronome-beat-caption">Beat</span>
                  </div>
                </div>

                <div className="metronome-details">
                  <p className="muted">
                    Cycle: {formatBeatNumber(metronomeDisplayCycleBeats)} beats | Subdivision: {formatBeatNumber(metronomeDisplaySubdivisionBeats)} beat
                    {metronomeRunning ? ` | Tick ${metronomeTickCount}` : ""}
                  </p>

                  <div className="metronome-accent-row">
                    <span className="metronome-accent-chip sam">Sam: Beat 1</span>
                    {!isCountInActive && metronomeKhaliBeat !== null ? (
                      <span className="metronome-accent-chip khali">
                        Khali: Beat {metronomeKhaliBeat + 1}
                      </span>
                    ) : isCountInActive ? (
                      <span className="metronome-accent-chip none">Khali: Starts after count-in</span>
                    ) : (
                      <span className="metronome-accent-chip none">Khali: Auto-off (short cycle)</span>
                    )}
                    {isCountInActive && (
                      <span className="metronome-accent-chip count-in">
                        Count-in: {Math.max(1, countInRemaining)}
                      </span>
                    )}
                  </div>

                  <section className="mini-metronome-panel" aria-live="polite">
                    <div className="mini-metronome-header">
                      <span className="mini-metronome-title">
                        Mini {mode === "alankar" ? "Alankar" : "Phrase"} Metronome
                      </span>
                      <span className={isCountInActive ? "mini-metronome-step-count count-in" : "mini-metronome-step-count"}>
                        {isCountInActive
                          ? `Recording in ${Math.max(1, countInRemaining)} beat${countInRemaining === 1 ? "" : "s"}`
                          : metronomeCurrentStep
                            ? `Step ${metronomeCurrentStep.stepNumber}/${referenceSteps.length}`
                            : `Step --/${referenceSteps.length}`}
                      </span>
                    </div>

                    <div className="mini-metronome-now-next">
                      <article className="mini-note-card">
                        <span className="mini-note-label">Now</span>
                        <strong>{metronomeCurrentStep?.note ?? "--"}</strong>
                      </article>

                      <article className="mini-note-card">
                        <span className="mini-note-label">Next</span>
                        <strong>{metronomeNextStep?.note ?? "--"}</strong>
                        {typeof metronomeBeatsUntilNext === "number" && (
                          <small>
                            in {formatBeatNumber(metronomeBeatsUntilNext)} beat
                            {metronomeBeatsUntilNext > 1 ? "s" : ""}
                          </small>
                        )}
                      </article>
                    </div>

                    <div
                      className="mini-metronome-note-rail"
                      role="list"
                      aria-label="Mini metronome aligned with alankar reference notes"
                    >
                      {referenceSteps.map((step, index) => {
                        const isActive = !isCountInActive && metronomeRunning && index === metronomeDisplayStepIndex;
                        const isUpcoming = !isCountInActive && metronomeRunning && index === metronomeNextStepIndex;

                        return (
                          <span
                            key={`${step.key}-mini`}
                            role="listitem"
                            className={
                              isActive
                                ? "mini-metronome-note active"
                                : isUpcoming
                                  ? "mini-metronome-note upcoming"
                                  : "mini-metronome-note"
                            }
                            title={`Step ${step.stepNumber}: ${step.note}`}
                          >
                            {step.note}
                          </span>
                        );
                      })}
                    </div>
                  </section>

                  <div className="metronome-track" aria-hidden="true">
                    <div className="metronome-track-fill" style={{ width: `${metronomeProgressPercent}%` }} />
                    <span className="metronome-cycle-marker sam" style={{ left: "0%" }} title="Sam accent: Beat 1" />
                    {!isCountInActive && typeof metronomeKhaliProgressPercent === "number" && (
                      <span
                        className="metronome-cycle-marker khali"
                        style={{ left: `${metronomeKhaliProgressPercent}%` }}
                        title={`Khali accent: Beat ${metronomeKhaliBeat !== null ? metronomeKhaliBeat + 1 : "-"}`}
                      />
                    )}
                    {referenceSteps.map((step) => (
                      <span
                        key={`${step.key}-marker`}
                        className="metronome-step-marker"
                        style={{ left: `${Math.max(1, Math.min(99, step.progress * 100))}%` }}
                        title={`Step ${step.stepNumber}: ${step.note}`}
                      />
                    ))}
                  </div>

                  <div className="row metronome-controls">
                    <button onClick={() => setMetronomeRunning((running) => !running)} disabled={isCountInActive}>
                      {isCountInActive ? "Count-In Running" : metronomeRunning ? "Stop Metronome" : "Start Metronome"}
                    </button>
                    <button onClick={() => setMetronomeMuted((muted) => !muted)}>
                      {metronomeMuted ? "Unmute Click" : "Mute Click"}
                    </button>
                    <button
                      disabled={isCountInActive}
                      onClick={() => {
                        setMetronomeRunning(false);
                        setMetronomeTickCount(0);
                        setMetronomePositionBeats(0);
                      }}
                    >
                      Reset Cycle
                    </button>
                  </div>
                </div>
              </section>

              <div className="reference-note-strip" role="list" aria-label="Reference notes">
                {referenceSteps.map((entry, index) => {
                  const beatDecimals = entry.beat % 1 === 0 ? 0 : 2;
                  const durationBeats =
                    typeof entry.durationBeats === "number"
                      ? entry.durationBeats.toFixed(entry.durationBeats % 1 === 0 ? 0 : 2)
                      : null;

                  return (
                    <div
                      className={
                        metronomeRunning && metronomeActiveStepIndex === index
                          ? "reference-note-chip active"
                          : "reference-note-chip"
                      }
                      role="listitem"
                      key={entry.key}
                    >
                      <span className="reference-step-index">Step {entry.stepNumber}</span>
                      <span className="reference-note-name">{entry.note}</span>
                      <span className="reference-note-time">Beat {entry.beat.toFixed(beatDecimals)}</span>
                      <span className="reference-note-duration">
                        {typeof entry.durationMs === "number" && durationBeats
                          ? `Hold ${entry.durationMs} ms (${durationBeats} beat)`
                          : "Phrase end"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </section>

        {inputMethod === "upload" ? (
          <label>
            Audio File (wav/mp3/m4a/ogg/flac)
            <input
              type="file"
              accept="audio/*,.wav,.mp3,.mpeg,.m4a,.aac,.ogg,.flac,.webm"
              onChange={onFileChange}
            />
          </label>
        ) : (
          <section className="record-box">
            <p className="muted">Recorded audio is converted to WAV before submission.</p>
            {isCountInActive && (
              <p className="muted recording-count-in">
                Count-in running. Recording starts in {Math.max(1, countInRemaining)} beat
                {countInRemaining === 1 ? "" : "s"}.
              </p>
            )}
            <div className="row">
              <button onClick={startRecording} disabled={recording || isCountInActive}>Start Recording</button>
              <button onClick={stopRecording} disabled={!recording && !isCountInActive}>
                {isCountInActive ? "Cancel Count-In" : "Stop Recording"}
              </button>
              <button onClick={onClearRecording} disabled={recording || isCountInActive || !hasRecordedClip}>
                Clear Recording
              </button>
            </div>
            {isCountInActive && <p className="muted">Metronome count-in in progress...</p>}
            {recording && <p className="muted">Recording in progress...</p>}
            {recordedWavFile && <p className="muted">Ready (WAV): {recordedWavFile.name}</p>}
            {!recordedWavFile && recordedRawFile && (
              <p className="muted">Ready (raw): {recordedRawFile.name}</p>
            )}
            {recordingPreviewUrl && <audio controls src={recordingPreviewUrl} className="audio-preview" />}
          </section>
        )}

        {recordingError && <p className="error">{recordingError}</p>}

        <div className="row">
          <button onClick={onSubmitPractice}>Submit Practice</button>
          <button onClick={onLoadCurriculum}>Refresh Curriculum Snapshot</button>
        </div>
      </section>

      <section className="grid">
        <article className="result-card studio-card">
          <h3>Practice Studio</h3>
          <ScreenState
            loading={practiceState.loading}
            error={practiceState.error}
            emptyMessage={
              practiceState.data?.empty.isEmpty ? practiceState.data.empty.message ?? undefined : undefined
            }
          />

          {!practiceState.loading && !practiceState.error && practiceState.data && !practiceState.data.empty.isEmpty && (
            <PracticeStudioPanel userId={safeUserId} practice={practiceState.data.data} />
          )}
        </article>

        <article className="result-card curriculum-snapshot-card">
          <h3>Curriculum Snapshot</h3>

          <ScreenState
            loading={curriculumState.loading}
            error={curriculumState.error}
            emptyMessage={curriculumSnapshotEmptyMessage ?? "Load snapshot to view curriculum guidance."}
          />

          {!curriculumState.loading &&
            !curriculumState.error &&
            curriculumSnapshot &&
            !curriculumState.data?.empty.isEmpty && (
              <>
                <div className="curriculum-snapshot-grid">
                  <article className="curriculum-snapshot-stat">
                    <h4>Current Level</h4>
                    <p>{toTitleToken(curriculumSnapshot.currentLevel || "beginner")}</p>
                  </article>

                  <article className="curriculum-snapshot-stat">
                    <h4>Composite Score</h4>
                    <p>{formatScorePercent(curriculumSnapshot.compositeScore)}</p>
                  </article>

                  <article className="curriculum-snapshot-stat">
                    <h4>Unlocked</h4>
                    <p>{curriculumSnapshot.unlockedContent.length}</p>
                  </article>

                  <article className="curriculum-snapshot-stat">
                    <h4>Mastered</h4>
                    <p>{curriculumSnapshot.masteredContent.length}</p>
                  </article>
                </div>

                <div className="curriculum-snapshot-focus">
                  <p>
                    <strong>Recommended:</strong> {curriculumSnapshot.recommendedContent ?? "N/A"}
                  </p>
                  <p>
                    <strong>Next Goal:</strong> {curriculumSnapshot.nextGoal ?? "N/A"}
                  </p>
                  <p>
                    <strong>Reason:</strong> {curriculumSnapshot.reason ?? "No recommendation reason available yet."}
                  </p>
                </div>

                <div className="curriculum-content-groups">
                  <section className="curriculum-content-group">
                    <h4>Unlocked Content</h4>
                    {curriculumSnapshot.unlockedContent.length === 0 ? (
                      <p className="muted">No unlocked content.</p>
                    ) : (
                      <div className="curriculum-content-pill-row">
                        {curriculumSnapshot.unlockedContent.map((item, index) => (
                          <span key={`unlocked-${item}-${index}`} className="curriculum-content-pill unlocked">
                            {item}
                          </span>
                        ))}
                      </div>
                    )}
                  </section>

                  <section className="curriculum-content-group">
                    <h4>Mastered Content</h4>
                    {curriculumSnapshot.masteredContent.length === 0 ? (
                      <p className="muted">No mastered content yet.</p>
                    ) : (
                      <div className="curriculum-content-pill-row">
                        {curriculumSnapshot.masteredContent.map((item, index) => (
                          <span key={`mastered-${item}-${index}`} className="curriculum-content-pill mastered">
                            {item}
                          </span>
                        ))}
                      </div>
                    )}
                  </section>

                  <section className="curriculum-content-group">
                    <h4>Locked Content</h4>
                    {curriculumSnapshot.lockedContent.length === 0 ? (
                      <p className="muted">No locked content.</p>
                    ) : (
                      <div className="curriculum-content-pill-row">
                        {curriculumSnapshot.lockedContent.map((item, index) => (
                          <span key={`locked-${item}-${index}`} className="curriculum-content-pill locked">
                            {item}
                          </span>
                        ))}
                      </div>
                    )}
                  </section>
                </div>
              </>
            )}
        </article>
      </section>
    </div>
  );
}
