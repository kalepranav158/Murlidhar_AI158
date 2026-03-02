import { apiRequest } from "./client";
import type { MessagePayload, SessionsApi } from "../types/api";

export const getSessions = async (userId: string, limit = 30) => {
  return apiRequest<SessionsApi | MessagePayload>("/sessions/", {
    method: "GET",
    query: {
      user_id: userId,
      limit,
    },
  });
};
