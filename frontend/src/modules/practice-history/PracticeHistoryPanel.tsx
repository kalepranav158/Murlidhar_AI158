import { useMemo } from "react";
import type { PracticeHistoryNormalized } from "../../types/normalized";
import { mapPracticeHistoryToTimeline } from "./mappers";
import PracticeHistoryTimeline from "./components/PracticeHistoryTimeline";

type PracticeHistoryPanelProps = {
  history: PracticeHistoryNormalized;
};

export default function PracticeHistoryPanel({ history }: PracticeHistoryPanelProps) {
  const timeline = useMemo(() => mapPracticeHistoryToTimeline(history), [history]);

  return (
    <section className="practice-history-panel">
      <div className="practice-history-summary">
        <article className="practice-history-stat">
          <h3>Sessions Shown</h3>
          <p>{timeline.sessionsShown}</p>
        </article>
        <article className="practice-history-stat">
          <h3>Latest Composite</h3>
          <p>{timeline.latestCompositeLabel}</p>
        </article>
        <article className="practice-history-stat">
          <h3>Trend</h3>
          <p>{timeline.trendLabel}</p>
        </article>
        <article className="practice-history-stat">
          <h3>Unlock Events</h3>
          <p>{timeline.unlockEvents}</p>
        </article>
      </div>

      <PracticeHistoryTimeline rows={timeline.rows} />

      <div className="practice-history-note">
        <p><strong>Unlocked content total:</strong> {history.unlockedContentCount}</p>
        <p className="muted">
          Unlock badges are inferred from backend curriculum snapshot deltas between refreshes.
        </p>
      </div>
    </section>
  );
}
