import { apiRequest } from "./client";
import { normalizePracticeResult } from "./adapters";
import type { MessagePayload, PracticeApi } from "../types/api";

const appendFile = (audioFile: File) => {
  const formData = new FormData();
  formData.append("file", audioFile);
  return formData;
};

export const submitAlankarPractice = async (input: {
  userId: string;
  alankarId: string;
  phraseIndex: number;
  tempo?: number;
  audioFile: File;
}) => {
  const payload = await apiRequest<PracticeApi | MessagePayload>(
    `/practice/alankar/${encodeURIComponent(input.userId)}/${encodeURIComponent(input.alankarId)}/${input.phraseIndex}`,
    {
      method: "POST",
      query: {
        tempo: input.tempo ?? 60,
      },
      body: appendFile(input.audioFile),
      timeoutMs: 30000,
      retries: 0,
    },
  );

  return normalizePracticeResult(payload);
};

export const submitSongPractice = async (input: {
  userId: string;
  songId: string;
  phraseIndex: number;
  tempo?: number;
  audioFile: File;
}) => {
  const payload = await apiRequest<PracticeApi | MessagePayload>(
    `/practice/song/${encodeURIComponent(input.userId)}/${encodeURIComponent(input.songId)}/${input.phraseIndex}`,
    {
      method: "POST",
      query: {
        tempo: input.tempo ?? 60,
      },
      body: appendFile(input.audioFile),
      timeoutMs: 30000,
      retries: 0,
    },
  );

  return normalizePracticeResult(payload);
};

export const submitFullSongPractice = async (input: {
  userId: string;
  songId: string;
  audioFile: File;
}) => {
  const payload = await apiRequest<PracticeApi | MessagePayload>(
    `/practice/practice/song/full/${encodeURIComponent(input.userId)}/${encodeURIComponent(input.songId)}`,
    {
      method: "POST",
      body: appendFile(input.audioFile),
      timeoutMs: 30000,
      retries: 0,
    },
  );

  return normalizePracticeResult(payload);
};
