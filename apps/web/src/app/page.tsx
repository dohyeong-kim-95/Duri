import { getApiBaseUrl, getWebSocketProbeUrl } from "@/lib/api";

import { TimelineWorkspace } from "./timeline-workspace";

export default function Home() {
  const apiBaseUrl = getApiBaseUrl();

  return (
    <TimelineWorkspace
      apiBaseUrl={apiBaseUrl}
      websocketUrl={getWebSocketProbeUrl(apiBaseUrl)}
    />
  );
}
