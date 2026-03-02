import { apiRequest } from "./client";
import type { DebugSessionsApi, MessagePayload } from "../types/api";

export const getDebugSessions = async (userId: string, limit = 10) => {
  return apiRequest<DebugSessionsApi | MessagePayload>(`/debug/sessions/${encodeURIComponent(userId)}`, {
    method: "GET",
    query: { limit },
  });
};

export const getDebugAlankar = async (userId: string, alankarId: string) => {
  return apiRequest<Record<string, unknown> | MessagePayload>(
    `/debug/alankar/${encodeURIComponent(userId)}/${encodeURIComponent(alankarId)}`,
    {
      method: "GET",
    },
  );
};

export const getDebugPhrase = async (userId: string, songId: string, phraseId: number) => {
  return apiRequest<Record<string, unknown> | MessagePayload>(
    `/debug/phrase/${encodeURIComponent(userId)}/${encodeURIComponent(songId)}/${phraseId}`,
    {
      method: "GET",
    },
  );
};

export const getDebugAnalytics = async (userId: string, limit = 30) => {
  return apiRequest<Record<string, unknown> | MessagePayload>(
    `/debug/analytics/${encodeURIComponent(userId)}`,
    {
      method: "GET",
      query: { limit },
    },
  );
};

export const getDebugStudent = async (userId: string) => {
  return apiRequest<Record<string, unknown> | MessagePayload>(
    `/debug/student/${encodeURIComponent(userId)}`,
    {
      method: "GET",
    },
  );
};
