import { apiRequest } from "./client";
import type { SongListItemApi } from "../types/api";

export const listSongs = async (input?: {
  contentType?: "alankar" | "song" | "melody" | string;
}) => {
  return apiRequest<SongListItemApi[]>("/songs/", {
    method: "GET",
    query: input?.contentType
      ? {
          content_type: input.contentType,
        }
      : undefined,
  });
};
