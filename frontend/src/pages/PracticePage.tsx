import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import {
  API_BASE_URL,
  listSongs,
} from "../api";
import { usePracticeSession } from "../hooks/usePracticeSession";
import { useStudentProfile } from "../hooks/useStudentProfile";
import ResultCard from "../components/ResultCard";
import ScreenState from "../components/ScreenState";
import { convertBlobToWavFile } from "../utils/audioToWav";
import { emitPracticeRefreshSignal } from "../utils/practiceRefreshSignal";
import { PracticeStudioPanel } from "../modules/practice-studio";

type ContentOption = {
  id: string;
  label: string;
};

export default function PracticePage() {
  const [userId, setUserId] = useState("demo_user");
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
  const { practiceState, submitAlankar, submitSong, submitMelody } = usePracticeSession();
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

  useEffect(() => {
    let disposed = false;

    const mapOptions = (
      catalog: Array<{ song_id: string; title?: string }>,
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

          return {
            id,
            label,
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

    if (mode === "song") {
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
      return;
    }

    try {
      await submitMelody({
        userId: safeUserId,
        melodyId: melodyId.trim(),
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
            onChange={(event) => setMode(event.target.value as "alankar" | "song" | "melody")}
          >
            <option value="alankar">Alankar Practice</option>
            <option value="song">Song Practice</option>
            <option value="melody">Melody Practice</option>
          </select>
        </label>

        {mode === "alankar" ? (
          <label>
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
          <label>
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
          <label>
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

        {catalogError && <p className="error">{catalogError}</p>}

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
