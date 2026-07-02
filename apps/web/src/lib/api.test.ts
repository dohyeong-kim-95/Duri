import { describe, expect, it } from "vitest";

import { getApiBaseUrl, getWebSocketProbeUrl } from "./api";

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
});
