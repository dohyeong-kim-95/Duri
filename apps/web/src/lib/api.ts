const DEFAULT_API_BASE_URL = "http://localhost:8000";

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
