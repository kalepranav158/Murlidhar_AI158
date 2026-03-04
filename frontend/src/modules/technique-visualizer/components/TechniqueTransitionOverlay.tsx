import type {
  TechniqueTransitionRow,
  TechniqueVisualizerModel,
} from "../types";

type TechniqueTransitionOverlayProps = {
  model: TechniqueVisualizerModel;
};

const asPercent = (score: number | null): string => {
  if (score === null) {
    return "N/A";
  }

  return `${Math.round(score * 100)}%`;
};

const computeOverlayStyle = (
  start: number | null,
  end: number | null,
  model: TechniqueVisualizerModel,
): { left: string; width: string } | null => {
  if (start === null || end === null) {
    return null;
  }

  const span = Math.max(0.001, model.timeMax - model.timeMin);
  const normalizedStart = ((start - model.timeMin) / span) * 100;
  const normalizedEnd = ((end - model.timeMin) / span) * 100;
  const left = Math.max(0, Math.min(100, normalizedStart));
  const width = Math.max(2, Math.abs(normalizedEnd - normalizedStart));

  return {
    left: `${left}%`,
    width: `${width}%`,
  };
};

const OverlayRow = ({
  row,
  model,
}: {
  row: TechniqueTransitionRow;
  model: TechniqueVisualizerModel;
}) => {
  const expectedStyle = computeOverlayStyle(row.expectedStart, row.expectedEnd, model);
  const observedStyle = computeOverlayStyle(row.observedStart, row.observedEnd, model);

  return (
    <article className="technique-overlay-row">
      <div className="technique-overlay-head">
        <h4>{row.label}</h4>
        <span className={row.matched ? "technique-overlay-badge matched" : "technique-overlay-badge missing"}>
          {row.matched ? "Matched" : "Expected"}
        </span>
      </div>

      <div className="technique-overlay-track">
        {expectedStyle && (
          <span className="technique-overlay-segment expected" style={expectedStyle} />
        )}
        {observedStyle && (
          <span className="technique-overlay-segment observed" style={observedStyle} />
        )}
      </div>

      <div className="technique-overlay-metrics">
        <p><strong>Observed:</strong> {row.observedSummary}</p>
        <p><strong>Position:</strong> {asPercent(row.positionScore)}</p>
        <p><strong>Strength:</strong> {asPercent(row.strengthScore)}</p>
        <p><strong>Clarity:</strong> {asPercent(row.clarityScore)}</p>
        <p><strong>Composite:</strong> {asPercent(row.compositeScore)}</p>
      </div>
    </article>
  );
};

export default function TechniqueTransitionOverlay({ model }: TechniqueTransitionOverlayProps) {
  return (
    <section className="technique-overlay-list">
      <div className="technique-overlay-legend">
        <span><i className="legend-dot technique-expected" />Expected transition</span>
        <span><i className="legend-dot technique-observed" />Observed execution</span>
      </div>

      {model.rows.map((row) => (
        <OverlayRow key={row.key} row={row} model={model} />
      ))}
    </section>
  );
}
