<script lang="ts">
  import DOMPurify from "dompurify";
  import { marked } from "marked";
  import { AlertCircle } from "lucide-svelte";
  import type { ChatMessage } from "$lib/api/types";
  import ToolActivity from "./ToolActivity.svelte";
  import SourcesList from "./SourcesList.svelte";

  interface Props {
    message: ChatMessage;
  }

  let { message }: Props = $props();

  const renderedHtml = $derived.by(() => {
    if (!message.content) return "";
    const raw = marked.parse(message.content, { async: false, breaks: true }) as string;
    return DOMPurify.sanitize(raw);
  });
</script>

{#if message.role === "user"}
  <div class="flex justify-end">
    <div
      class="max-w-[82%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground shadow-xs whitespace-pre-wrap"
    >
      {message.content}
    </div>
  </div>
{:else}
  <div class="flex justify-start">
    <div class="w-full max-w-[92%] rounded-2xl rounded-bl-sm border border-border bg-card px-4 py-3 text-card-foreground shadow-xs">
      {#if message.tools && message.tools.length > 0}
        <ToolActivity tools={message.tools} />
      {/if}

      {#if message.content}
        <div class="prose-chat">
          {@html renderedHtml}
        </div>
      {:else if message.streaming}
        <div class="flex items-center gap-1.5 py-1 text-xs text-muted-foreground">
          <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-primary"></span>
          <span>Thinking...</span>
        </div>
      {/if}

      {#if message.error}
        <div class="mt-2 flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          <AlertCircle class="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>{message.error}</span>
        </div>
      {/if}

      {#if message.sources && message.sources.length > 0}
        <SourcesList sources={message.sources} />
      {/if}
    </div>
  </div>
{/if}
