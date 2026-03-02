import { apiRequest } from "./client";
import type { SongListItemApi } from "../types/api";

export const listSongs = async () => {
  return apiRequest<SongListItemApi[]>("/songs/", {
    method: "GET",
  });
};
