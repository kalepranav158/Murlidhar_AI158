import { useState } from "react";
import { submitAlankarPractice, submitFullSongPractice, submitSongPractice } from "../api";
import { initialAsyncState, type AsyncState } from "../types/ui";

export function usePracticeSession() {
  const [practiceState, setPracticeState] = useState<AsyncState<unknown>>(initialAsyncState());

  const submitAlankar = async (input: {
    userId: string;
    alankarId: string;
    phraseIndex: number;
    tempo?: number;
    audioFile: File;
  }) => {
    setPracticeState({ loading: true, error: null, data: null });
    try {
      const payload = await submitAlankarPractice(input);
      setPracticeState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setPracticeState({ loading: false, error: message, data: null });
      throw error;
    }
  };

  const submitSong = async (input: {
    userId: string;
    songId: string;
    phraseIndex: number;
    tempo?: number;
    audioFile: File;
  }) => {
    setPracticeState({ loading: true, error: null, data: null });
    try {
      const payload = await submitSongPractice(input);
      setPracticeState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setPracticeState({ loading: false, error: message, data: null });
      throw error;
    }
  };

  const submitFullSong = async (input: {
    userId: string;
    songId: string;
    audioFile: File;
  }) => {
    setPracticeState({ loading: true, error: null, data: null });
    try {
      const payload = await submitFullSongPractice(input);
      setPracticeState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setPracticeState({ loading: false, error: message, data: null });
      throw error;
    }
  };

  return {
    practiceState,
    submitAlankar,
    submitSong,
    submitFullSong,
  };
}
