export type MessageRole = "user" | "assistant";

export interface HealthStatus {
  status: "ok" | "degraded";
  bot: string;
  model: string;
  search_backend: string;
  docs_dir_exists: boolean;
  store_db: string;
}

export interface SourceCitation {
  type: "doc" | "block" | string;
  path?: string;
  start_line?: number;
  end_line?: number;
  id?: string;
  title?: string;
  source?: string;
  [key: string]: unknown;
}

export interface ToolActivityItem {
  tool: string;
  args?: Record<string, unknown>;
  summary?: string;
  status: "running" | "done";
}

export interface UiBlockPayload {
  id: string;
  plugin: string;
  slot?: "inline" | "inspector";
  title?: string;
  props: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  tools?: ToolActivityItem[];
  sources?: SourceCitation[];
  uiBlocks?: UiBlockPayload[];
  error?: string;
  streaming?: boolean;
}

export type SseEvent =
  | { type: "text_delta"; data: { delta: string } }
  | { type: "tool_call"; data: { tool: string; args: Record<string, unknown> } }
  | { type: "tool_result"; data: { tool: string; summary: string } }
  | { type: "sources"; data: { sources: SourceCitation[] } }
  | { type: "ui_block"; data: UiBlockPayload }
  | { type: "error"; data: { message: string } }
  | { type: "done"; data: Record<string, never> };
