import type { ProjectedPoint } from "../types";

type UserPitchCurveProps = {
  points: ProjectedPoint[];
};

const buildPolylinePoints = (points: ProjectedPoint[]) => {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
};

export default function UserPitchCurve({ points }: UserPitchCurveProps) {
  if (points.length === 0) {
    return null;
  }

  if (points.length === 1) {
    const point = points[0];
    return <circle cx={point.x} cy={point.y} r={3} className="timeline-user-point" />;
  }

  return (
    <g>
      <polyline
        points={buildPolylinePoints(points)}
        className="timeline-user-curve"
      />
      {points.map((point, index) => (
        <circle
          key={`user-point-${point.time}-${index}`}
          cx={point.x}
          cy={point.y}
          r={2.5}
          className="timeline-user-point"
        />
      ))}
    </g>
  );
}
