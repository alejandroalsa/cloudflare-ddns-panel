<script setup lang="ts">
import { useTheme } from "@/lib/theme";
import { Sun, Moon, Monitor } from "lucide-vue-next";

const { mode, setTheme } = useTheme();
</script>

<template>
  <div class="flex items-center rounded-[5px] border p-0.5">
    <button
      type="button"
      title="Tema claro"
      class="flex h-7 w-7 items-center justify-center rounded-[5px] transition-colors"
      :class="mode === 'light' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent'"
      @click="setTheme('light')"
    >
      <Sun class="h-4 w-4" />
    </button>
    <button
      type="button"
      title="Tema oscuro"
      class="flex h-7 w-7 items-center justify-center rounded-[5px] transition-colors"
      :class="mode === 'dark' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent'"
      @click="setTheme('dark')"
    >
      <Moon class="h-4 w-4" />
    </button>
    <button
      type="button"
      title="Usar el tema del sistema"
      class="flex h-7 w-7 items-center justify-center rounded-[5px] transition-colors"
      :class="mode === 'system' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent'"
      @click="setTheme('system')"
    >
      <Monitor class="h-4 w-4" />
    </button>
  </div>
</template>
