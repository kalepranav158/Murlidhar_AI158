import ReferenceNoteBar from "./ReferenceNoteBar";
import TechniqueMarker from "./TechniqueMarker";
import UserPitchCurve from "./UserPitchCurve";
import type {
  PracticeStudioModel,
  ProjectedPoint,
  ProjectedTechniqueEvent,
  TimeWindowSelection,
} from "../types";

type PitchTimelineProps = {
  model: PracticeStudioModel;
  highlightedWindow?: TimeWindowSelection | null;
};

const SVG_WIDTH = 920;
const SVG_HEIGHT = 280;
const PADDING = {
  left: 56,
  right: 18,
  top: 52,
  bottom: 36,
};

export default function PitchTimeline({ model, highlightedWindow = null }: PitchTimelineProps) {
  const innerWidth = SVG_WIDTH - PADDING.left - PADDING.right;
  const innerHeight = SVG_HEIGHT - PADDING.top - PADDING.bottom;

  const timeSpan = Math.max(0.001, model.timeMax - model.timeMin);
  const pitchSpan = Math.max(0.001, model.pitchMax - model.pitchMin);

  const toX = (time: number) => {
    return PADDING.left + ((time - model.timeMin) / timeSpan) * innerWidth;
  };

  const toY = (pitch: number) => {
    return PADDING.top + (1 - (pitch - model.pitchMin) / pitchSpan) * innerHeight;
  };

  const referencePoints: ProjectedPoint[] = model.referencePoints.map((point) => ({
    x: toX(point.time),
    y: toY(point.pitch),
    note: point.note,
    time: point.time,
  }));

  const detectedPoints: ProjectedPoint[] = model.detectedPoints.map((point) => ({
    x: toX(point.time),
    y: toY(point.pitch),
    note: point.note,
    time: point.time,
  }));

  const techniqueEvents: ProjectedTechniqueEvent[] = model.techniqueEvents.map((event) => {
    const start = Math.min(event.startTime, event.endTime);
    const end = Math.max(event.startTime, event.endTime);

    return {
      kind: event.kind,
      xStart: toX(start),
      xEnd: toX(end),
      label: event.label,
    };
  });

  const gridLines = 6;
  const yTicks = Array.from({ length: gridLines + 1 }, (_, index) => {
    const ratio = index / gridLines;
    const y = PADDING.top + ratio * innerHeight;
    const pitch = model.pitchMax - ratio * pitchSpan;

    return {
      y,
      label: pitch.toFixed(1),
    };
  });

  const duration = model.timeMax - model.timeMin;
  const secondStep = duration > 10 ? 2 : 1;
  const xTicks = [] as Array<{ x: number; label: string }>;
  for (let second = Math.floor(model.timeMin); second <= Math.ceil(model.timeMax); second += secondStep) {
    xTicks.push({
      x: toX(second),
      label: `${second.toFixed(0)}s`,
    });
  }

  const windowStart = highlightedWindow
    ? Math.max(model.timeMin, Math.min(highlightedWindow.startTime, highlightedWindow.endTime))
    : null;
  const windowEnd = highlightedWindow
    ? Math.min(model.timeMax, Math.max(highlightedWindow.startTime, highlightedWindow.endTime))
    : null;
  const hasWindow =
    typeof windowStart === "number" &&
    typeof windowEnd === "number" &&
    Number.isFinite(windowStart) &&
    Number.isFinite(windowEnd) &&
    windowEnd > windowStart;
  const xStart = hasWindow ? toX(windowStart) : 0;
  const xEnd = hasWindow ? toX(windowEnd) : 0;
  const windowWidth = Math.max(0, xEnd - xStart);

  return (
    <div className="pitch-timeline-wrap">
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="pitch-timeline-svg"
        role="img"
        aria-label="Reference melody and user pitch curve timeline"
      >
        <rect
          x={PADDING.left}
          y={PADDING.top}
          width={innerWidth}
          height={innerHeight}
          className="timeline-bg"
        />

        {hasWindow && (
          <g>
            <rect
              x={xStart}
              y={PADDING.top}
              width={windowWidth}
              height={innerHeight}
              className="timeline-selection-window"
            />
            <line x1={xStart} y1={PADDING.top} x2={xStart} y2={PADDING.top + innerHeight} className="timeline-selection-edge" />
            <line x1={xEnd} y1={PADDING.top} x2={xEnd} y2={PADDING.top + innerHeight} className="timeline-selection-edge" />
          </g>
        )}

        {yTicks.map((tick) => (
          <g key={`y-${tick.y}`}>
            <line
              x1={PADDING.left}
              y1={tick.y}
              x2={PADDING.left + innerWidth}
              y2={tick.y}
              className="timeline-grid-line"
            />
            <text x={6} y={tick.y + 4} className="timeline-axis-label">
              {tick.label}
            </text>
          </g>
        ))}

        {xTicks.map((tick) => (
          <g key={`x-${tick.label}`}>
            <line
              x1={tick.x}
              y1={PADDING.top}
              x2={tick.x}
              y2={PADDING.top + innerHeight}
              className="timeline-grid-line"
            />
            <text x={tick.x - 8} y={SVG_HEIGHT - 10} className="timeline-axis-label">
              {tick.label}
            </text>
          </g>
        ))}

        <TechniqueMarker events={techniqueEvents} />
        <ReferenceNoteBar points={referencePoints} />
        <UserPitchCurve points={detectedPoints} />
      </svg>

      <div className="timeline-legend">
        <span><i className="legend-dot legend-reference" />Reference melody</span>
        <span><i className="legend-dot legend-user" />User pitch curve</span>
        <span><i className="legend-dot legend-selection" />Selected heatmap window</span>
        <span><i className="legend-dot legend-meend" />Meend markers</span>
        <span><i className="legend-dot legend-gamak" />Gamak markers</span>
      </div>
    </div>
  );
}
