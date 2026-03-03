import { useState } from "react";
import { getStudentCurriculum, getStudentProfile, getStudentStreak } from "../api";
import { initialAsyncState, type AsyncState } from "../types/ui";
import type {
  ApiResult,
  StudentCurriculumNormalized,
  StudentProfileNormalized,
  StudentStreakNormalized,
} from "../types/normalized";

export function useStudentProfile() {
  const [profileState, setProfileState] =
    useState<AsyncState<ApiResult<StudentProfileNormalized>>>(initialAsyncState());
  const [curriculumState, setCurriculumState] =
    useState<AsyncState<ApiResult<StudentCurriculumNormalized>>>(initialAsyncState());
  const [streakState, setStreakState] =
    useState<AsyncState<ApiResult<StudentStreakNormalized>>>(initialAsyncState());

  const loadProfile = async (userId: string) => {
    setProfileState({ loading: true, error: null, data: null });
    try {
      const payload = await getStudentProfile(userId);
      setProfileState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setProfileState({ loading: false, error: message, data: null });
      throw error;
    }
  };

  const loadCurriculum = async (userId: string) => {
    setCurriculumState({ loading: true, error: null, data: null });
    try {
      const payload = await getStudentCurriculum(userId);
      setCurriculumState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setCurriculumState({ loading: false, error: message, data: null });
      throw error;
    }
  };

  const loadStreak = async (userId: string) => {
    setStreakState({ loading: true, error: null, data: null });
    try {
      const payload = await getStudentStreak(userId);
      setStreakState({ loading: false, error: null, data: payload });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setStreakState({ loading: false, error: message, data: null });
      throw error;
    }
  };

  return {
    profileState,
    curriculumState,
    streakState,
    loadProfile,
    loadCurriculum,
    loadStreak,
  };
}
