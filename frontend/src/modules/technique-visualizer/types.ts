export type TechniqueKind = "meend" | "gamak" | "unknown";

export type TechniqueTransitionRow = {
  key: string;
  label: string;
  technique: TechniqueKind;
  expectedStart: number | null;
  expectedEnd: number | null;
  observedStart: number | null;
  observedEnd: number | null;
  observedSummary: string;
  positionScore: number | null;
  directionScore: number | null;
  strengthScore: number | null;
  clarityScore: number | null;
  compositeScore: number | null;
  matched: boolean;
};

export type TechniqueVisualizerModel = {
  rows: TechniqueTransitionRow[];
  timeMin: number;
  timeMax: number;
  detectedMeend: number;
  detectedGamak: number;
  expectedTransitions: number;
  matchedTransitions: number;
};
