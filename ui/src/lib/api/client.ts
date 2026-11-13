import type { HealthStatus, MessageRole, SseEvent } from "./types";

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch("/health");
  if (!res.ok && res.status !== 503) {
    throw new Error(`Health check failed (${res.status})`);
  }
  return (await res.json()) as HealthStatus;
}

export interface ApiChatMessage {
  role: MessageRole;
  content: string;
}

/**
 * Stream typed SSE events from POST /api/chat.
 */
export async function streamChat(
  messages: ApiChatMessage[],
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal,
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const errBody = (await res.json()) as { detail?: string };
      if (errBody.detail) detail = errBody.detail;
    } catch {
      // ignore non-JSON error body
    }
    throw new Error(detail);
  }

  if (!res.body) {
    throw new Error("Response stream is empty.");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

    let sepIndex: number;
    while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawFrame = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);
      const parsed = parseSseFrame(rawFrame);
      if (parsed) {
        onEvent(parsed);
      }
    }
  }

  if (buffer.trim()) {
    const parsed = parseSseFrame(buffer);
    if (parsed) {
      onEvent(parsed);
    }
  }
}

function parseSseFrame(frame: string): SseEvent | null {
  let eventType = "message";
  const dataLines: string[] = [];

  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (dataLines.length === 0) return null;

  const rawData = dataLines.join("\n");
  try {
    const data = JSON.parse(rawData);
    return { type: eventType, data } as SseEvent;
  } catch {
    return null;
  }
}
