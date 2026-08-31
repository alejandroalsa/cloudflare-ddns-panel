<script setup lang="ts">
import { cn } from "@/lib/utils";

interface Props {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success";
  class?: string;
}
const props = withDefaults(defineProps<Props>(), { variant: "default" });

const variants: Record<string, string> = {
  default: "border-transparent bg-primary text-primary-foreground",
  secondary: "border-transparent bg-secondary text-secondary-foreground",
  destructive: "border-transparent bg-destructive text-destructive-foreground",
  outline: "text-foreground border-border",
  success: "border-transparent bg-emerald-100 text-emerald-800",
};
</script>

<template>
  <span
    :class="
      cn(
        'inline-flex items-center gap-1.5 rounded-[5px] border px-3 py-1 text-sm font-semibold transition-colors',
        variants[props.variant],
        props.class
      )
    "
  >
    <slot />
  </span>
</template>
