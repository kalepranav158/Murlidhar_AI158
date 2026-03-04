import { useMemo } from "react";
import type { PracticeResultNormalized } from "../../types/normalized";
import { mapPracticeToStudioModel } from "./mappers";
import PitchTimeline from "./components/PitchTimeline";
import { TechniqueVisualizerPanel } from "../technique-visualizer";
import { AdaptiveCoachPanel } from "../adaptive-coach";

type PracticeStudioPanelProps = {
  userId: string;
  practice: PracticeResultNormalized;
};

type FeedbackSection = {
  label: string;
  value: string;
};

const asRecord = (value: unknown): Record<string, unknown> | null => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
};

const asText = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

const getFeedbackSections = (feedback: unknown): FeedbackSection[] => {
  const feedbackText = asText(feedback);
  if (feedbackText) {
    return [{ label: "Feedback", value: feedbackText }];
  }

  const feedbackObj = asRecord(feedback);
  if (!feedbackObj) {
    return [];
  }

  const sections: FeedbackSection[] = [];
  const pushIfText = (label: string, key: string) => {
    const value = asText(feedbackObj[key]);
    if (value) {
      sections.push({ label, value });
    }
  };

  pushIfText("Strengths & Assessment", "technical_assessment");
  pushIfText("Mistake Breakdown", "mistake_breakdown");
  pushIfText("Root Cause", "root_cause_analysis");
  pushIfText("Corrective Guidance", "corrective_guidance");
  pushIfText("Structured Practice Plan", "structured_practice_plan");
  pushIfText("Tempo Recommendation", "tempo_adjustment_recommendation");

  if (sections.length > 0) {
    return sections;
  }

  const fallback = JSON.stringify(feedbackObj, null, 2);
  if (fallback.trim().length > 0) {
    return [{ label: "Feedback", value: fallback }];
  }

  return [];
};

export default function PracticeStudioPanel({ userId, practice }: PracticeStudioPanelProps) {
  const studioModel = useMemo(() => mapPracticeToStudioModel(practice), [practice]);
  const feedbackSections = useMemo(() => getFeedbackSections(practice.rawFeedback), [practice.rawFeedback]);

  const meendCount = Array.isArray(practice.techniques?.meend) ? practice.techniques.meend.length : 0;
  const gamakCount = Array.isArray(practice.techniques?.gamak) ? practice.techniques.gamak.length : 0;

  return (
    <section className="practice-studio-panel">
      <div className="practice-studio-summary">
        <article className="practice-studio-stat">
          <h3>Accuracy</h3>
          <p>{practice.noteAccuracy !== null ? `${practice.noteAccuracy.toFixed(1)}%` : "N/A"}</p>
        </article>
        <article className="practice-studio-stat">
          <h3>Pitch Error</h3>
          <p>
            {practice.avgPitchErrorCents !== null
              ? `${practice.avgPitchErrorCents.toFixed(1)} cents`
              : "N/A"}
          </p>
        </article>
        <article className="practice-studio-stat">
          <h3>Timing Error</h3>
          <p>
            {practice.avgTimingErrorSec !== null
              ? `${practice.avgTimingErrorSec.toFixed(2)} sec`
              : "N/A"}
          </p>
        </article>
        <article className="practice-studio-stat">
          <h3>Technique Score</h3>
          <p>{practice.techniqueScore !== null ? practice.techniqueScore.toFixed(2) : "N/A"}</p>
        </article>
      </div>

      {studioModel ? (
        <PitchTimeline model={studioModel} />
      ) : (
        <p className="muted">Pitch timeline is not available for this response yet.</p>
      )}

      <TechniqueVisualizerPanel practice={practice} />

      <AdaptiveCoachPanel userId={userId} practice={practice} />

      <div className="practice-studio-insights">
        <p>
          <strong>Detected techniques:</strong> meend {meendCount}, gamak {gamakCount}
        </p>
        {practice.recommendedTempo !== null && (
          <p><strong>Tempo target:</strong> {practice.recommendedTempo} BPM</p>
        )}
        {practice.focusPhrase !== null && (
          <p><strong>Focus phrase:</strong> {practice.focusPhrase}</p>
        )}
        {practice.focusArea && (
          <p><strong>Focus area:</strong> {practice.focusArea}</p>
        )}
        {practice.alignmentDebug?.dtwTranspositionShiftSemitones !== null && (
          <p>
            <strong>Alignment shift:</strong> {practice.alignmentDebug?.dtwTranspositionShiftSemitones} semitones
          </p>
        )}
      </div>

      <div className="practice-studio-feedback">
        <h3>Guru Feedback</h3>
        {feedbackSections.length === 0 ? (
          <p className="muted">No feedback explanation available for this attempt.</p>
        ) : (
          <div className="practice-feedback-list">
            {feedbackSections.map((section) => (
              <article key={section.label} className="practice-feedback-item">
                <h4>{section.label}</h4>
                <p>{section.value}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
