<script setup lang="ts">
import { ref } from "vue";
import { cn } from "@/lib/utils";
import { Eye, EyeOff } from "lucide-vue-next";

defineProps<{ class?: string; placeholder?: string; autocomplete?: string; required?: boolean }>();
const model = defineModel<string | null>();

const visible = ref(false);
</script>

<template>
  <div class="relative">
    <input
      v-model="model"
      :type="visible ? 'text' : 'password'"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :required="required"
      :class="
        cn(
          'flex h-10 w-full rounded-[5px] border border-input bg-background px-3 py-2 pr-10 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
          $props.class
        )
      "
    />
    <button
      type="button"
      tabindex="-1"
      class="absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground hover:text-foreground"
      @click="visible = !visible"
    >
      <EyeOff v-if="visible" class="h-4 w-4" />
      <Eye v-else class="h-4 w-4" />
    </button>
  </div>
</template>
