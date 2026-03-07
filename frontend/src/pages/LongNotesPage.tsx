import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getPreferredUserId } from "../utils/userIdentity";

const G_STRING_NOTE = "G3";
const G_STRING_INDIAN_NOTE = "Mandra Pa";
const G_STRING_FREQUENCY_HZ = 196;
const METER_RANGE_CENTS = 50;
const IN_TUNE_THRESHOLD_CENTS = 10;
const MIN_SIGNAL_RMS = 0.01;
const SA_REFERENCE_HZ = 523.25;
const WESTERN_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

const INDIAN_NOTE_NAMES = [
  "Sa",
  "Komal Re",
  "Re",
  "Komal Ga",
  "Ga",
  "Ma",
  "Tivra Ma",
  "Pa",
  "Komal Dha",
  "Dha",
  "Komal Ni",
  "Ni",
];

type DetectionSnapshot = {
  frequencyHz: number | null;
  centsOffset: number | null;
  signalRms: number;
};

type NoteDisplayMode = "indian" | "western";

const formatSeconds = (value: number): string => {
  return `${value.toFixed(1)}s`;
};

const clamp = (value: number, min: number, max: number): number => {
  return Math.min(max, Math.max(min, value));
};

const computeRms = (buffer: Float32Array): number => {
  let sumSquares = 0;
  for (let i = 0; i < buffer.length; i += 1) {
    const sample = buffer[i] ?? 0;
    sumSquares += sample * sample;
  }

  return Math.sqrt(sumSquares / buffer.length);
};

const estimateFrequency = (buffer: Float32Array, sampleRate: number): number | null => {
  const minHz = 70;
  const maxHz = 1100;
  const minLag = Math.floor(sampleRate / maxHz);
  const maxLag = Math.floor(sampleRate / minHz);

  if (minLag < 1 || maxLag <= minLag || maxLag >= buffer.length) {
    return null;
  }

  let bestLag = -1;
  let bestCorrelation = 0;

  for (let lag = minLag; lag <= maxLag; lag += 1) {
    let corr = 0;
    for (let i = 0; i < buffer.length - lag; i += 1) {
      corr += buffer[i] * buffer[i + lag];
    }

    if (corr > bestCorrelation) {
      bestCorrelation = corr;
      bestLag = lag;
    }
  }

  if (bestLag === -1) {
    return null;
  }

  const leftLag = bestLag - 1;
  const rightLag = bestLag + 1;

  let leftCorr = bestCorrelation;
  let rightCorr = bestCorrelation;

  if (leftLag >= minLag) {
    let corr = 0;
    for (let i = 0; i < buffer.length - leftLag; i += 1) {
      corr += buffer[i] * buffer[i + leftLag];
    }
    leftCorr = corr;
  }

  if (rightLag <= maxLag) {
    let corr = 0;
    for (let i = 0; i < buffer.length - rightLag; i += 1) {
      corr += buffer[i] * buffer[i + rightLag];
    }
    rightCorr = corr;
  }

  const denominator = (2 * bestCorrelation) - leftCorr - rightCorr;
  const shift = denominator === 0 ? 0 : (rightCorr - leftCorr) / (2 * denominator);
  const refinedLag = bestLag + shift;

  if (!Number.isFinite(refinedLag) || refinedLag <= 0) {
    return null;
  }

  const frequency = sampleRate / refinedLag;
  if (!Number.isFinite(frequency) || frequency <= 0) {
    return null;
  }

  return frequency;
};

const getNearestIndianNoteName = (frequencyHz: number): string => {
  if (!Number.isFinite(frequencyHz) || frequencyHz <= 0) {
    return "-";
  }

  const semitonesFromSa = 12 * Math.log2(frequencyHz / SA_REFERENCE_HZ);
  const nearestSemitone = Math.round(semitonesFromSa);
  const noteIndex = ((nearestSemitone % 12) + 12) % 12;
  const octaveNumber = Math.floor(nearestSemitone / 12);

  let octavePrefix = "Madhya";
  if (octaveNumber <= -1) {
    octavePrefix = "Mandra";
  } else if (octaveNumber >= 1) {
    octavePrefix = "Taar";
  }

  return `${octavePrefix} ${INDIAN_NOTE_NAMES[noteIndex]}`;
};

const getNearestWesternNoteName = (frequencyHz: number): string => {
  if (!Number.isFinite(frequencyHz) || frequencyHz <= 0) {
    return "-";
  }

  const midi = Math.round((12 * Math.log2(frequencyHz / 440)) + 69);
  const pitchClass = ((midi % 12) + 12) % 12;
  const octave = Math.floor(midi / 12) - 1;
  return `${WESTERN_NOTE_NAMES[pitchClass]}${octave}`;
};

