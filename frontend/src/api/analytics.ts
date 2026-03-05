import { apiRequest } from "./client";
import type {
  AnalyticsConsistencyApi,
  AnalyticsConsistencyDetailsApi,
  AnalyticsPitchStabilityApi,
  AnalyticsRadarApi,
  AnalyticsRecommendationApi,
  AnalyticsSkillLevelApi,
  AnalyticsSummaryApi,
  AnalyticsTrendApi,
  AnalyticsWeakestPhraseApi,
  LearningDifficultyApi,
  LearningModelStatusApi,
  LearningRecommendationApi,
  MessagePayload,
  StudentAnalyticsApi,
} from "../types/api";

export const getAnalyticsDashboard = async (userId: string) => {
  return apiRequest<StudentAnalyticsApi | MessagePayload>("/analytics/dashboard", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsTrend = async (userId: string) => {
  return apiRequest<AnalyticsTrendApi | MessagePayload>("/analytics/trend", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsConsistency = async (userId: string) => {
  return apiRequest<AnalyticsConsistencyApi | MessagePayload>("/analytics/consistency", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsSummary = async (userId: string) => {
  return apiRequest<AnalyticsSummaryApi | MessagePayload>("/analytics/summary", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsSkillLevel = async (userId: string) => {
  return apiRequest<AnalyticsSkillLevelApi | MessagePayload>("/analytics/skill-level", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsPitchStabilityControl = async (userId: string) => {
  return apiRequest<AnalyticsPitchStabilityApi | MessagePayload>(
    "/analytics/pitch-stability-control",
    {
      method: "GET",
      query: { user_id: userId },
    },
  );
};

export const getAnalyticsRecommendationAdaptivePlan = async (userId: string) => {
  return apiRequest<AnalyticsRecommendationApi | MessagePayload>(
    "/analytics/recommendation-adaptive_plan",
    {
      method: "GET",
      query: { user_id: userId },
    },
  );
};

export const getAnalyticsConsistencyDetails = async (userId: string) => {
  return apiRequest<AnalyticsConsistencyDetailsApi | MessagePayload>(
    "/analytics/consistency-details",
    {
      method: "GET",
      query: { user_id: userId },
    },
  );
};

export const getAnalyticsTestDashboard = async (userId: string) => {
  return apiRequest<Record<string, unknown> | MessagePayload>("/analytics/test-dashboard", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsRadar = async (userId: string) => {
  return apiRequest<AnalyticsRadarApi | MessagePayload | null>("/analytics/radar", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsSkillEvolution = async (userId: string) => {
  return apiRequest<Record<string, unknown> | MessagePayload>("/analytics/skill-evolution", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsRisk = async (userId: string) => {
  return apiRequest<Record<string, unknown> | MessagePayload>("/analytics/risk", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsForecast = async (userId: string) => {
  return apiRequest<Record<string, unknown> | MessagePayload>("/analytics/forecast", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsWeakestPhrase = async (userId: string, songId: string) => {
  return apiRequest<AnalyticsWeakestPhraseApi | MessagePayload>(
    "/analytics/song/weakest-phrase",
    {
      method: "GET",
      query: { user_id: userId, song_id: songId },
    },
  );
};

export const getAnalyticsLearningDifficulty = async (userId: string) => {
  return apiRequest<LearningDifficultyApi | MessagePayload>("/analytics/learning/difficulty", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsLearningRecommendation = async (userId: string) => {
  return apiRequest<LearningRecommendationApi | MessagePayload>("/analytics/learning/recommendation", {
    method: "GET",
    query: { user_id: userId },
  });
};

export const getAnalyticsLearningModelStatus = async () => {
  return apiRequest<LearningModelStatusApi | MessagePayload>("/analytics/learning/model-status", {
    method: "GET",
  });
};
