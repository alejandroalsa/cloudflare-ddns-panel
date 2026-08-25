<script setup lang="ts">
import { cn } from "@/lib/utils";

defineProps<{ class?: string; disabled?: boolean }>();
const model = defineModel<boolean>({ default: false });
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="model"
    :disabled="disabled"
    :class="
      cn(
        'inline-flex h-6 w-11 shrink-0 items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
        model ? 'bg-primary' : 'bg-input',
        $props.class
      )
    "
    @click="!disabled && (model = !model)"
  >
    <span
      :class="
        cn(
          'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition-transform',
          model ? 'translate-x-5' : 'translate-x-0'
        )
      "
    />
  </button>
</template>
