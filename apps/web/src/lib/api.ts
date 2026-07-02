const DEFAULT_API_BASE_URL = "http://localhost:8000";
const ACCESS_TOKEN_STORAGE_KEY = "duri.accessToken";

export type TimelineLog = {
  id: string;
  type: "Message" | "Photo" | string;
  created_at: string;
  actor_id: string;
  actor_display_name?: string;
  period?: string;
  payload?: {
    text?: string;
    caption?: string | null;
    media_ref_id?: string;
    [key: string]: unknown;
  };
  metadata?: Record<string, unknown>;
  media_refs?: Array<{
    original_filename?: string;
    mime_type?: string;
    storage_path?: string;
    [key: string]: unknown;
  }>;
};

export type TimelineResponse = {
  items: TimelineLog[];
};

export type SearchResponse = {
  results: TimelineLog[];
};

type Fetcher = (input: string | URL, init?: RequestInit) => Promise<Response>;

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

export function getApiBaseUrl(envValue = process.env.NEXT_PUBLIC_API_BASE_URL): string {
  const value = envValue?.trim();
  if (!value) {
    return DEFAULT_API_BASE_URL;
  }

  return value.replace(/\/+$/, "");
}

export function getWebSocketProbeUrl(apiBaseUrl = getApiBaseUrl()): string {
  const url = new URL(apiBaseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/probe";
  url.search = "";
  url.hash = "";
  return url.toString();
}

export function readStoredAccessToken(storage: Storage | undefined = safeLocalStorage()): string {
  return storage?.getItem(ACCESS_TOKEN_STORAGE_KEY)?.trim() ?? "";
}

export async function fetchTimeline({
  apiBaseUrl = getApiBaseUrl(),
  accessToken,
  fetcher = fetch,
}: {
  apiBaseUrl?: string;
  accessToken: string;
  fetcher?: Fetcher;
}): Promise<TimelineResponse> {
  return requestJson<TimelineResponse>({
    apiBaseUrl,
    path: "/timeline",
    accessToken,
    fetcher,
  });
}

export async function searchTimeline({
  apiBaseUrl = getApiBaseUrl(),
  accessToken,
  query,
  fetcher = fetch,
}: {
  apiBaseUrl?: string;
  accessToken: string;
  query: string;
  fetcher?: Fetcher;
}): Promise<SearchResponse> {
  return requestJson<SearchResponse>({
    apiBaseUrl,
    path: `/search?q=${encodeURIComponent(query)}`,
    accessToken,
    fetcher,
  });
}

export function formatTimelineTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--:--";
  }
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

export function summarizeTimelineLog(log: TimelineLog): string {
  if (log.type === "Message" && typeof log.payload?.text === "string") {
    return log.payload.text;
  }

  if (log.type === "Photo") {
    const filename = log.media_refs?.[0]?.original_filename;
    return filename ? `Photo: ${filename}` : "Photo";
  }

  return log.type;
}

function safeLocalStorage(): Storage | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.localStorage;
}

async function requestJson<T>({
  apiBaseUrl,
  path,
  accessToken,
  fetcher,
}: {
  apiBaseUrl: string;
  path: string;
  accessToken: string;
  fetcher: Fetcher;
}): Promise<T> {
  const response = await fetcher(new URL(path, `${apiBaseUrl}/`), {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new ApiRequestError("API request failed", response.status);
  }

  return (await response.json()) as T;
}
