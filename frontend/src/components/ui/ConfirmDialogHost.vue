<script setup lang="ts">
import { useConfirmStore } from "@/stores/confirm";
import Dialog from "@/components/ui/Dialog.vue";
import Button from "@/components/ui/Button.vue";
import { AlertTriangle, X, Trash2 } from "lucide-vue-next";

const store = useConfirmStore();
</script>

<template>
  <Dialog :open="store.open" @update:open="(v) => !v && store.resolve(false)">
    <div class="flex items-start gap-3">
      <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-[5px] bg-destructive/10">
        <AlertTriangle class="h-5 w-5 text-destructive" />
      </div>
      <div>
        <h2 class="text-lg font-semibold">{{ store.title }}</h2>
        <p class="mt-1 text-sm text-muted-foreground">{{ store.description }}</p>
      </div>
    </div>
    <div class="mt-6 flex justify-end gap-2">
      <Button variant="outline" @click="store.resolve(false)">
        <X class="h-4 w-4" /> Cancelar
      </Button>
      <Button variant="destructive" @click="store.resolve(true)">
        <Trash2 class="h-4 w-4" /> {{ store.confirmLabel }}
      </Button>
    </div>
  </Dialog>
</template>
