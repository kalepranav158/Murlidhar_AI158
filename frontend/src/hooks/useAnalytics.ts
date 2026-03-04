import { useCallback, useState } from "react";
import { getAnalyticsTrend, getStudentAnalytics } from "../api";
import { initialAsyncState, type AsyncState } from "../types/ui";
import type { AnalyticsTrendApi, MessagePayload } from "../types/api";
import type { AnalyticsSnapshotNormalized, ApiResult } from "../types/normalized";

export function useAnalytics() {
  const [analyticsState, setAnalyticsState] =
    useState<AsyncState<ApiResult<AnalyticsSnapshotNormalized>>>(initialAsyncState());
  const [trendState, setTrendState] =
    useState<AsyncState<AnalyticsTrendApi | MessagePayload>>(initialAsyncState());

  const loadAnalytics = useCallback(async (userId: string) => {
    setAnalyticsState({ loading: true, error: null, data: null });
    try {
      const payload = await getStudentAnalytics(userId);
      setAnalyticsState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setAnalyticsState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  const loadTrend = useCallback(async (userId: string) => {
    setTrendState({ loading: true, error: null, data: null });
    try {
      const payload = await getAnalyticsTrend(userId);
      setTrendState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setTrendState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  const loadProgress = useCallback(async (userId: string) => {
    setAnalyticsState({ loading: true, error: null, data: null });
    setTrendState({ loading: true, error: null, data: null });

    try {
      const [analytics, trend] = await Promise.all([
        getStudentAnalytics(userId),
        getAnalyticsTrend(userId),
      ]);

      setAnalyticsState({ loading: false, error: null, data: analytics });
      setTrendState({ loading: false, error: null, data: trend });
      return { analytics, trend };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setAnalyticsState({ loading: false, error: message, data: null });
      setTrendState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  return {
    analyticsState,
    trendState,
    loadAnalytics,
    loadTrend,
    loadProgress,
  };
}
