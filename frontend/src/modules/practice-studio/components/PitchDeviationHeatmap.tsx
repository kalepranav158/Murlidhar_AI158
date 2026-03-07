import { useEffect, useMemo, useState } from "react";
import { EChartBase, type BaseChartOption, type ChartEvents } from "../../charts";
import type { PracticeResultNormalized } from "../../../types/normalized";
import type { TimeWindowSelection } from "../types";

type PitchDeviationScaleMode = "absolute" | "signed";

type PitchDeviationHeatmapProps = {
  practice: PracticeResultNormalized;
  onSelectWindow?: (window: TimeWindowSelection | null) => void;
};

type TimeSlot = {
  startTime: number;
  endTime: number;
  label: string;
};

type HeatmapComputation = {
  option: BaseChartOption;
  binCount: number;
  maxAbsCents: number;
  meanCents: number;
  mode: PitchDeviationScaleMode;
  timeSlots: TimeSlot[];
};

const SWARA_TO_SEMITONE: Record<string, number> = {
  Sa: 0,
  "Komal Re": 1,
  Re: 2,
  "Komal Ga": 3,
  Ga: 4,
  Ma: 5,
  "Tivra Ma": 6,
  Pa: 7,
  "Komal Dha": 8,
  Dha: 9,
  "Komal Ni": 10,
  Ni: 11,
};

const OCTAVE_TO_OFFSET: Record<string, number> = {
  Mandra: -12,
  Madhya: 0,
  Taar: 12,
};

const parseNoteRank = (note: string): number => {
  const raw = note.trim();
  if (!raw) {
    return Number.MAX_SAFE_INTEGER;
  }

  const tokens = raw.split(/\s+/);
  const octaveToken = tokens[0];
  const hasOctave = Object.prototype.hasOwnProperty.call(OCTAVE_TO_OFFSET, octaveToken);

  const octaveOffset = hasOctave ? OCTAVE_TO_OFFSET[octaveToken] : OCTAVE_TO_OFFSET.Madhya;
  const swara = hasOctave ? tokens.slice(1).join(" ") : tokens.join(" ");

  if (!Object.prototype.hasOwnProperty.call(SWARA_TO_SEMITONE, swara)) {
    return Number.MAX_SAFE_INTEGER;
  }

  return octaveOffset + SWARA_TO_SEMITONE[swara];
};

