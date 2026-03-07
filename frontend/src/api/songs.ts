import { apiRequest } from "./client";
import type { SongListItemApi, SongPhraseReferenceApi } from "../types/api";

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

export const getSongPhraseReference = async (input: {
  songId: string;
  phraseIndex: number;
}) => {
  return apiRequest<SongPhraseReferenceApi>(
    `/songs/${encodeURIComponent(input.songId)}/phrase/${input.phraseIndex}`,
    {
      method: "GET",
    },
  );
};
