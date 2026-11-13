<script lang="ts">
  import { Check, Palette } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";
  import { THEMES, themeStore, type ThemeId } from "$lib/state/theme.svelte";
  import { cn } from "$lib/utils";

  let open = $state(false);
  let containerEl: HTMLDivElement | undefined = $state();

  const activeTheme = $derived(THEMES.find((t) => t.id === themeStore.current) ?? THEMES[0]);

  function selectTheme(id: ThemeId): void {
    themeStore.setTheme(id);
    open = false;
  }

  function handleWindowClick(e: MouseEvent): void {
    if (!open || !containerEl) return;
    if (!containerEl.contains(e.target as Node)) {
      open = false;
    }
  }

  function handleWindowKeydown(e: KeyboardEvent): void {
    if (open && e.key === "Escape") {
      open = false;
    }
  }
</script>

<svelte:window onclick={handleWindowClick} onkeydown={handleWindowKeydown} />

<div bind:this={containerEl} class="relative">
  <Button
    variant="ghost"
    size="sm"
    type="button"
    aria-haspopup="listbox"
    aria-expanded={open}
    aria-label="Switch theme"
    title={`Theme: ${activeTheme.label}`}
    onclick={() => (open = !open)}
  >
    <Palette class="h-3.5 w-3.5" />
    <span class="hidden sm:inline">{activeTheme.label}</span>
  </Button>

  {#if open}
    <div
      role="listbox"
      aria-label="Available themes"
      class="absolute right-0 z-50 mt-1.5 w-60 rounded-lg border border-border bg-card p-1.5 text-card-foreground shadow-xs"
    >
      <div class="px-2 py-1 text-[11px] font-medium text-muted-foreground">
        Theme
      </div>
      <div class="space-y-0.5">
        {#each THEMES as theme (theme.id)}
          {@const selected = themeStore.current === theme.id}
          <button
            type="button"
            role="option"
            aria-selected={selected}
            onclick={() => selectTheme(theme.id)}
            class={cn(
              "flex w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-xs transition-colors cursor-pointer",
              selected
                ? "bg-accent text-accent-foreground"
                : "text-foreground hover:bg-accent/60",
            )}
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <span class="flex shrink-0 items-center -space-x-1">
                {#each theme.swatches as color, i (i)}
                  <span
                    class="h-3 w-3 rounded-full border border-border/80"
                    style="background-color: {color};"
                  ></span>
                {/each}
              </span>
              <span class="min-w-0">
                <span class="block font-medium leading-tight">{theme.label}</span>
                <span class="block truncate text-[10px] text-muted-foreground">
                  {theme.description}
                </span>
              </span>
            </div>
            {#if selected}
              <Check class="h-3.5 w-3.5 shrink-0 text-primary" />
            {/if}
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>
