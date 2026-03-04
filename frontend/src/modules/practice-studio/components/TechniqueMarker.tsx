import type { ProjectedTechniqueEvent } from "../types";

type TechniqueMarkerProps = {
  events: ProjectedTechniqueEvent[];
};

export default function TechniqueMarker({ events }: TechniqueMarkerProps) {
  if (events.length === 0) {
    return null;
  }

  return (
    <g>
      {events.map((event, index) => {
        const width = Math.max(2, event.xEnd - event.xStart);
        const y = 14 + (index % 2) * 18;

        return (
          <g key={`${event.kind}-${event.xStart}-${event.xEnd}-${index}`}>
            <rect
              x={event.xStart}
              y={y}
              width={width}
              height={12}
              className={
                event.kind === "meend"
                  ? "timeline-technique-meend"
                  : "timeline-technique-gamak"
              }
            />
            <text x={event.xStart + 2} y={y + 10} className="timeline-technique-label">
              {event.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}
