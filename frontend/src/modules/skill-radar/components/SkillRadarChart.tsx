import type { SkillRadarNormalized } from "../../../types/normalized";
import type { SkillRadarAxis } from "../types";

type SkillRadarChartProps = {
  radar: SkillRadarNormalized;
};

const SIZE = 420;
const CENTER = SIZE / 2;
const RADIUS = 140;
const GRID_STEPS = 5;

const clamp01 = (value: number) => {
  if (value < 0) {
    return 0;
  }

  if (value > 1) {
    return 1;
  }

  return value;
};

const toPoint = (angleRadians: number, radius: number) => {
  const x = CENTER + Math.cos(angleRadians) * radius;
  const y = CENTER + Math.sin(angleRadians) * radius;

  return { x, y };
};

const polygonPoints = (axes: SkillRadarAxis[], scale = 1) => {
  const baseAngle = -Math.PI / 2;
  const step = (Math.PI * 2) / axes.length;

  return axes
    .map((axis, index) => {
      const valueRadius = RADIUS * clamp01(axis.value) * scale;
      const point = toPoint(baseAngle + step * index, valueRadius);
      return `${point.x},${point.y}`;
    })
    .join(" ");
};

export default function SkillRadarChart({ radar }: SkillRadarChartProps) {
  const axes: SkillRadarAxis[] = [
    { key: "rhythm", label: "Rhythm", value: radar.rhythm },
    { key: "pitch", label: "Pitch", value: radar.pitch },
    { key: "progress", label: "Progress", value: radar.progress },
    { key: "consistency", label: "Consistency", value: radar.consistency },
    { key: "technique", label: "Technique", value: radar.technique },
  ];

  const baseAngle = -Math.PI / 2;
  const step = (Math.PI * 2) / axes.length;

  return (
    <div className="skill-radar-wrap">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="skill-radar-svg" role="img" aria-label="Skill radar chart">
        {Array.from({ length: GRID_STEPS }, (_, index) => {
          const scale = (index + 1) / GRID_STEPS;
          const points = polygonPoints(axes, scale);
          return (
            <polygon
              key={`grid-${index}`}
              points={points}
              className="skill-radar-grid"
            />
          );
        })}

        {axes.map((axis, index) => {
          const angle = baseAngle + step * index;
          const outer = toPoint(angle, RADIUS);
          const labelPoint = toPoint(angle, RADIUS + 26);

          return (
            <g key={axis.key}>
              <line
                x1={CENTER}
                y1={CENTER}
                x2={outer.x}
                y2={outer.y}
                className="skill-radar-axis"
              />
              <text
                x={labelPoint.x}
                y={labelPoint.y}
                className="skill-radar-label"
                textAnchor="middle"
              >
                {axis.label}
              </text>
            </g>
          );
        })}

        <polygon
          points={polygonPoints(axes)}
          className="skill-radar-shape"
        />

        {axes.map((axis, index) => {
          const angle = baseAngle + step * index;
          const point = toPoint(angle, RADIUS * clamp01(axis.value));

          return (
            <circle
              key={`dot-${axis.key}`}
              cx={point.x}
              cy={point.y}
              r={4}
              className="skill-radar-dot"
            />
          );
        })}
      </svg>
    </div>
  );
}
