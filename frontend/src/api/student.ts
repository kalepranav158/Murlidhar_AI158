import { apiRequest } from "./client";
import {
  normalizeAnalytics,
  normalizeCurriculum,
  normalizeProfile,
  normalizeStreak,
} from "./adapters";
import type {
  MessagePayload,
  SessionsApi,
  StudentAnalyticsApi,
  StudentCurriculumApi,
  StudentProfileApi,
  StudentStreakApi,
} from "../types/api";

export const getStudentProfile = async (userId: string) => {
  const payload = await apiRequest<StudentProfileApi | MessagePayload>("/student/profile", {
    method: "GET",
    query: { user_id: userId },
  });

  return normalizeProfile(payload);
};

export const getStudentCurriculum = async (userId: string) => {
  const payload = await apiRequest<StudentCurriculumApi | MessagePayload>("/student/curriculum", {
    method: "GET",
    query: { user_id: userId },
  });

  return normalizeCurriculum(payload);
};

export const getStudentStreak = async (userId: string) => {
  const payload = await apiRequest<StudentStreakApi | MessagePayload>("/student/streak", {
    method: "GET",
    query: { user_id: userId },
  });

  return normalizeStreak(payload);
};

export const getStudentAnalytics = async (userId: string) => {
  const [analyticsPayload, streakPayload, sessionsPayload] = await Promise.all([
    apiRequest<StudentAnalyticsApi | MessagePayload>("/student/analytics", {
      method: "GET",
      query: { user_id: userId },
    }),
    apiRequest<StudentStreakApi | MessagePayload>("/student/streak", {
      method: "GET",
      query: { user_id: userId },
    }),
    apiRequest<SessionsApi | MessagePayload>("/sessions/", {
      method: "GET",
      query: { user_id: userId, limit: 30 },
    }),
  ]);

  return normalizeAnalytics(analyticsPayload, streakPayload, sessionsPayload);
};
