import type {
  MessagePayload,
  PracticeApi,
  SessionsApi,
  StudentAnalyticsApi,
  StudentCurriculumApi,
  StudentProfileApi,
  StudentStreakApi,
} from "../types/api";
import type {
  AnalyticsSnapshotNormalized,
  ApiResult,
  PracticeResultNormalized,
  StudentCurriculumNormalized,
  StudentProfileNormalized,
  StudentStreakNormalized,
} from "../types/normalized";

const asStringArray = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === "string") : [];

export const isMessagePayload = (payload: unknown): payload is MessagePayload => {
  const status = (payload as { status?: unknown })?.status;
  const hasEnvelopeStatus = status === "no_data" || status === "error";

  return (
    typeof payload === "object" &&
    payload !== null &&
    (hasEnvelopeStatus || "message" in payload) &&
    typeof (payload as { message?: unknown }).message === "string"
  );
};

export const normalizeProfile = (
  payload: StudentProfileApi | MessagePayload | null | undefined,
): ApiResult<StudentProfileNormalized> => {
  if (!payload || isMessagePayload(payload)) {
    return {
      data: {
        currentLevel: "beginner",
        unlockedContent: [],
        masteredContent: [],
        recommendedContent: null,
        compositeScore: null,
        reason: null,
      },
      empty: {
        isEmpty: true,
        message: isMessagePayload(payload) ? payload.message : "No profile data available.",
      },
    };
  }

  return {
    data: {
      currentLevel: payload.current_level ?? "beginner",
      unlockedContent: asStringArray(payload.unlocked_content),
      masteredContent: asStringArray(payload.mastered_content),
      recommendedContent: payload.recommended_content ?? null,
      compositeScore: typeof payload.composite_score === "number" ? payload.composite_score : null,
      reason: payload.reason ?? null,
    },
    empty: {
      isEmpty: false,
      message: null,
    },
  };
};

export const normalizeCurriculum = (
  payload: StudentCurriculumApi | MessagePayload | null | undefined,
): ApiResult<StudentCurriculumNormalized> => {
  if (!payload || isMessagePayload(payload)) {
    return {
      data: {
        currentLevel: "beginner",
        unlockedContent: [],
        masteredContent: [],
        lockedContent: [],
        recommendedContent: null,
        reason: null,
        nextGoal: null,
        compositeScore: null,
      },
      empty: {
        isEmpty: true,
        message: isMessagePayload(payload) ? payload.message : "No curriculum data available.",
      },
    };
  }

  return {
    data: {
      currentLevel: payload.current_level ?? "beginner",
      unlockedContent: asStringArray(payload.unlocked_content),
      masteredContent: asStringArray(payload.mastered_content),
      lockedContent: asStringArray(payload.locked),
      recommendedContent: payload.recommended_content ?? null,
      reason: payload.reason ?? null,
      nextGoal: payload.next_goal ?? null,
      compositeScore:
        typeof payload.skill_snapshot?.composite_score === "number"
          ? payload.skill_snapshot.composite_score
          : null,
    },
    empty: {
      isEmpty: false,
      message: null,
    },
  };
};

export const normalizeStreak = (
  payload: StudentStreakApi | MessagePayload | null | undefined,
): ApiResult<StudentStreakNormalized> => {
  if (!payload || isMessagePayload(payload)) {
    return {
      data: {
        currentStreak: 0,
        longestStreak: 0,
        totalPracticeDays: 0,
        lastPracticeDate: null,
      },
      empty: {
        isEmpty: true,
        message: isMessagePayload(payload) ? payload.message : "No streak data available.",
      },
    };
  }

  return {
    data: {
      currentStreak: payload.current_streak ?? 0,
      longestStreak: payload.longest_streak ?? 0,
      totalPracticeDays: payload.total_practice_days ?? 0,
      lastPracticeDate: payload.last_practice_date ?? payload.last_practice_logical_date ?? null,
    },
    empty: {
      isEmpty: false,
      message: null,
    },
  };
};

