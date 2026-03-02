import { apiRequest } from "./client";
import type { RootHealthApi } from "../types/api";

export const getRootHealth = async () => {
  return apiRequest<RootHealthApi>("/", {
    method: "GET",
  });
};
