import { useCallback, useState } from "react";
import {
  getAnalyticsLearningDifficulty,
  getAnalyticsLearningModelStatus,
  getAnalyticsLearningRecommendation,
  getAnalyticsTrend,
  getStudentAnalytics,
} from "../api";
import { initialAsyncState, type AsyncState } from "../types/ui";
import type {
  AnalyticsTrendApi,
  LearningDifficultyApi,
  LearningModelStatusApi,
  LearningRecommendationApi,
  MessagePayload,
} from "../types/api";
import type { AnalyticsSnapshotNormalized, ApiResult } from "../types/normalized";

export function useAnalytics() {
  const [analyticsState, setAnalyticsState] =
    useState<AsyncState<ApiResult<AnalyticsSnapshotNormalized>>>(initialAsyncState());
  const [trendState, setTrendState] =
    useState<AsyncState<AnalyticsTrendApi | MessagePayload>>(initialAsyncState());
  const [learningDifficultyState, setLearningDifficultyState] =
    useState<AsyncState<LearningDifficultyApi | MessagePayload>>(initialAsyncState());
  const [learningRecommendationState, setLearningRecommendationState] =
    useState<AsyncState<LearningRecommendationApi | MessagePayload>>(initialAsyncState());
  const [learningModelState, setLearningModelState] =
    useState<AsyncState<LearningModelStatusApi | MessagePayload>>(initialAsyncState());

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

  const loadLearningIntelligence = useCallback(async (userId: string) => {
    setLearningDifficultyState({ loading: true, error: null, data: null });
    setLearningRecommendationState({ loading: true, error: null, data: null });
    setLearningModelState({ loading: true, error: null, data: null });

    try {
      const [difficulty, recommendation, model] = await Promise.all([
        getAnalyticsLearningDifficulty(userId),
        getAnalyticsLearningRecommendation(userId),
        getAnalyticsLearningModelStatus(),
      ]);

      setLearningDifficultyState({ loading: false, error: null, data: difficulty });
      setLearningRecommendationState({ loading: false, error: null, data: recommendation });
      setLearningModelState({ loading: false, error: null, data: model });
      return { difficulty, recommendation, model };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setLearningDifficultyState({ loading: false, error: message, data: null });
      setLearningRecommendationState({ loading: false, error: message, data: null });
      setLearningModelState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  const loadProgress = useCallback(async (userId: string) => {
    setAnalyticsState({ loading: true, error: null, data: null });
    setTrendState({ loading: true, error: null, data: null });
    setLearningDifficultyState({ loading: true, error: null, data: null });
    setLearningRecommendationState({ loading: true, error: null, data: null });
    setLearningModelState({ loading: true, error: null, data: null });

    try {
      const [analytics, trend, difficulty, recommendation, model] = await Promise.all([
        getStudentAnalytics(userId),
        getAnalyticsTrend(userId),
        getAnalyticsLearningDifficulty(userId),
        getAnalyticsLearningRecommendation(userId),
        getAnalyticsLearningModelStatus(),
      ]);

      setAnalyticsState({ loading: false, error: null, data: analytics });
      setTrendState({ loading: false, error: null, data: trend });
      setLearningDifficultyState({ loading: false, error: null, data: difficulty });
      setLearningRecommendationState({ loading: false, error: null, data: recommendation });
      setLearningModelState({ loading: false, error: null, data: model });
      return { analytics, trend, difficulty, recommendation, model };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setAnalyticsState({ loading: false, error: message, data: null });
      setTrendState({ loading: false, error: message, data: null });
      setLearningDifficultyState({ loading: false, error: message, data: null });
      setLearningRecommendationState({ loading: false, error: message, data: null });
      setLearningModelState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  return {
    analyticsState,
    trendState,
    learningDifficultyState,
    learningRecommendationState,
    learningModelState,
    loadAnalytics,
    loadTrend,
    loadLearningIntelligence,
    loadProgress,
  };
}
