<script lang="ts">
  import { ChevronDown, ChevronRight, Loader2, Wrench } from "lucide-svelte";
  import type { ToolActivityItem } from "$lib/api/types";
  import { Badge } from "$lib/components/ui/badge";

  interface Props {
    tools: ToolActivityItem[];
  }

  let { tools }: Props = $props();
  let expanded = $state(false);

  const runningCount = $derived(tools.filter((t) => t.status === "running").length);
</script>

{#if tools.length > 0}
  <div class="mb-2 rounded-md border border-border bg-muted/40 text-xs">
    <button
      type="button"
      class="flex w-full items-center justify-between px-2.5 py-1.5 text-left text-muted-foreground hover:text-foreground cursor-pointer"
      onclick={() => (expanded = !expanded)}
    >
      <span class="flex items-center gap-1.5 font-medium">
        {#if runningCount > 0}
          <Loader2 class="h-3.5 w-3.5 animate-spin text-primary" />
          <span>Running {tools.at(-1)?.tool}...</span>
        {:else}
          <Wrench class="h-3.5 w-3.5" />
          <span>Used {tools.length} tool{tools.length === 1 ? "" : "s"}</span>
        {/if}
      </span>
      {#if expanded}
        <ChevronDown class="h-3.5 w-3.5" />
      {:else}
        <ChevronRight class="h-3.5 w-3.5" />
      {/if}
    </button>

    {#if expanded}
      <div class="space-y-1.5 border-t border-border px-2.5 py-2">
        {#each tools as item, idx (idx)}
          <div class="rounded bg-background/70 p-2 border border-border/60">
            <div class="flex items-center justify-between gap-2">
              <span class="font-mono font-medium text-foreground">{item.tool}</span>
              <Badge variant={item.status === "running" ? "default" : "secondary"}>
                {item.status}
              </Badge>
            </div>
            {#if item.args && Object.keys(item.args).length > 0}
              <pre class="mt-1 overflow-x-auto text-[11px] text-muted-foreground">{JSON.stringify(item.args)}</pre>
            {/if}
            {#if item.summary}
              <p class="mt-1 line-clamp-3 text-[11px] text-muted-foreground">{item.summary}</p>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
{/if}
