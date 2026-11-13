<script lang="ts">
  import type { ChatMessage } from "$lib/api/types";
  import MessageBubble from "./MessageBubble.svelte";

  interface Props {
    messages: ChatMessage[];
    botName?: string;
  }

  let { messages, botName = "WebAgent" }: Props = $props();
  let containerEl: HTMLDivElement | undefined = $state();
  let pinnedToBottom = $state(true);

  function handleScroll(): void {
    if (!containerEl) return;
    const distanceFromBottom =
      containerEl.scrollHeight - containerEl.scrollTop - containerEl.clientHeight;
    pinnedToBottom = distanceFromBottom < 48;
  }

  $effect(() => {
    // Re-run whenever message count or latest message content changes
    const count = messages.length;
    const lastContentLen = messages.at(-1)?.content.length ?? 0;
    const lastToolsLen = messages.at(-1)?.tools?.length ?? 0;
    void (count + lastContentLen + lastToolsLen);

    if (pinnedToBottom && containerEl) {
      containerEl.scrollTop = containerEl.scrollHeight;
    }
  });
</script>

<div
  bind:this={containerEl}
  onscroll={handleScroll}
  class="flex-1 overflow-y-auto px-4 py-6"
>
  <div class="mx-auto flex max-w-3xl flex-col gap-4">
    {#if messages.length === 0}
      <div class="mt-16 text-center">
        <h2 class="text-lg font-semibold text-foreground">{botName}</h2>
        <p class="mt-1 text-sm text-muted-foreground">
          Ask a question to search the knowledge base and docs.
        </p>
      </div>
    {:else}
      {#each messages as msg (msg.id)}
        <MessageBubble message={msg} />
      {/each}
    {/if}
  </div>
</div>
