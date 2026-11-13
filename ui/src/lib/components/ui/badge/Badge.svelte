<script lang="ts">
  import type { Snippet } from "svelte";
  import type { HTMLAttributes } from "svelte/elements";
  import { cn } from "$lib/utils";

  type Variant = "default" | "secondary" | "outline" | "destructive";

  interface Props extends HTMLAttributes<HTMLSpanElement> {
    variant?: Variant;
    children?: Snippet;
  }

  let { variant = "secondary", class: className, children, ...rest }: Props = $props();

  const variantClasses: Record<Variant, string> = {
    default: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    outline: "border border-border text-foreground",
    destructive: "bg-destructive/15 text-destructive border border-destructive/30",
  };
</script>

<span
  class={cn(
    "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
    variantClasses[variant],
    className,
  )}
  {...rest}
>
  {@render children?.()}
</span>
