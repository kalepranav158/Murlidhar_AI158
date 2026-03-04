import { useCallback, useState } from "react";
import {
  getAnalyticsRecommendationAdaptivePlan,
} from "../../../api";
import type {
  AnalyticsRecommendationApi,
  MessagePayload,
} from "../../../types/api";
import { initialAsyncState, type AsyncState } from "../../../types/ui";
import {
  mapAnalyticsRecommendationToCoach,
} from "../mappers";
import type {
  AdaptiveCoachRecommendation,
} from "../types";

export function useAdaptiveCoach() {
  const [recommendationState, setRecommendationState] =
    useState<AsyncState<AdaptiveCoachRecommendation | null>>(initialAsyncState());

  const loadRecommendation = useCallback(async (userId: string) => {
    setRecommendationState({ loading: true, error: null, data: null });

    try {
      const payload =
        await getAnalyticsRecommendationAdaptivePlan(userId) as
          | AnalyticsRecommendationApi
          | MessagePayload;
      const mapped = mapAnalyticsRecommendationToCoach(payload);

      setRecommendationState({
        loading: false,
        error: null,
        data: mapped,
      });

      return mapped;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setRecommendationState({ loading: false, error: message, data: null });
      throw error;
    }
  }, []);

  return {
    recommendationState,
    loadRecommendation,
  };
}