export const normalizeAnalytics = (
  analyticsPayload: StudentAnalyticsApi | MessagePayload | null | undefined,
  streakPayload?: StudentStreakApi | MessagePayload | null,
  sessionsPayload?: SessionsApi | MessagePayload | null,
): ApiResult<AnalyticsSnapshotNormalized> => {
  const streak = normalizeStreak(streakPayload).data;

  const trendFromSessions =
    sessionsPayload && !isMessagePayload(sessionsPayload)
      ? (sessionsPayload.sessions ?? [])
          .map((session) => session.composite_score)
          .filter((score): score is number => typeof score === "number")
          .reverse()
      : [];

  if (!analyticsPayload || isMessagePayload(analyticsPayload)) {
    return {
      data: {
        compositeTrend: trendFromSessions,
        slope: null,
        consistencyIndex: null,
        compositeScore: null,
        streakCurrent: streak.currentStreak,
        streakLongest: streak.longestStreak,
        trendLabel: null,
        plateau: false,
        risk: false,
      },
      empty: {
        isEmpty: true,
        message: isMessagePayload(analyticsPayload)
          ? analyticsPayload.message
          : "No analytics data available.",
      },
    };
  }

  return {
    data: {
      compositeTrend: trendFromSessions,
      slope: typeof analyticsPayload.trend?.slope === "number" ? analyticsPayload.trend.slope : null,
      consistencyIndex:
        typeof analyticsPayload.indices?.consistency_index === "number"
          ? analyticsPayload.indices.consistency_index
          : null,
      compositeScore:
        typeof analyticsPayload.indices?.composite_score === "number"
          ? analyticsPayload.indices.composite_score
          : null,
      streakCurrent: streak.currentStreak,
      streakLongest: streak.longestStreak,
      trendLabel: analyticsPayload.trend?.classification ?? null,
      plateau: Boolean(analyticsPayload.flags?.plateau),
      risk: Boolean(analyticsPayload.flags?.risk),
    },
    empty: {
      isEmpty: false,
      message: null,
    },
  };
};

const extractAdaptivePlanSummary = (payload: PracticeApi): string | null => {
  if (payload.adaptive_plan && typeof payload.adaptive_plan === "object") {
    const candidateKeys = ["reason", "suggestion", "practice_focus", "recommended_tempo_adjustment"];
    for (const key of candidateKeys) {
      const value = (payload.adaptive_plan as Record<string, unknown>)[key];
      if (typeof value === "string" && value.trim().length > 0) {
        return value;
      }
    }
  }

  if (payload.song_adaptive_plan && typeof payload.song_adaptive_plan === "object") {
    const suggestion = (payload.song_adaptive_plan as Record<string, unknown>)["suggestion"];
    if (typeof suggestion === "string" && suggestion.trim().length > 0) {
      return suggestion;
    }
  }

  return null;
};

export const normalizePracticeResult = (
  payload: PracticeApi | MessagePayload | null | undefined,
): ApiResult<PracticeResultNormalized> => {
  if (!payload || isMessagePayload(payload)) {
    return {
      data: {
        song: null,
        phraseIndex: null,
        noteAccuracy: null,
        avgPitchErrorCents: null,
        avgTimingErrorSec: null,
        techniqueScore: null,
        adaptivePlanSummary: null,
        unlockEvent: false,
        rawFeedback: null,
        curriculum: null,
        detectedNotes: [],
        alignmentDebug: null,
        techniques: null,
        techniqueDetails: null,
      },
      empty: {
        isEmpty: true,
        message: isMessagePayload(payload) ? payload.message : "No practice data returned.",
      },
    };
  }

  const curriculum = normalizeCurriculum(payload.curriculum).data;
  const detectedNotesRaw = Array.isArray(payload.detected_notes)
    ? payload.detected_notes
    : Array.isArray(payload.played_notes)
      ? payload.played_notes
      : [];
  const detectedNotes = detectedNotesRaw
    .map((note) => {
      if (
        typeof note?.note !== "string" ||
        typeof note?.cents !== "number" ||
        typeof note?.time !== "number"
      ) {
        return null;
      }

      return {
        note: note.note,
        cents: note.cents,
        time: note.time,
      };
    })
    .filter((note): note is { note: string; cents: number; time: number } => note !== null);

  return {
    data: {
      song: payload.song ?? null,
      phraseIndex: typeof payload.phrase_index === "number" ? payload.phrase_index : null,
      noteAccuracy:
        typeof payload.evaluation?.note_accuracy === "number" ? payload.evaluation.note_accuracy : null,
      avgPitchErrorCents:
        typeof payload.evaluation?.avg_pitch_error_cents === "number"
          ? payload.evaluation.avg_pitch_error_cents
          : null,
      avgTimingErrorSec:
        typeof payload.evaluation?.avg_timing_error_sec === "number"
          ? payload.evaluation.avg_timing_error_sec
          : null,
      techniqueScore: typeof payload.technique_score === "number" ? payload.technique_score : null,
      adaptivePlanSummary: extractAdaptivePlanSummary(payload),
      unlockEvent: Boolean(payload.full_song_unlocked),
      rawFeedback: payload.evaluation?.feedback,
      curriculum: payload.curriculum ? curriculum : null,
      detectedNotes,
      alignmentDebug:
        payload.alignment_debug && typeof payload.alignment_debug === "object"
          ? {
              dtwTranspositionShiftSemitones:
                typeof payload.alignment_debug.dtw_transposition_shift_semitones === "number"
                  ? payload.alignment_debug.dtw_transposition_shift_semitones
                  : null,
            }
          : null,
      techniques:
        payload.techniques && typeof payload.techniques === "object"
          ? (payload.techniques as Record<string, unknown>)
          : null,
      techniqueDetails:
        payload.technique_details && typeof payload.technique_details === "object"
          ? (payload.technique_details as Record<string, unknown>)
          : null,
    },
    empty: {
      isEmpty: false,
      message: null,
    },
  };
};
