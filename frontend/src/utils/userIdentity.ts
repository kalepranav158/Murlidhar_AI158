import { getStoredAuthSession } from "./authStorage";

const APP_USER_ID_STORAGE_KEY = "venora_user_id";
const APP_USER_ID_FALLBACK = "kalepranav158";

const isBrowser = (): boolean => typeof window !== "undefined";

const normalizeCandidate = (value: string | null | undefined): string | null => {
  if (!value) {
    return null;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  const withoutDomain = trimmed.includes("@") ? trimmed.split("@")[0] : trimmed;
  const normalized = withoutDomain
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[^a-z0-9._-]/g, "");

  return normalized.length > 0 ? normalized : null;
};

const deriveFromSession = (): string | null => {
  const session = getStoredAuthSession();
  if (!session) {
    return null;
  }

  return normalizeCandidate(session.email) ?? normalizeCandidate(session.username);
};

export const getPreferredUserId = (): string => {
  if (!isBrowser()) {
    return APP_USER_ID_FALLBACK;
  }

  const fromStorage = normalizeCandidate(window.localStorage.getItem(APP_USER_ID_STORAGE_KEY));
  if (fromStorage) {
    return fromStorage;
  }

  const fromSession = deriveFromSession();
  const resolved = fromSession ?? APP_USER_ID_FALLBACK;
  window.localStorage.setItem(APP_USER_ID_STORAGE_KEY, resolved);
  return resolved;
};

export const setPreferredUserId = (value: string): string => {
  const normalized = normalizeCandidate(value) ?? APP_USER_ID_FALLBACK;

  if (isBrowser()) {
    window.localStorage.setItem(APP_USER_ID_STORAGE_KEY, normalized);
  }

  return normalized;
};

export const syncPreferredUserIdWithSession = (): string => {
  const fromSession = deriveFromSession();

  if (fromSession) {
    return setPreferredUserId(fromSession);
  }

  return getPreferredUserId();
};