const buildPitchDeviationHeatmap = (
  practice: PracticeResultNormalized,
  mode: PitchDeviationScaleMode,
): HeatmapComputation | null => {
  const detected = practice.detectedNotes.filter(
    (note) =>
      typeof note.time === "number" &&
      Number.isFinite(note.time) &&
      typeof note.cents === "number" &&
      Number.isFinite(note.cents) &&
      typeof note.note === "string" &&
      note.note.trim().length > 0,
  );

  if (detected.length === 0) {
    return null;
  }

  const minTime = Math.min(...detected.map((entry) => entry.time));
  const maxTimeRaw = Math.max(...detected.map((entry) => entry.time));
  const maxTime = maxTimeRaw > minTime ? maxTimeRaw : minTime + 0.2;
  const span = Math.max(0.001, maxTime - minTime);

  const binCount = Math.max(8, Math.min(24, Math.ceil(span / 0.35)));
  const binSize = span / binCount;

  const referenceNoteSet = new Set(
    practice.referenceNotes
      .map((note) => note.note)
      .filter((note): note is string => typeof note === "string" && note.trim().length > 0),
  );
  const detectedNoteSet = new Set(detected.map((note) => note.note));

  const noteCategories = Array.from(new Set([...referenceNoteSet, ...detectedNoteSet])).sort(
    (left, right) => {
      const rankLeft = parseNoteRank(left);
      const rankRight = parseNoteRank(right);

      if (rankLeft === rankRight) {
        return left.localeCompare(right);
      }

      return rankLeft - rankRight;
    },
  );

  if (noteCategories.length === 0) {
    return null;
  }

  const noteIndexMap = new Map(noteCategories.map((note, index) => [note, index]));
  const bucketMap = new Map<
    string,
    { sumAbs: number; sumSigned: number; count: number; x: number; y: number }
  >();

  for (const sample of detected) {
    const yIndex = noteIndexMap.get(sample.note);
    if (typeof yIndex !== "number") {
      continue;
    }

    const bucketRaw = Math.floor((sample.time - minTime) / binSize);
    const xIndex = Math.max(0, Math.min(binCount - 1, bucketRaw));
    const key = `${xIndex}:${yIndex}`;
    const signedCents = sample.cents;
    const absCents = Math.abs(signedCents);

    const existing = bucketMap.get(key);
    if (existing) {
      existing.sumAbs += absCents;
      existing.sumSigned += signedCents;
      existing.count += 1;
    } else {
      bucketMap.set(key, {
        sumAbs: absCents,
        sumSigned: signedCents,
        count: 1,
        x: xIndex,
        y: yIndex,
      });
    }
  }

  if (bucketMap.size === 0) {
    return null;
  }

  const heatmapData: Array<[number, number, number]> = Array.from(bucketMap.values()).map((entry) => [
    entry.x,
    entry.y,
    Math.round(
      ((mode === "absolute" ? entry.sumAbs : entry.sumSigned) / entry.count) * 10,
    ) / 10,
  ]);

  const maxAbsCents = Math.max(...heatmapData.map((entry) => Math.abs(entry[2])));
  const meanCents =
    heatmapData.reduce((sum, entry) => sum + entry[2], 0) /
    Math.max(1, heatmapData.length);

  const visualMax = Math.max(20, Math.ceil(maxAbsCents / 5) * 5);

  const timeSlots = Array.from({ length: binCount }, (_, index) => {
    const start = minTime + (index * binSize);
    const end = index === binCount - 1 ? maxTime : start + binSize;
    return {
      startTime: start,
      endTime: end,
      label: `${start.toFixed(1)}-${end.toFixed(1)}s`,
    };
  });
  const timeLabels = timeSlots.map((slot) => slot.label);
  const modeLabel = mode === "absolute" ? "|cents|" : "signed cents";
  const seriesName = mode === "absolute" ? "Pitch Deviation" : "Pitch Deviation (Signed)";

  const option: BaseChartOption = {
    tooltip: {
      trigger: "item",
      formatter: (params: unknown) => {
        const payload = params as { data?: [number, number, number] };
        const data = payload?.data;

        if (!data || data.length < 3) {
          return "No data";
        }

        const x = data[0];
        const y = data[1];
        const value = data[2];

        const slotLabel = typeof x === "number" ? timeLabels[x] ?? `T${x + 1}` : "Unknown";
        const noteLabel = typeof y === "number" ? noteCategories[y] ?? "Unknown" : "Unknown";

        return `${slotLabel}<br/>${noteLabel}<br/>${modeLabel}: ${value.toFixed(1)}`;
      },
    },
    grid: {
      left: 64,
      right: 16,
      top: 26,
      bottom: 66,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: timeLabels,
      splitArea: {
        show: true,
      },
      axisLabel: {
        color: "#5d6473",
        rotate: 35,
      },
      axisLine: {
        lineStyle: {
          color: "#c5cbdb",
        },
      },
    },
    yAxis: {
      type: "category",
      data: noteCategories,
      splitArea: {
        show: true,
      },
      axisLabel: {
        color: "#5d6473",
      },
      axisLine: {
        lineStyle: {
          color: "#c5cbdb",
        },
      },
    },
    visualMap: {
      min: mode === "absolute" ? 0 : -visualMax,
      max: visualMax,
      orient: "horizontal",
      left: "center",
      bottom: 12,
      calculable: true,
      inRange: {
        color:
          mode === "absolute"
            ? ["#e0f2fe", "#60a5fa", "#2563eb", "#b91c1c"]
            : ["#1d4ed8", "#93c5fd", "#f8fafc", "#fca5a5", "#b91c1c"],
      },
      text: mode === "absolute" ? ["High", "Low"] : ["Positive", "Negative"],
      textStyle: {
        color: "#4b556a",
      },
    },
    series: [
      {
        name: seriesName,
        type: "heatmap",
        data: heatmapData,
        emphasis: {
          itemStyle: {
            shadowBlur: 8,
            shadowColor: "rgba(0, 0, 0, 0.25)",
          },
        },
      },
    ],
  };

  return {
    option,
    binCount,
    maxAbsCents,
    meanCents,
    mode,
    timeSlots,
  };
};

