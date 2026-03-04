import { useMemo } from "react";
import type { PracticeResultNormalized } from "../../types/normalized";
import { mapPracticeToTechniqueVisualizer } from "./mappers";
import TechniqueTransitionOverlay from "./components/TechniqueTransitionOverlay";

type TechniqueVisualizerPanelProps = {
  practice: PracticeResultNormalized;
};

export default function TechniqueVisualizerPanel({ practice }: TechniqueVisualizerPanelProps) {
  const model = useMemo(() => mapPracticeToTechniqueVisualizer(practice), [practice]);

  if (!model) {
    return (
      <section className="technique-visualizer-panel">
        <h3>Technique Visualizer</h3>
        <p className="muted">No meend or gamak transition data available for this attempt.</p>
      </section>
    );
  }

  return (
    <section className="technique-visualizer-panel">
      <h3>Technique Visualizer</h3>

      <div className="technique-visualizer-summary">
        <article className="technique-visualizer-stat">
          <h4>Detected Meend</h4>
          <p>{model.detectedMeend}</p>
        </article>
        <article className="technique-visualizer-stat">
          <h4>Detected Gamak</h4>
          <p>{model.detectedGamak}</p>
        </article>
        <article className="technique-visualizer-stat">
          <h4>Expected Transitions</h4>
          <p>{model.expectedTransitions}</p>
        </article>
        <article className="technique-visualizer-stat">
          <h4>Matched Transitions</h4>
          <p>{model.matchedTransitions}</p>
        </article>
      </div>

      {model.rows.length === 0 ? (
        <p className="muted">No transition-level comparison details were returned.</p>
      ) : (
        <TechniqueTransitionOverlay model={model} />
      )}
    </section>
  );
}
