"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  ApiRequestError,
  TimelineLog,
  fetchTimeline,
  formatTimelineTime,
  readStoredAccessToken,
  searchTimeline,
  summarizeTimelineLog,
} from "@/lib/api";

type LoadState = "idle" | "loading" | "ready" | "locked" | "error";

export function TimelineWorkspace({
  apiBaseUrl,
  websocketUrl,
}: {
  apiBaseUrl: string;
  websocketUrl: string;
}) {
  const [accessToken, setAccessToken] = useState("");
  const [items, setItems] = useState<TimelineLog[]>([]);
  const [query, setQuery] = useState("");
  const [state, setState] = useState<LoadState>("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = readStoredAccessToken();
    setAccessToken(token);

    if (!token) {
      setState("locked");
      return;
    }

    void loadTimeline(token);
  }, [apiBaseUrl]);

  const statusText = useMemo(() => {
    if (state === "loading") {
      return "Loading";
    }
    if (state === "locked") {
      return "Session unavailable";
    }
    if (state === "error") {
      return error || "Request failed";
    }
    return `${items.length} records`;
  }, [error, items.length, state]);

  async function loadTimeline(token = accessToken) {
    setState("loading");
    setError("");

    try {
      const response = await fetchTimeline({ apiBaseUrl, accessToken: token });
      setItems(response.items);
      setState("ready");
    } catch (caught) {
      handleRequestError(caught);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!accessToken) {
      setState("locked");
      return;
    }

    setState("loading");
    setError("");

    try {
      if (!query.trim()) {
        await loadTimeline();
        return;
      }

      const response = await searchTimeline({
        apiBaseUrl,
        accessToken,
        query,
      });
      setItems(response.results);
      setState("ready");
    } catch (caught) {
      handleRequestError(caught);
    }
  }

  function handleRequestError(caught: unknown) {
    if (caught instanceof ApiRequestError && caught.status === 401) {
      setState("locked");
      setError("Session unavailable");
      return;
    }

    setState("error");
    setError("Request failed");
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">Duri</div>
        <form className="search-form" onSubmit={handleSearch}>
          <label htmlFor="timeline-search">Search</label>
          <input
            id="timeline-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            disabled={!accessToken || state === "loading"}
            autoComplete="off"
          />
          <button type="submit" disabled={!accessToken || state === "loading"}>
            Search
          </button>
        </form>
      </header>

      <div className="workspace">
        <aside className="side-panel" aria-label="Connection status">
          <dl className="connection-list">
            <div>
              <dt>Status</dt>
              <dd>{statusText}</dd>
            </div>
            <div>
              <dt>HTTP</dt>
              <dd>{apiBaseUrl}</dd>
            </div>
            <div>
              <dt>WS</dt>
              <dd>{websocketUrl}</dd>
            </div>
          </dl>
        </aside>

        <section className="timeline-panel" aria-label="Timeline">
          {state === "loading" ? <p className="empty-row">Loading</p> : null}
          {state !== "loading" && items.length === 0 ? (
            <p className="empty-row">{state === "locked" ? "Session unavailable" : "No records"}</p>
          ) : null}
          {items.map((item) => (
            <article className="timeline-item" key={item.id}>
              <time dateTime={item.created_at}>{formatTimelineTime(item.created_at)}</time>
              <div className="timeline-copy">
                <div className="timeline-meta">
                  <span>{item.actor_display_name || item.actor_id}</span>
                  <span>{item.type}</span>
                </div>
                <p>{summarizeTimelineLog(item)}</p>
              </div>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
