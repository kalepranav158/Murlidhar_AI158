import type {
  AnalyticsRadarApi,
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
  PracticeHistoryNormalized,
  PracticeResultNormalized,
  SkillRadarNormalized,
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
        contentType: null,
        song: null,
        phraseIndex: null,
        noteAccuracy: null,
        avgPitchErrorCents: null,
        avgTimingErrorSec: null,
        techniqueScore: null,
        adaptivePlanSummary: null,
        recommendedTempo: null,
        songRecommendedTempo: null,
        focusArea: null,
        focusPhrase: null,
        targetDrill: null,
        exerciseMode: null,
        variationStrategy: null,
        tempoFeedback: null,
        songRecommendation: null,
        unlockEvent: false,
        rawFeedback: null,
        curriculum: null,
        detectedNotes: [],
        referenceNotes: [],
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

  const referenceNotesRaw = Array.isArray(payload.reference_notes) ? payload.reference_notes : [];
  const referenceNotes = referenceNotesRaw
    .map((note) => {
      if (typeof note?.note !== "string" || typeof note?.time !== "number") {
        return null;
      }

      return {
        note: note.note,
        time: note.time,
      };
    })
    .filter((note): note is { note: string; time: number } => note !== null);

  const adaptivePlan =
    payload.adaptive_plan && typeof payload.adaptive_plan === "object"
      ? (payload.adaptive_plan as Record<string, unknown>)
      : null;
  const songAdaptivePlan =
    payload.song_adaptive_plan && typeof payload.song_adaptive_plan === "object"
      ? (payload.song_adaptive_plan as Record<string, unknown>)
      : null;

  return {
    data: {
      contentType: typeof payload.content_type === "string" ? payload.content_type : null,
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
      recommendedTempo:
        typeof adaptivePlan?.recommended_tempo === "number"
          ? adaptivePlan.recommended_tempo
          : typeof songAdaptivePlan?.recommended_tempo === "number"
            ? songAdaptivePlan.recommended_tempo
          : null,
      songRecommendedTempo:
        typeof songAdaptivePlan?.recommended_tempo === "number"
          ? songAdaptivePlan.recommended_tempo
          : null,
      focusArea:
        typeof adaptivePlan?.focus_area === "string"
          ? adaptivePlan.focus_area
          : null,
      focusPhrase:
        typeof songAdaptivePlan?.focus_phrase === "number"
          ? songAdaptivePlan.focus_phrase
          : null,
      targetDrill:
        typeof adaptivePlan?.target_drill === "string"
          ? adaptivePlan.target_drill
          : null,
      exerciseMode:
        typeof adaptivePlan?.exercise_mode === "string"
          ? adaptivePlan.exercise_mode
          : null,
      variationStrategy:
        typeof adaptivePlan?.variation_strategy === "string"
          ? adaptivePlan.variation_strategy
          : null,
      tempoFeedback:
        typeof adaptivePlan?.tempo_feedback === "string"
          ? adaptivePlan.tempo_feedback
          : null,
      songRecommendation:
        typeof songAdaptivePlan?.song_recommendation === "string"
          ? songAdaptivePlan.song_recommendation
          : null,
      unlockEvent: Boolean(payload.full_song_unlocked),
      rawFeedback: payload.evaluation?.feedback,
      curriculum: payload.curriculum ? curriculum : null,
      detectedNotes,
      referenceNotes,
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

const clamp01 = (value: number): number => {
  if (value < 0) {
    return 0;
  }

  if (value > 1) {
    return 1;
  }

  return value;
};

const normalizeIndexValue = (value: unknown): number | null => {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }

  if (value <= 1) {
    return clamp01(value);
  }

  if (value <= 100) {
    return clamp01(value / 100);
  }

  return 1;
};

const latestTechniqueFromSessions = (
  sessionsPayload?: SessionsApi | MessagePayload | null,
): number | null => {
  if (!sessionsPayload || isMessagePayload(sessionsPayload)) {
    return null;
  }

  const latest = sessionsPayload.sessions?.[0];
  return normalizeIndexValue(latest?.technique_score);
};

export const normalizeSkillRadar = (
  radarPayload: AnalyticsRadarApi | MessagePayload | null | undefined,
  sessionsPayload?: SessionsApi | MessagePayload | null,
  analyticsSnapshot?: ApiResult<AnalyticsSnapshotNormalized> | null,
): ApiResult<SkillRadarNormalized> => {
  const radarNoData = !radarPayload || isMessagePayload(radarPayload);
  const radar = radarNoData ? null : radarPayload;

  const pitch = normalizeIndexValue(radar?.pitch);
  const rhythm = normalizeIndexValue(radar?.rhythm);
  const consistency = normalizeIndexValue(radar?.consistency);
  const radarComposite = normalizeIndexValue(radar?.composite);
  const radarTechnique = normalizeIndexValue(radar?.technique);
  const radarProgress = normalizeIndexValue(radar?.progress);

  const sessionTechnique = latestTechniqueFromSessions(sessionsPayload);
  const analyticsComposite = normalizeIndexValue(analyticsSnapshot?.data.compositeScore ?? null);

  const technique = radarTechnique ?? sessionTechnique ?? 0;
  const progress = radarProgress ?? analyticsComposite ?? radarComposite ?? 0;

  const composite = radarComposite ?? analyticsComposite ?? progress;

  return {
    data: {
      pitch: pitch ?? 0,
      rhythm: rhythm ?? 0,
      technique,
      consistency: consistency ?? 0,
      progress,
      composite,
      techniqueSource: radarTechnique !== null ? "radar" : sessionTechnique !== null ? "sessions" : "fallback",
      progressSource: radarProgress !== null ? "radar" : analyticsComposite !== null ? "analytics" : "fallback",
    },
    empty: {
      isEmpty: radarNoData,
      message: radarNoData && isMessagePayload(radarPayload)
        ? radarPayload.message
        : radarNoData
          ? "No radar data available."
          : null,
    },
  };
};

const asFiniteNumberOrNull = (value: unknown): number | null => {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
};

const extractSessionsPayload = (
  payload: SessionsApi | MessagePayload | null | undefined,
): SessionsApi | null => {
  if (!payload) {
    return null;
  }

  if (!isMessagePayload(payload)) {
    return payload;
  }

  if (typeof payload.data !== "object" || payload.data === null) {
    return null;
  }

  const data = payload.data as { count?: unknown; sessions?: unknown };
  if (!Array.isArray(data.sessions)) {
    return null;
  }

  return {
    count: typeof data.count === "number" ? data.count : data.sessions.length,
    sessions: data.sessions as SessionsApi["sessions"],
  };
};

export const normalizePracticeHistory = (
  sessionsPayload: SessionsApi | MessagePayload | null | undefined,
  options?: {
    unlockDelta?: number;
    unlockedContentCount?: number;
  },
): ApiResult<PracticeHistoryNormalized> => {
  const payload = extractSessionsPayload(sessionsPayload);
  const rawSessions = Array.isArray(payload?.sessions) ? payload.sessions : [];

  const sessionsWithSourceOrder = rawSessions
    .map((session, sourceOrder) => {
      if (typeof session !== "object" || session === null) {
        return null;
      }

      const entry = session as {
        id?: unknown;
        timestamp?: unknown;
        note_accuracy?: unknown;
        composite_score?: unknown;
        pitch_index?: unknown;
        rhythm_index?: unknown;
        consistency_index?: unknown;
        technique_score?: unknown;
      };

      return {
        sourceOrder,
        session: {
          id: asFiniteNumberOrNull(entry.id),
          timestamp: typeof entry.timestamp === "string" ? entry.timestamp : null,
          noteAccuracy: asFiniteNumberOrNull(entry.note_accuracy),
          compositeScore: asFiniteNumberOrNull(entry.composite_score),
          pitchIndex: asFiniteNumberOrNull(entry.pitch_index),
          rhythmIndex: asFiniteNumberOrNull(entry.rhythm_index),
          consistencyIndex: asFiniteNumberOrNull(entry.consistency_index),
          techniqueScore: asFiniteNumberOrNull(entry.technique_score),
        },
      };
    })
    .filter(
      (
        item,
      ): item is {
        sourceOrder: number;
        session: PracticeHistoryNormalized["sessions"][number];
      } => item !== null,
    );

  const sessions = sessionsWithSourceOrder
    .sort((left, right) => {
      const leftId = left.session.id;
      const rightId = right.session.id;

      if (leftId !== null && rightId !== null && leftId !== rightId) {
        return leftId - rightId;
      }

      const leftTime = left.session.timestamp ? Date.parse(left.session.timestamp) : Number.NaN;
      const rightTime = right.session.timestamp ? Date.parse(right.session.timestamp) : Number.NaN;
      const leftValidTime = Number.isFinite(leftTime);
      const rightValidTime = Number.isFinite(rightTime);

      if (leftValidTime && rightValidTime && leftTime !== rightTime) {
        return leftTime - rightTime;
      }

      return left.sourceOrder - right.sourceOrder;
    })
    .map((item) => item.session);

  const unlockDeltaRaw = options?.unlockDelta;
  const unlockDelta =
    typeof unlockDeltaRaw === "number" && Number.isFinite(unlockDeltaRaw)
      ? Math.max(0, Math.floor(unlockDeltaRaw))
      : 0;

  const unlockedContentCountRaw = options?.unlockedContentCount;
  const unlockedContentCount =
    typeof unlockedContentCountRaw === "number" && Number.isFinite(unlockedContentCountRaw)
      ? Math.max(0, Math.floor(unlockedContentCountRaw))
      : 0;

  return {
    data: {
      sessions,
      unlockDelta,
      unlockedContentCount,
    },
    empty: {
      isEmpty: sessions.length === 0,
      message:
        sessions.length === 0
          ? isMessagePayload(sessionsPayload)
            ? sessionsPayload.message
            : "No sessions available."
          : null,
    },
  };
};
