import { useCallback, useRef, useState } from "react";
import {
  getSessions,
  getStudentProfile,
  normalizePracticeHistory,
} from "../../../api";
import type {
  ApiResult,
  PracticeHistoryNormalized,
} from "../../../types/normalized";
import { initialAsyncState, type AsyncState } from "../../../types/ui";

export function usePracticeHistory() {
  const [historyState, setHistoryState] =
    useState<AsyncState<ApiResult<PracticeHistoryNormalized>>>(initialAsyncState());
  const previousUnlockedCountRef = useRef<number | null>(null);

  const loadPracticeHistory = useCallback(async (userId: string, limit = 25) => {
    setHistoryState({ loading: true, error: null, data: null });

    const boundedLimit = Number.isFinite(limit)
      ? Math.min(100, Math.max(1, Math.floor(limit)))
      : 25;

    try {
      const [sessionsPayload, profilePayload] = await Promise.all([
        getSessions(userId, boundedLimit),
        getStudentProfile(userId),
      ]);

      const unlockedContentCount = profilePayload.data.unlockedContent.length;
      const previousUnlockedCount = previousUnlockedCountRef.current;
      const unlockDelta =
        previousUnlockedCount === null
          ? 0
          : Math.max(0, unlockedContentCount - previousUnlockedCount);

      previousUnlockedCountRef.current = unlockedContentCount;

      const normalized = normalizePracticeHistory(sessionsPayload, {
        unlockDelta,
        unlockedContentCount,
      });

      setHistoryState({ loading: false, error: null, data: normalized });
      return normalized;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setHistoryState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  return {
    historyState,
    loadPracticeHistory,
  };
}
