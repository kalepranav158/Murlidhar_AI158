import type { SkillRadarNormalized } from "../../types/normalized";
import SkillRadarChart from "./components/SkillRadarChart";

type SkillRadarPanelProps = {
  radar: SkillRadarNormalized;
};

const asPercent = (value: number) => `${Math.round(value * 100)}%`;

export default function SkillRadarPanel({ radar }: SkillRadarPanelProps) {
  return (
    <section className="skill-radar-panel">
      <SkillRadarChart radar={radar} />

      <div className="skill-radar-metrics">
        <article className="skill-radar-metric">
          <h3>Pitch</h3>
          <p>{asPercent(radar.pitch)}</p>
        </article>
        <article className="skill-radar-metric">
          <h3>Rhythm</h3>
          <p>{asPercent(radar.rhythm)}</p>
        </article>
        <article className="skill-radar-metric">
          <h3>Technique</h3>
          <p>{asPercent(radar.technique)}</p>
        </article>
        <article className="skill-radar-metric">
          <h3>Consistency</h3>
          <p>{asPercent(radar.consistency)}</p>
        </article>
        <article className="skill-radar-metric">
          <h3>Progress</h3>
          <p>{asPercent(radar.progress)}</p>
        </article>
        <article className="skill-radar-metric">
          <h3>Composite</h3>
          <p>{asPercent(radar.composite)}</p>
        </article>
      </div>

      <div className="skill-radar-sources">
        <p><strong>Technique source:</strong> {radar.techniqueSource}</p>
        <p><strong>Progress source:</strong> {radar.progressSource}</p>
      </div>
    </section>
  );
}
