import { useCallback, useState } from "react";
import {
  getAnalyticsRadar,
  getSessions,
  getStudentAnalytics,
  normalizeSkillRadar,
} from "../../../api";
import type { ApiResult, SkillRadarNormalized } from "../../../types/normalized";
import { initialAsyncState, type AsyncState } from "../../../types/ui";

export function useSkillRadar() {
  const [radarState, setRadarState] =
    useState<AsyncState<ApiResult<SkillRadarNormalized>>>(initialAsyncState());

  const loadSkillRadar = useCallback(async (userId: string) => {
    setRadarState({ loading: true, error: null, data: null });

    try {
      const [radarPayload, sessionsPayload, analyticsSnapshot] = await Promise.all([
        getAnalyticsRadar(userId),
        getSessions(userId, 1),
        getStudentAnalytics(userId),
      ]);

      const normalized = normalizeSkillRadar(
        radarPayload,
        sessionsPayload,
        analyticsSnapshot,
      );

      setRadarState({ loading: false, error: null, data: normalized });
      return normalized;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setRadarState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  return {
    radarState,
    loadSkillRadar,
  };
}