const readBinIndex = (payload: unknown): number | null => {
  const event = payload as { data?: unknown; value?: unknown };
  const data = event?.data;
  const value = event?.value;

  const candidate =
    Array.isArray(data) && data.length > 0
      ? data[0]
      : Array.isArray(value) && value.length > 0
        ? value[0]
        : null;

  if (typeof candidate !== "number" || !Number.isFinite(candidate)) {
    return null;
  }

  return Math.round(candidate);
};

export default function PitchDeviationHeatmap({
  practice,
  onSelectWindow,
}: PitchDeviationHeatmapProps) {
  const [mode, setMode] = useState<PitchDeviationScaleMode>("absolute");
  const [selectedBin, setSelectedBin] = useState<number | null>(null);

  const computation = useMemo(() => buildPitchDeviationHeatmap(practice, mode), [practice, mode]);

  useEffect(() => {
    if (!computation) {
      setSelectedBin(null);
      onSelectWindow?.(null);
      return;
    }

    if (selectedBin === null) {
      return;
    }

    if (selectedBin < 0 || selectedBin >= computation.timeSlots.length) {
      setSelectedBin(null);
      onSelectWindow?.(null);
      return;
    }

    const slot = computation.timeSlots[selectedBin];
    onSelectWindow?.({
      startTime: slot.startTime,
      endTime: slot.endTime,
      label: slot.label,
    });
  }, [computation, onSelectWindow, selectedBin]);

  const selectedWindow =
    computation && selectedBin !== null && selectedBin >= 0 && selectedBin < computation.timeSlots.length
      ? computation.timeSlots[selectedBin]
      : null;

  const onEvents = useMemo<ChartEvents | undefined>(() => {
    if (!computation) {
      return undefined;
    }

    return {
      click: (payload: unknown) => {
        const binIndex = readBinIndex(payload);
        if (binIndex === null || binIndex < 0 || binIndex >= computation.timeSlots.length) {
          return;
        }

        setSelectedBin(binIndex);
      },
    };
  }, [computation]);

  const clearSelection = () => {
    setSelectedBin(null);
    onSelectWindow?.(null);
  };

  return (
    <section className="practice-studio-heatmap">
      <h3>Pitch Deviation Heatmap</h3>
      <p className="muted">Click a heatmap cell to highlight the same time window in the pitch timeline.</p>

      <div className="heatmap-toolbar">
        <div className="heatmap-toggle-group" role="group" aria-label="Pitch deviation scale">
          <button
            type="button"
            className={mode === "absolute" ? "heatmap-toggle-btn active" : "heatmap-toggle-btn"}
            onClick={() => setMode("absolute")}
          >
            Absolute Cents
          </button>
          <button
            type="button"
            className={mode === "signed" ? "heatmap-toggle-btn active" : "heatmap-toggle-btn"}
            onClick={() => setMode("signed")}
          >
            Signed Cents
          </button>
        </div>

        <button type="button" onClick={clearSelection} disabled={selectedBin === null}>
          Clear Timeline Highlight
        </button>
      </div>

      {!computation ? (
        <p className="muted">Heatmap needs detected pitch samples with cents and timing data.</p>
      ) : (
        <>
          <p className="muted">
            Mode: {computation.mode === "absolute" ? "Absolute" : "Signed"} | Bins: {computation.binCount} | Mean: {computation.meanCents.toFixed(1)} cents | Peak |cents|: {computation.maxAbsCents.toFixed(1)}
          </p>
          {selectedWindow && (
            <p className="muted heatmap-selection-note">
              Selected timeline window: {selectedWindow.label}
            </p>
          )}
          <EChartBase option={computation.option} height={340} renderer="canvas" onEvents={onEvents} />
        </>
      )}
    </section>
  );
}
