import { apiRequest } from "./client";
import type {
  AuthGoogleLoginRequestApi,
  AuthLoginRequestApi,
  AuthLoginResponseApi,
  AuthLogoutResponseApi,
  AuthVerifyResponseApi,
} from "../types/api";

export const loginAuth = async (payload: AuthLoginRequestApi) => {
  return apiRequest<AuthLoginResponseApi>("/auth/login", {
    method: "POST",
    body: payload,
    retries: 0,
  });
};

export const verifyAuth = async () => {
  return apiRequest<AuthVerifyResponseApi>("/auth/verify", {
    method: "GET",
    retries: 0,
  });
};

export const loginGoogleAuth = async (payload: AuthGoogleLoginRequestApi) => {
  return apiRequest<AuthLoginResponseApi>("/auth/google", {
    method: "POST",
    body: payload,
    retries: 0,
  });
};

export const logoutAuth = async () => {
  return apiRequest<AuthLogoutResponseApi>("/auth/logout", {
    method: "POST",
    retries: 0,
  });
};
