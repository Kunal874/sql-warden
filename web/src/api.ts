export type Payload = Record<string, unknown> & { status?: string; step?: string; reason?: string };
export type RunEvent = { id: number; type: string; payload: Payload };
export type Reply = { ok: boolean; status: number; body: Payload };

export async function request(
  path: string,
  init: { method?: string; body?: unknown; token?: string } = {},
): Promise<Reply> {
  const headers: Record<string, string> = {};
  if (init.body !== undefined) headers["Content-Type"] = "application/json";
  if (init.token) headers.Authorization = `Bearer ${init.token}`;
  try {
    const response = await fetch(path, {
      method: init.method ?? "GET",
      headers,
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
    });
    const body = (await response.json().catch(() => ({}))) as Payload;
    return { ok: response.ok, status: response.status, body };
  } catch {
    return { ok: false, status: 0, body: { reason: "network_error" } };
  }
}

/** Read the run's SSE stream with fetch so the capability stays in a header. */
export async function streamEvents(
  runId: string,
  token: string,
  lastId: number,
  onEvent: (event: RunEvent) => void,
  signal: AbortSignal,
): Promise<{ lastId: number; status: number }> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/events`, {
    headers: { Authorization: `Bearer ${token}`, "Last-Event-ID": String(lastId) },
    signal,
  });
  if (!response.ok || !response.body) return { lastId, status: response.status };
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const event = parseFrame(frame);
      if (event) {
        lastId = event.id;
        onEvent(event);
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
  return { lastId, status: response.status };
}

function parseFrame(frame: string): RunEvent | null {
  let id = 0;
  let type = "message";
  let data = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith(":")) continue;
    if (line.startsWith("id: ")) id = Number(line.slice(4));
    else if (line.startsWith("event: ")) type = line.slice(7);
    else if (line.startsWith("data: ")) data += line.slice(6);
  }
  if (!id || !data) return null;
  try {
    return { id, type, payload: JSON.parse(data) as Payload };
  } catch {
    return null;
  }
}
