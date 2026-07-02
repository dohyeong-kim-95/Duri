import { describe, expect, it } from "vitest";

import {
  ApiRequestError,
  fetchTimeline,
  formatTimelineTime,
  getApiBaseUrl,
  getWebSocketProbeUrl,
  readStoredAccessToken,
  searchTimeline,
  summarizeTimelineLog,
} from "./api";

describe("API endpoint configuration", () => {
  it("uses the local FastAPI server by default", () => {
    expect(getApiBaseUrl(undefined)).toBe("http://localhost:8000");
  });

  it("normalizes configured API base URLs", () => {
    expect(getApiBaseUrl("https://duri.example.test///")).toBe("https://duri.example.test");
  });

  it("builds the FastAPI WebSocket probe URL from the API base URL", () => {
    expect(getWebSocketProbeUrl("https://duri.example.test/api")).toBe(
      "wss://duri.example.test/ws/probe",
    );
  });

  it("reads the stored access token when future auth flow provides one", () => {
    const storage = new Map<string, string>();
    storage.set("duri.accessToken", " token-value ");

    expect(
      readStoredAccessToken({
        getItem: (key: string) => storage.get(key) ?? null,
      } as Storage),
    ).toBe("token-value");
  });

  it("fetches the authenticated timeline endpoint", async () => {
    const calls: Array<{ input: string; authorization: string | null }> = [];

    const response = await fetchTimeline({
      apiBaseUrl: "https://duri.example.test",
      accessToken: "access-token",
      filters: { period: "2026-07", type: "Message" },
      fetcher: async (input, init) => {
        const headers = new Headers(init?.headers);
        calls.push({
          input: input.toString(),
          authorization: headers.get("Authorization"),
        });
        return Response.json({ items: [{ id: "01J", type: "Message" }] });
      },
    });

    expect(calls).toEqual([
      {
        input: "https://duri.example.test/timeline?period=2026-07&type=Message",
        authorization: "Bearer access-token",
      },
    ]);
    expect(response.items[0].id).toBe("01J");
  });

  it("fetches search results with an encoded query", async () => {
    const calls: string[] = [];

    await searchTimeline({
      apiBaseUrl: "https://duri.example.test",
      accessToken: "access-token",
      query: "김치 찌개",
      filters: { period: "2026-07", type: "Photo" },
      fetcher: async (input) => {
        calls.push(input.toString());
        return Response.json({ results: [] });
      },
    });

    expect(calls).toEqual([
      "https://duri.example.test/search?period=2026-07&type=Photo&q=%EA%B9%80%EC%B9%98+%EC%B0%8C%EA%B0%9C",
    ]);
  });

  it("raises a typed error when the API rejects the request", async () => {
    await expect(
      fetchTimeline({
        apiBaseUrl: "https://duri.example.test",
        accessToken: "bad-token",
        fetcher: async () => new Response("Unauthorized", { status: 401 }),
      }),
    ).rejects.toMatchObject(new ApiRequestError("API request failed", 401));
  });

  it("formats and summarizes timeline logs for display", () => {
    expect(formatTimelineTime("2026-07-12T19:28:00+09:00")).toMatch(/\d{2}:\d{2}/);
    expect(
      summarizeTimelineLog({
        id: "01J_MSG",
        type: "Message",
        created_at: "2026-07-12T19:28:00+09:00",
        actor_id: "01J_USER_1",
        payload: { text: "오늘 저녁 뭐 먹을까?" },
      }),
    ).toBe("오늘 저녁 뭐 먹을까?");
    expect(
      summarizeTimelineLog({
        id: "01J_PHOTO",
        type: "Photo",
        created_at: "2026-07-12T19:30:00+09:00",
        actor_id: "01J_USER_1",
        media_refs: [{ original_filename: "dinner.jpg" }],
      }),
    ).toBe("Photo: dinner.jpg");
  });
});
