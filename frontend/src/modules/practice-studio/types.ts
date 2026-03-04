export type StudioReferencePoint = {
  note: string;
  time: number;
  pitch: number;
};

export type StudioDetectedPoint = {
  note: string;
  time: number;
  cents: number;
  pitch: number;
};

export type StudioTechniqueEvent = {
  kind: "meend" | "gamak";
  startTime: number;
  endTime: number;
  label: string;
};

export type PracticeStudioModel = {
  referencePoints: StudioReferencePoint[];
  detectedPoints: StudioDetectedPoint[];
  techniqueEvents: StudioTechniqueEvent[];
  timeMin: number;
  timeMax: number;
  pitchMin: number;
  pitchMax: number;
};

export type ProjectedPoint = {
  x: number;
  y: number;
  note: string;
  time: number;
};

export type ProjectedTechniqueEvent = {
  kind: "meend" | "gamak";
  xStart: number;
  xEnd: number;
  label: string;
};
