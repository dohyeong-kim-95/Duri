import { getApiBaseUrl, getWebSocketProbeUrl } from "@/lib/api";

const timelineItems = [
  { time: "09:12", kind: "Message", text: "Timeline shell ready" },
  { time: "09:14", kind: "System", text: "FastAPI healthcheck pending" },
  { time: "09:15", kind: "System", text: "WebSocket probe pending" },
];

export default function Home() {
  const apiBaseUrl = getApiBaseUrl();
  const websocketUrl = getWebSocketProbeUrl(apiBaseUrl);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Duri</p>
          <h1>Timeline</h1>
        </div>
        <div className="status-pill">MVP scaffold</div>
      </header>

      <section className="workspace" aria-label="Duri workspace">
        <aside className="side-panel" aria-label="Connection status">
          <div className="panel-heading">
            <span>Backend</span>
            <span className="dot" aria-hidden="true" />
          </div>
          <dl className="connection-list">
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

        <section className="timeline-panel" aria-label="Timeline preview">
          {timelineItems.map((item) => (
            <article className="timeline-item" key={`${item.time}-${item.kind}`}>
              <time>{item.time}</time>
              <div>
                <strong>{item.kind}</strong>
                <p>{item.text}</p>
              </div>
            </article>
          ))}
        </section>
      </section>
    </main>
  );
}
