import type { PracticeHistoryTimelineRow } from "../types";

type PracticeHistoryTimelineProps = {
  rows: PracticeHistoryTimelineRow[];
};

export default function PracticeHistoryTimeline({ rows }: PracticeHistoryTimelineProps) {
  if (rows.length === 0) {
    return <p className="muted">No timeline rows to display.</p>;
  }

  return (
    <ol className="practice-history-list">
      {rows.map((row) => (
        <li key={row.key} className="practice-history-item">
          <div className="practice-history-track">
            <span className="practice-history-dot" aria-hidden="true" />
          </div>

          <article className="practice-history-entry">
            <div className="practice-history-entry-head">
              <h4>Session {row.sequence}</h4>
              <p className="muted">{row.timestampLabel}</p>
            </div>

            <div className="practice-history-metrics">
              <p><strong>Accuracy:</strong> {row.noteAccuracyLabel}</p>
              <p><strong>Composite:</strong> {row.compositeLabel}</p>
              <p><strong>Technique:</strong> {row.techniqueLabel}</p>
              <p><strong>Δ Composite:</strong> {row.deltaLabel}</p>
            </div>

            {row.badges.length > 0 && (
              <div className="practice-history-badges">
                {row.badges.map((badge) => (
                  <span
                    key={`${row.key}-${badge.kind}`}
                    className={`practice-history-badge ${badge.kind}`}
                  >
                    {badge.label}
                  </span>
                ))}
              </div>
            )}
          </article>
        </li>
      ))}
    </ol>
  );
}
