import type { ProjectedPoint } from "../types";

type ReferenceNoteBarProps = {
  points: ProjectedPoint[];
};

export default function ReferenceNoteBar({ points }: ReferenceNoteBarProps) {
  if (points.length === 0) {
    return null;
  }

  const labelStep = points.length > 16 ? Math.ceil(points.length / 12) : 1;

  return (
    <g>
      {points.slice(0, -1).map((point, index) => {
        const next = points[index + 1];

        return (
          <line
            key={`ref-line-${point.time}-${next.time}`}
            x1={point.x}
            y1={point.y}
            x2={next.x}
            y2={point.y}
            className="timeline-reference-line"
          />
        );
      })}

      {points.map((point, index) => (
        <g key={`ref-point-${point.time}-${index}`}>
          <circle cx={point.x} cy={point.y} r={4} className="timeline-reference-point" />
          {index % labelStep === 0 && (
            <text x={point.x + 4} y={point.y - 8} className="timeline-note-label">
              {point.note}
            </text>
          )}
        </g>
      ))}
    </g>
  );
}
