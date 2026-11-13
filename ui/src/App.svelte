<script lang="ts">
  import { onMount } from "svelte";
  import { Trash2 } from "lucide-svelte";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { ThemeSwitcher } from "$lib/components/ui/theme-switcher";
  import ChatContainer from "$lib/components/chat/ChatContainer.svelte";
  import PromptInput from "$lib/components/chat/PromptInput.svelte";
  import { chatStore } from "$lib/state/chat.svelte";

  onMount(() => {
    void chatStore.refreshHealth();
  });

  const botName = $derived(chatStore.health?.bot || "WebAgent");
</script>

<div class="flex h-dvh flex-col bg-background text-foreground">
  <header class="flex h-13 shrink-0 items-center justify-between border-b border-border px-4">
    <div class="flex items-center gap-2.5">
      <span class="text-sm font-semibold tracking-tight">{botName}</span>
      {#if chatStore.health}
        <Badge variant={chatStore.health.status === "ok" ? "secondary" : "destructive"}>
          {chatStore.health.status === "ok" ? "Ready" : "Degraded"}
        </Badge>
      {:else if chatStore.healthError}
        <Badge variant="destructive">Offline</Badge>
      {/if}
    </div>

    <div class="flex items-center gap-1.5">
      <ThemeSwitcher />
      {#if chatStore.messages.length > 0}
        <Button
          variant="ghost"
          size="sm"
          onclick={() => chatStore.clearMessages()}
          title="Clear conversation"
        >
          <Trash2 class="h-3.5 w-3.5" />
          <span>Clear</span>
        </Button>
      {/if}
    </div>
  </header>

  <ChatContainer messages={chatStore.messages} {botName} />

  <PromptInput
    isStreaming={chatStore.isStreaming}
    onSend={(text) => void chatStore.sendMessage(text)}
    onStop={() => chatStore.stopStreaming()}
  />
</div>