const getCentsOffset = (frequencyHz: number, referenceHz: number): number => {
  return 1200 * Math.log2(frequencyHz / referenceHz);
};

export default function LongNotesPage() {
  const userId = useMemo(() => getPreferredUserId(), []);

  const [isListening, setIsListening] = useState(false);
  const [noteDisplayMode, setNoteDisplayMode] = useState<NoteDisplayMode>("indian");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<DetectionSnapshot>({
    frequencyHz: null,
    centsOffset: null,
    signalRms: 0,
  });
  const [holdSeconds, setHoldSeconds] = useState(0);
  const [bestHoldSeconds, setBestHoldSeconds] = useState(0);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const lastFrameTimeRef = useRef<number | null>(null);
  const holdSecondsRef = useRef(0);

  const stopListening = useCallback(() => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => undefined);
      audioContextRef.current = null;
    }

    lastFrameTimeRef.current = null;
    setIsListening(false);
  }, []);

  const resetHoldStats = useCallback(() => {
    holdSecondsRef.current = 0;
    setHoldSeconds(0);
    setBestHoldSeconds(0);
  }, []);

  const startListening = useCallback(async () => {
    if (isListening) {
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setErrorMessage("Microphone capture is not available in this browser.");
      return;
    }

    setErrorMessage(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });

      streamRef.current = stream;

      const context = new window.AudioContext();
      audioContextRef.current = context;

      const source = context.createMediaStreamSource(stream);
      sourceRef.current = source;

      const analyser = context.createAnalyser();
      analyser.fftSize = 4096;
      analyser.smoothingTimeConstant = 0.04;
      analyserRef.current = analyser;

      source.connect(analyser);

      const dataBuffer = new Float32Array(analyser.fftSize);
      setIsListening(true);

      const tick = (timeMs: number) => {
        const analyserNode = analyserRef.current;

        if (!analyserNode) {
          return;
        }

        analyserNode.getFloatTimeDomainData(dataBuffer);

        const rms = computeRms(dataBuffer);
        const frameDeltaSeconds = lastFrameTimeRef.current === null
          ? 0
          : Math.max(0, (timeMs - lastFrameTimeRef.current) / 1000);
        lastFrameTimeRef.current = timeMs;

        if (rms < MIN_SIGNAL_RMS) {
          holdSecondsRef.current = 0;
          setHoldSeconds(0);
          setSnapshot((previous) => ({
            ...previous,
            frequencyHz: null,
            centsOffset: null,
            signalRms: rms,
          }));

          animationFrameRef.current = requestAnimationFrame(tick);
          return;
        }

        const frequencyHz = estimateFrequency(dataBuffer, audioContextRef.current?.sampleRate ?? 44100);

        if (!frequencyHz) {
          holdSecondsRef.current = 0;
          setHoldSeconds(0);
          setSnapshot((previous) => ({
            ...previous,
            frequencyHz: null,
            centsOffset: null,
            signalRms: rms,
          }));

          animationFrameRef.current = requestAnimationFrame(tick);
          return;
        }

        const centsOffset = getCentsOffset(frequencyHz, G_STRING_FREQUENCY_HZ);
        const inTuneNow = Math.abs(centsOffset) <= IN_TUNE_THRESHOLD_CENTS;

        if (inTuneNow) {
          holdSecondsRef.current += frameDeltaSeconds;
        } else {
          holdSecondsRef.current = 0;
        }

        const nextHoldSeconds = holdSecondsRef.current;

        setHoldSeconds(nextHoldSeconds);
        setBestHoldSeconds((previous) => Math.max(previous, nextHoldSeconds));
        setSnapshot({
          frequencyHz,
          centsOffset,
          signalRms: rms,
        });

        animationFrameRef.current = requestAnimationFrame(tick);
      };

      animationFrameRef.current = requestAnimationFrame(tick);
    } catch (error) {
      stopListening();
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to start microphone capture. Please allow mic access.",
      );
    }
  }, [isListening, stopListening]);

  useEffect(() => {
    return () => {
      stopListening();
    };
  }, [stopListening]);

  const centsOffset = snapshot.centsOffset;
  const meterPercent = useMemo(() => {
    if (centsOffset === null || !Number.isFinite(centsOffset)) {
      return 50;
    }

    const clamped = clamp(centsOffset, -METER_RANGE_CENTS, METER_RANGE_CENTS);
    return ((clamped + METER_RANGE_CENTS) / (2 * METER_RANGE_CENTS)) * 100;
  }, [centsOffset]);

  const statusText = useMemo(() => {
    if (snapshot.frequencyHz === null || centsOffset === null) {
      return isListening ? "Listening... play a long G note" : "Ready";
    }

    const absCents = Math.abs(centsOffset);
    if (absCents <= 5) {
      return "Excellent center";
    }

    if (absCents <= IN_TUNE_THRESHOLD_CENTS) {
      return "In tune";
    }

    return centsOffset > 0 ? "Sharp" : "Flat";
  }, [centsOffset, isListening, snapshot.frequencyHz]);

  const statusClassName = useMemo(() => {
    if (snapshot.frequencyHz === null || centsOffset === null) {
      return "long-note-status idle";
    }

    const absCents = Math.abs(centsOffset);
    if (absCents <= 5) {
      return "long-note-status excellent";
    }

    if (absCents <= IN_TUNE_THRESHOLD_CENTS) {
      return "long-note-status tuned";
    }

    return "long-note-status drift";
  }, [centsOffset, snapshot.frequencyHz]);

  const detectedNoteLabel = useMemo(() => {
    if (snapshot.frequencyHz === null) {
      return "-";
    }

    return noteDisplayMode === "indian"
      ? getNearestIndianNoteName(snapshot.frequencyHz)
      : getNearestWesternNoteName(snapshot.frequencyHz);
  }, [noteDisplayMode, snapshot.frequencyHz]);

  const referenceNoteLabel = noteDisplayMode === "indian" ? G_STRING_INDIAN_NOTE : G_STRING_NOTE;
  const alternateReferenceLabel = noteDisplayMode === "indian" ? G_STRING_NOTE : G_STRING_INDIAN_NOTE;

  return (
    <div className="container">
      <h1>Long Notes Trainer</h1>

      <section className="card long-note-hero-card">
        <p className="user-id-inline">
          <span className="user-id-inline-label">User ID:</span>{" "}
          <span className="user-id-inline-value">{userId}</span>
        </p>
        <p className="long-note-subtext">
          Sustain the target note and keep the meter centered for steady long-note control.
        </p>

        <div className="long-note-reference-pill" aria-label="Reference note">
          <span className="long-note-reference-note">{referenceNoteLabel}</span>
          <span className="long-note-reference-meta">{G_STRING_FREQUENCY_HZ} Hz ({alternateReferenceLabel}) reference</span>
        </div>

        <div className="row">
          <button onClick={isListening ? stopListening : startListening}>
            {isListening ? "Stop Live Detection" : "Start Live Detection"}
          </button>
          <button onClick={resetHoldStats}>Reset Hold Stats</button>
          <label htmlFor="long-note-display-mode" className="long-note-display-control">
            <span className="long-note-display-label">Note Display</span>
            <span className="long-note-display-select-wrap">
              <select
                id="long-note-display-mode"
                value={noteDisplayMode}
                onChange={(event) => {
                  const nextMode = event.target.value === "western" ? "western" : "indian";
                  setNoteDisplayMode(nextMode);
                }}
              >
                <option value="indian">Indian (Sargam)</option>
                <option value="western">Western (A-B)</option>
              </select>
            </span>
          </label>
        </div>

        {errorMessage && <p className="error">{errorMessage}</p>}
      </section>

      <section className="card long-note-meter-card">
        <div className={statusClassName}>{statusText}</div>

        <div className="long-note-meter-wrap" role="meter" aria-label="Cents offset meter">
          <div className="long-note-meter-track">
            <div className="long-note-meter-center-zone" />
            <div className="long-note-meter-needle" style={{ left: `${meterPercent}%` }} />
          </div>
          <div className="long-note-meter-labels">
            <span>Flat -50</span>
            <span>Center 0</span>
            <span>Sharp +50</span>
          </div>
        </div>

        <div className="long-note-stats-grid">
          <article className="long-note-stat-card">
            <h3>Detected Frequency</h3>
            <p>{snapshot.frequencyHz !== null ? `${snapshot.frequencyHz.toFixed(2)} Hz` : "--"}</p>
          </article>

          <article className="long-note-stat-card">
            <h3>Detected Note</h3>
            <p>{detectedNoteLabel}</p>
          </article>

          <article className="long-note-stat-card">
            <h3>Cents Offset</h3>
            <p>
              {centsOffset !== null
                ? `${centsOffset > 0 ? "+" : ""}${centsOffset.toFixed(1)} cents`
                : "--"}
            </p>
          </article>

          <article className="long-note-stat-card">
            <h3>Signal Strength</h3>
            <p>{snapshot.signalRms.toFixed(3)}</p>
          </article>

          <article className="long-note-stat-card">
            <h3>Current In-Tune Hold</h3>
            <p>{formatSeconds(holdSeconds)}</p>
          </article>

          <article className="long-note-stat-card">
            <h3>Best Hold</h3>
            <p>{formatSeconds(bestHoldSeconds)}</p>
          </article>
        </div>
      </section>
    </div>
  );
}
