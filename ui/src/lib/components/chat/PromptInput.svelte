<script lang="ts">
  import { ArrowUp, Square } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";

  interface Props {
    isStreaming: boolean;
    onSend: (text: string) => void;
    onStop: () => void;
  }

  let { isStreaming, onSend, onStop }: Props = $props();
  let input = $state("");
  let textareaEl: HTMLTextAreaElement | undefined = $state();

  function adjustHeight(): void {
    if (!textareaEl) return;
    textareaEl.style.height = "auto";
    textareaEl.style.height = `${Math.min(textareaEl.scrollHeight, 180)}px`;
  }

  function submit(): void {
    if (!input.trim() || isStreaming) return;
    const text = input;
    input = "";
    if (textareaEl) {
      textareaEl.style.height = "auto";
    }
    onSend(text);
  }

  function handleKeydown(e: KeyboardEvent): void {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }
</script>

<div class="border-t border-border bg-background px-4 py-3">
  <form
    class="mx-auto flex max-w-3xl items-end gap-2 rounded-xl border border-input bg-card p-2 shadow-xs focus-within:ring-1 focus-within:ring-ring"
    onsubmit={(e) => {
      e.preventDefault();
      submit();
    }}
  >
    <textarea
      bind:this={textareaEl}
      bind:value={input}
      oninput={adjustHeight}
      onkeydown={handleKeydown}
      rows={1}
      placeholder="Ask something... (Enter to send, Shift+Enter for newline)"
      class="max-h-[180px] min-h-[38px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
    ></textarea>

    {#if isStreaming}
      <Button
        type="button"
        variant="destructive"
        size="icon"
        aria-label="Stop generation"
        onclick={onStop}
      >
        <Square class="h-4 w-4" />
      </Button>
    {:else}
      <Button
        type="submit"
        size="icon"
        disabled={!input.trim()}
        aria-label="Send message"
      >
        <ArrowUp class="h-4 w-4" />
      </Button>
    {/if}
  </form>
</div>
