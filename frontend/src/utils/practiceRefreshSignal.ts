export type PracticeRefreshSignal = {
  userId: string;
  submittedAt: number;
};

export type PracticeRefreshConsumer = "skill-radar" | "practice-history";

const SIGNAL_STORAGE_KEY = "murlidhar:practice-refresh:latest";
const CONSUMER_STORAGE_KEY_PREFIX = "murlidhar:practice-refresh:handled:";
const PRACTICE_REFRESH_EVENT = "murlidhar:practice-refresh";

const isBrowser = () => typeof window !== "undefined";

const asSignal = (value: unknown): PracticeRefreshSignal | null => {
  if (typeof value !== "object" || value === null) {
    return null;
  }

  const entry = value as { userId?: unknown; submittedAt?: unknown };
  if (typeof entry.userId !== "string" || typeof entry.submittedAt !== "number") {
    return null;
  }

  if (!Number.isFinite(entry.submittedAt)) {
    return null;
  }

  const userId = entry.userId.trim();
  if (!userId) {
    return null;
  }

  return {
    userId,
    submittedAt: entry.submittedAt,
  };
};

const getHandledKey = (consumer: PracticeRefreshConsumer): string => {
  return `${CONSUMER_STORAGE_KEY_PREFIX}${consumer}`;
};

const getHandledTimestamp = (consumer: PracticeRefreshConsumer): number => {
  if (!isBrowser()) {
    return 0;
  }

  const raw = window.sessionStorage.getItem(getHandledKey(consumer));
  if (!raw) {
    return 0;
  }

  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
};

export const emitPracticeRefreshSignal = (userId: string): PracticeRefreshSignal | null => {
  if (!isBrowser()) {
    return null;
  }

  const normalizedUserId = userId.trim();
  if (!normalizedUserId) {
    return null;
  }

  const signal: PracticeRefreshSignal = {
    userId: normalizedUserId,
    submittedAt: Date.now(),
  };

  window.sessionStorage.setItem(SIGNAL_STORAGE_KEY, JSON.stringify(signal));
  window.dispatchEvent(
    new CustomEvent<PracticeRefreshSignal>(PRACTICE_REFRESH_EVENT, {
      detail: signal,
    }),
  );

  return signal;
};

export const getLatestPracticeRefreshSignal = (): PracticeRefreshSignal | null => {
  if (!isBrowser()) {
    return null;
  }

  const raw = window.sessionStorage.getItem(SIGNAL_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return asSignal(JSON.parse(raw));
  } catch {
    return null;
  }
};

export const isPracticeRefreshPending = (
  consumer: PracticeRefreshConsumer,
  signal: PracticeRefreshSignal,
  userId: string,
): boolean => {
  const normalizedUserId = userId.trim();
  if (!normalizedUserId) {
    return false;
  }

  if (signal.userId !== normalizedUserId) {
    return false;
  }

  return getHandledTimestamp(consumer) < signal.submittedAt;
};

export const markPracticeRefreshHandled = (
  consumer: PracticeRefreshConsumer,
  signal: PracticeRefreshSignal,
): void => {
  if (!isBrowser()) {
    return;
  }

  window.sessionStorage.setItem(getHandledKey(consumer), String(signal.submittedAt));
};

export const subscribePracticeRefreshSignal = (
  handler: (signal: PracticeRefreshSignal) => void,
): (() => void) => {
  if (!isBrowser()) {
    return () => undefined;
  }

  const listener = (event: Event) => {
    const customEvent = event as CustomEvent<PracticeRefreshSignal>;
    const signal = asSignal(customEvent.detail);
    if (!signal) {
      return;
    }

    handler(signal);
  };

  window.addEventListener(PRACTICE_REFRESH_EVENT, listener as EventListener);

  return () => {
    window.removeEventListener(PRACTICE_REFRESH_EVENT, listener as EventListener);
  };
};