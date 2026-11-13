<script lang="ts">
  import { BookOpen, ChevronDown, ChevronRight, FileText } from "lucide-svelte";
  import type { SourceCitation } from "$lib/api/types";

  interface Props {
    sources: SourceCitation[];
  }

  let { sources }: Props = $props();
  let expanded = $state(false);

  function formatLabel(s: SourceCitation): string {
    if (s.type === "doc" && s.path) {
      if (s.start_line && s.end_line) {
        return `${s.path} (L${s.start_line}–L${s.end_line})`;
      }
      if (s.start_line) {
        return `${s.path} (L${s.start_line})`;
      }
      return s.path;
    }
    return s.title || s.id || s.source || "Knowledge Block";
  }
</script>

{#if sources.length > 0}
  <div class="mt-2.5 rounded-md border border-border bg-muted/30 text-xs">
    <button
      type="button"
      class="flex w-full items-center justify-between px-2.5 py-1.5 text-left text-muted-foreground hover:text-foreground cursor-pointer"
      onclick={() => (expanded = !expanded)}
    >
      <span class="flex items-center gap-1.5 font-medium">
        <BookOpen class="h-3.5 w-3.5" />
        <span>Sources ({sources.length})</span>
      </span>
      {#if expanded}
        <ChevronDown class="h-3.5 w-3.5" />
      {:else}
        <ChevronRight class="h-3.5 w-3.5" />
      {/if}
    </button>

    {#if expanded}
      <ul class="space-y-1 border-t border-border px-2.5 py-2">
        {#each sources as src, idx (idx)}
          <li class="flex items-center gap-1.5 text-muted-foreground">
            <FileText class="h-3 w-3 shrink-0" />
            <span class="truncate font-mono text-[11px] text-foreground">{formatLabel(src)}</span>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
{/if}
