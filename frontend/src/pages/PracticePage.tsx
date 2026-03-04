import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import {
  API_BASE_URL,
} from "../api";
import { usePracticeSession } from "../hooks/usePracticeSession";
import { useStudentProfile } from "../hooks/useStudentProfile";
import ResultCard from "../components/ResultCard";
import ScreenState from "../components/ScreenState";
import { convertBlobToWavFile } from "../utils/audioToWav";
import { emitPracticeRefreshSignal } from "../utils/practiceRefreshSignal";
import { PracticeStudioPanel } from "../modules/practice-studio";

export default function PracticePage() {
  const [userId, setUserId] = useState("demo_user");
  const [mode, setMode] = useState<"alankar" | "song">("alankar");
  const [inputMethod, setInputMethod] = useState<"upload" | "record">("upload");
  const [alankarId, setAlankarId] = useState("alankar_1");
  const [songId, setSongId] = useState("song_1");
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [tempo, setTempo] = useState(60);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [recordedWavFile, setRecordedWavFile] = useState<File | null>(null);
  const [recordedRawFile, setRecordedRawFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [recordingPreviewUrl, setRecordingPreviewUrl] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const { practiceState, submitAlankar, submitSong } = usePracticeSession();
  const { curriculumState, loadCurriculum } = useStudentProfile();

  const safeUserId = useMemo(() => userId.trim(), [userId]);

  useEffect(() => {
    return () => {
      if (recordingPreviewUrl) {
        URL.revokeObjectURL(recordingPreviewUrl);
      }

      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, [recordingPreviewUrl]);

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

            if (recordingPreviewUrl) {
              URL.revokeObjectURL(recordingPreviewUrl);
            }
            setRecordingPreviewUrl(URL.createObjectURL(wavFile));
          } catch {
            setRecordedWavFile(null);

            if (recordingPreviewUrl) {
              URL.revokeObjectURL(recordingPreviewUrl);
            }
            setRecordingPreviewUrl(URL.createObjectURL(rawFile));

            setRecordingError(
              "Browser WAV conversion failed. Using raw recording file; backend will convert/process it.",
            );
          }

          setAudioFile(null);
        } catch (error) {
          const message = error instanceof Error ? error.message : "Failed to process recorded audio.";
          setRecordingError(message);
        } finally {
          mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
          mediaStreamRef.current = null;
        }
      };

      recorder.start();
      setRecording(true);
      setRecordedWavFile(null);
      setRecordedRawFile(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Microphone access failed.";
      setRecordingError(message);
    }
  };

  const stopRecording = () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== "recording") {
      return;
    }

    mediaRecorderRef.current.stop();
    setRecording(false);
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
          phraseIndex,
          tempo,
          audioFile: selectedFile,
        });
        emitPracticeRefreshSignal(safeUserId);
      } catch {
        return;
      }
      return;
    }

    try {
      await submitSong({
        userId: safeUserId,
        songId: songId.trim(),
        phraseIndex,
        tempo,
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

  return (
    <div className="container">
      <h1>Practice Studio</h1>
      <p className="muted">Base URL: {API_BASE_URL}</p>

      <section className="card">
        <label>
          User ID
          <input value={userId} onChange={(event) => setUserId(event.target.value)} />
        </label>

        <label>
          Mode
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value as "alankar" | "song")}
          >
            <option value="alankar">Alankar Practice</option>
            <option value="song">Song Practice</option>
          </select>
        </label>

        {mode === "alankar" ? (
          <label>
            Alankar ID
            <input value={alankarId} onChange={(event) => setAlankarId(event.target.value)} />
          </label>
        ) : (
          <label>
            Song ID
            <input value={songId} onChange={(event) => setSongId(event.target.value)} />
          </label>
        )}

        <label>
          Phrase Index
          <input
            type="number"
            min={0}
            value={phraseIndex}
            onChange={(event) => setPhraseIndex(Number(event.target.value || 0))}
          />
        </label>

        <label>
          Tempo
          <input
            type="number"
            min={20}
            max={220}
            value={tempo}
            onChange={(event) => setTempo(Number(event.target.value || 60))}
          />
        </label>

        <label>
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
            <div className="row">
              <button onClick={startRecording} disabled={recording}>Start Recording</button>
              <button onClick={stopRecording} disabled={!recording}>Stop Recording</button>
            </div>
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
        <ResultCard title="Curriculum Snapshot" state={curriculumState} />
      </section>
    </div>
  );
}
