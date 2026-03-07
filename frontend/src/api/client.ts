import { clearStoredAuth, getStoredAuthToken } from "../utils/authStorage";

export const API_BASE_URL =
  (import.meta as unknown as { env?: { VITE_API_BASE_URL?: string } }).env
    ?.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

const DEFAULT_TIMEOUT_MS = 12000;
const DEFAULT_GET_RETRIES = 1;

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type RequestConfig = {
  method?: HttpMethod;
  query?: Record<string, string | number | boolean | null | undefined>;
  body?: unknown;
  headers?: Record<string, string>;
  timeoutMs?: number;
  retries?: number;
};

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

const toQueryString = (query?: RequestConfig["query"]): string => {
  if (!query) return "";

  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.set(key, String(value));
    }
  });

  const text = params.toString();
  return text ? `?${text}` : "";
};

const toError = async (response: Response): Promise<ApiError> => {
  let payload: unknown;

  try {
    payload = await response.json();
  } catch {
    payload = await response.text();
  }

  const messageFromPayload =
    typeof payload === "object" && payload !== null
      ? ((payload as { detail?: string; message?: string }).detail ??
        (payload as { detail?: string; message?: string }).message)
      : null;

  return new ApiError(
    messageFromPayload || `Request failed with status ${response.status}`,
    response.status,
    payload,
  );
};

const requestOnce = async <T>(
  path: string,
  config: RequestConfig,
): Promise<T> => {
  const method = config.method ?? "GET";
  const url = `${API_BASE_URL}${path}${toQueryString(config.query)}`;
  const timeoutMs = config.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const authToken = getStoredAuthToken();

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method,
      signal: controller.signal,
      headers: {
        ...(config.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...config.headers,
      },
      body:
        config.body === undefined
          ? undefined
          : config.body instanceof FormData
            ? config.body
            : JSON.stringify(config.body),
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearStoredAuth();
      }
      throw await toError(response);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(`Request timeout after ${timeoutMs}ms`, 408, null);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
};

export const apiRequest = async <T>(
  path: string,
  config: RequestConfig = {},
): Promise<T> => {
  const method = config.method ?? "GET";
  const retries = config.retries ?? (method === "GET" ? DEFAULT_GET_RETRIES : 0);

  let attempt = 0;
  while (true) {
    try {
      return await requestOnce<T>(path, config);
    } catch (error) {
      if (attempt >= retries) {
        throw error;
      }
      attempt += 1;
    }
  }
};
