export const AUTH_TOKEN_STORAGE_KEY = "venora_auth_token";
export const AUTH_SESSION_STORAGE_KEY = "venora_auth_session";

export type StoredAuthSession = {
  username: string;
  authProvider: string;
  email: string | null;
  expiresAt: string | null;
};

const isBrowser = (): boolean => typeof window !== "undefined";

export const getStoredAuthToken = (): string | null => {
  if (!isBrowser()) {
    return null;
  }

  const value = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
  if (!value) {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

export const setStoredAuthToken = (token: string): void => {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
};

export const clearStoredAuthToken = (): void => {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
};

export const getStoredAuthSession = (): StoredAuthSession | null => {
  if (!isBrowser()) {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<StoredAuthSession>;
    if (!parsed || typeof parsed.username !== "string") {
      return null;
    }

    return {
      username: parsed.username,
      authProvider:
        typeof parsed.authProvider === "string" && parsed.authProvider.trim().length > 0
          ? parsed.authProvider
          : "password",
      email: typeof parsed.email === "string" && parsed.email.trim().length > 0 ? parsed.email : null,
      expiresAt: typeof parsed.expiresAt === "string" ? parsed.expiresAt : null,
    };
  } catch {
    return null;
  }
};

export const setStoredAuthSession = (session: StoredAuthSession): void => {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.setItem(AUTH_SESSION_STORAGE_KEY, JSON.stringify(session));
};

export const clearStoredAuthSession = (): void => {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
};

export const clearStoredAuth = (): void => {
  clearStoredAuthToken();
  clearStoredAuthSession();
};
