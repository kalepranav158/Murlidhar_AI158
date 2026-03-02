import { apiRequest } from "./client";
import type { AskRequestApi, AskResponseApi, MessagePayload } from "../types/api";

export const askGuru = async (userId: string, payload: AskRequestApi) => {
  return apiRequest<AskResponseApi | MessagePayload>("/ask/", {
    method: "POST",
    query: { user_id: userId },
    body: payload,
  });
};
