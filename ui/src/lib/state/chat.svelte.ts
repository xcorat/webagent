import { fetchHealth, streamChat } from "$lib/api/client";
import type { ChatMessage, HealthStatus, SseEvent } from "$lib/api/types";

const STORAGE_KEY = "webagent.chat.v1";

function loadStoredMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((m) => ({ ...m, streaming: false }));
  } catch {
    return [];
  }
}

function saveMessages(messages: ChatMessage[]): void {
  try {
    const clean = messages.map(({ streaming: _s, ...rest }) => rest);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(clean));
  } catch {
    // ignore storage quota errors
  }
}

class ChatStore {
  messages = $state<ChatMessage[]>(loadStoredMessages());
  isStreaming = $state(false);
  health = $state<HealthStatus | null>(null);
  healthError = $state<string | null>(null);

  private abortController: AbortController | null = null;

  async refreshHealth(): Promise<void> {
    try {
      this.health = await fetchHealth();
      this.healthError = null;
    } catch (err) {
      this.healthError = err instanceof Error ? err.message : "Backend unreachable";
    }
  }

  clearMessages(): void {
    this.stopStreaming();
    this.messages = [];
    saveMessages([]);
  }

  stopStreaming(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.isStreaming = false;
    const last = this.messages.at(-1);
    if (last?.streaming) {
      last.streaming = false;
      saveMessages(this.messages);
    }
  }

  async sendMessage(text: string): Promise<void> {
    const trimmed = text.trim();
    if (!trimmed || this.isStreaming) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      tools: [],
      sources: [],
      uiBlocks: [],
      streaming: true,
    };

    // Build payload before pushing the empty assistant placeholder
    const historyPayload = [...this.messages, userMsg]
      .filter((m) => m.content.trim().length > 0)
      .map((m) => ({ role: m.role, content: m.content }));

    this.messages.push(userMsg, assistantMsg);
    const assistantIndex = this.messages.length - 1;
    this.isStreaming = true;
    this.abortController = new AbortController();
    saveMessages(this.messages);

    try {
      await streamChat(
        historyPayload,
        (event) => this.handleSseEvent(assistantIndex, event),
        this.abortController.signal,
      );
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        const msg = err instanceof Error ? err.message : "Streaming failed";
        this.messages[assistantIndex].error = msg;
      }
    } finally {
      this.messages[assistantIndex].streaming = false;
      this.isStreaming = false;
      this.abortController = null;
      saveMessages(this.messages);
    }
  }

  private handleSseEvent(index: number, event: SseEvent): void {
    const target = this.messages[index];
    if (!target) return;

    switch (event.type) {
      case "text_delta":
        target.content += event.data.delta;
        break;
      case "tool_call":
        target.tools = [
          ...(target.tools ?? []),
          { tool: event.data.tool, args: event.data.args, status: "running" },
        ];
        break;
      case "tool_result": {
        const tools = [...(target.tools ?? [])];
        const pendingIdx = tools.findLastIndex(
          (t) => t.tool === event.data.tool && t.status === "running",
        );
        if (pendingIdx !== -1) {
          tools[pendingIdx] = {
            ...tools[pendingIdx],
            summary: event.data.summary,
            status: "done",
          };
        } else {
          tools.push({
            tool: event.data.tool,
            summary: event.data.summary,
            status: "done",
          });
        }
        target.tools = tools;
        break;
      }
      case "sources":
        target.sources = event.data.sources;
        break;
      case "ui_block":
        target.uiBlocks = [...(target.uiBlocks ?? []), event.data];
        break;
      case "error":
        target.error = event.data.message;
        break;
      case "done":
        target.streaming = false;
        break;
    }
  }
}

export const chatStore = new ChatStore();
