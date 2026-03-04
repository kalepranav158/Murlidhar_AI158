import type { PracticeResultNormalized } from "../../types/normalized";
import type {
  PracticeStudioModel,
  StudioDetectedPoint,
  StudioReferencePoint,
  StudioTechniqueEvent,
} from "./types";

const SWARA_TO_SEMITONE: Record<string, number> = {
  Sa: 0,
  "Komal Re": 1,
  Re: 2,
  "Komal Ga": 3,
  Ga: 4,
  Ma: 5,
  "Tivra Ma": 6,
  Pa: 7,
  "Komal Dha": 8,
  Dha: 9,
  "Komal Ni": 10,
  Ni: 11,
};

const OCTAVE_TO_OFFSET: Record<string, number> = {
  Mandra: -12,
  Madhya: 0,
  Taar: 12,
};

const parseNotePitch = (note: string, cents = 0): number | null => {
  const raw = note.trim();
  if (!raw) {
    return null;
  }

  const tokens = raw.split(/\s+/);
  const hasOctave = Object.prototype.hasOwnProperty.call(OCTAVE_TO_OFFSET, tokens[0]);

  const octave = hasOctave ? tokens[0] : "Madhya";
  const swara = hasOctave ? tokens.slice(1).join(" ") : tokens.join(" ");

  if (!swara || !Object.prototype.hasOwnProperty.call(SWARA_TO_SEMITONE, swara)) {
    return null;
  }

  return OCTAVE_TO_OFFSET[octave] + SWARA_TO_SEMITONE[swara] + cents / 100;
};

const asObjectArray = (value: unknown): Array<Record<string, unknown>> => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(
    (entry): entry is Record<string, unknown> =>
      typeof entry === "object" && entry !== null,
  );
};

const mapReferencePoints = (practice: PracticeResultNormalized): StudioReferencePoint[] => {
  return practice.referenceNotes
    .map((note) => {
      const pitch = parseNotePitch(note.note, 0);
      if (pitch === null || !Number.isFinite(note.time)) {
        return null;
      }

      return {
        note: note.note,
        time: note.time,
        pitch,
      };
    })
    .filter((note): note is StudioReferencePoint => note !== null)
    .sort((left, right) => left.time - right.time);
};

const mapDetectedPoints = (practice: PracticeResultNormalized): StudioDetectedPoint[] => {
  return practice.detectedNotes
    .map((note) => {
      const pitch = parseNotePitch(note.note, note.cents);
      if (pitch === null || !Number.isFinite(note.time)) {
        return null;
      }

      return {
        note: note.note,
        time: note.time,
        cents: note.cents,
        pitch,
      };
    })
    .filter((note): note is StudioDetectedPoint => note !== null)
    .sort((left, right) => left.time - right.time);
};

const mapTechniqueEvents = (practice: PracticeResultNormalized): StudioTechniqueEvent[] => {
  const techniques = practice.techniques;

  const meend = asObjectArray(techniques?.meend).map((entry, index) => {
    const startTime = typeof entry.start_time === "number" ? entry.start_time : 0;
    const endTime = typeof entry.end_time === "number" ? entry.end_time : startTime;
    const fromNote = typeof entry.from_note === "string" ? entry.from_note : null;
    const toNote = typeof entry.to_note === "string" ? entry.to_note : null;

    return {
      kind: "meend" as const,
      startTime,
      endTime,
      label:
        fromNote && toNote
          ? `${fromNote} → ${toNote} (meend)`
          : `Meend ${index + 1}`,
    };
  });

  const gamak = asObjectArray(techniques?.gamak).map((entry, index) => {
    const startTime = typeof entry.start_time === "number" ? entry.start_time : 0;
    const endTime = typeof entry.end_time === "number" ? entry.end_time : startTime;
    const centerNote = typeof entry.center_note === "string" ? entry.center_note : null;

    return {
      kind: "gamak" as const,
      startTime,
      endTime,
      label: centerNote ? `${centerNote} (gamak)` : `Gamak ${index + 1}`,
    };
  });

  return [...meend, ...gamak]
    .filter((event) => Number.isFinite(event.startTime) && Number.isFinite(event.endTime))
    .sort((left, right) => left.startTime - right.startTime);
};

export const mapPracticeToStudioModel = (
  practice: PracticeResultNormalized,
): PracticeStudioModel | null => {
  const referencePoints = mapReferencePoints(practice);
  const detectedPoints = mapDetectedPoints(practice);
  const techniqueEvents = mapTechniqueEvents(practice);

  if (referencePoints.length === 0 && detectedPoints.length === 0) {
    return null;
  }

  const times = [
    ...referencePoints.map((point) => point.time),
    ...detectedPoints.map((point) => point.time),
    ...techniqueEvents.map((event) => event.startTime),
    ...techniqueEvents.map((event) => event.endTime),
  ];

  const pitches = [
    ...referencePoints.map((point) => point.pitch),
    ...detectedPoints.map((point) => point.pitch),
  ];

  const rawTimeMin = times.length > 0 ? Math.min(...times) : 0;
  const rawTimeMax = times.length > 0 ? Math.max(...times) : 1;
  const timeMin = Math.min(0, rawTimeMin);
  const timeMax = rawTimeMax > timeMin ? rawTimeMax : timeMin + 1;

  const rawPitchMin = pitches.length > 0 ? Math.min(...pitches) : -2;
  const rawPitchMax = pitches.length > 0 ? Math.max(...pitches) : 14;
  const pitchMin = Math.floor(rawPitchMin - 1);
  const pitchMax = Math.ceil(rawPitchMax + 1);

  return {
    referencePoints,
    detectedPoints,
    techniqueEvents,
    timeMin,
    timeMax,
    pitchMin,
    pitchMax: pitchMax > pitchMin ? pitchMax : pitchMin + 1,
  };
};
