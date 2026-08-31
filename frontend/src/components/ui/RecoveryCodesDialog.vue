<script setup lang="ts">
import Dialog from "@/components/ui/Dialog.vue";
import Button from "@/components/ui/Button.vue";
import { AlertTriangle, Download, Check } from "lucide-vue-next";

const props = defineProps<{ open: boolean; codes: string[] }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

function downloadCodes() {
  const content =
    "Códigos de recuperación — Cloudflare DDNS Panel\n" +
    "Guárdalos en un lugar seguro. Cada código solo se puede usar una vez.\n\n" +
    props.codes.join("\n") +
    "\n";
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "codigos-recuperacion-ddns-panel.txt";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <div class="flex items-start gap-3">
      <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-[5px] bg-amber-100">
        <AlertTriangle class="h-5 w-5 text-amber-600" />
      </div>
      <div>
        <h2 class="text-lg font-semibold">Guarda tus códigos de recuperación</h2>
        <p class="mt-1 text-sm text-muted-foreground">
          Solo se muestran una vez. Si pierdes el acceso a tu app de autenticación, podrás usar
          uno de estos códigos (de un solo uso) para entrar en su lugar.
        </p>
      </div>
    </div>

    <div class="mt-4 grid grid-cols-2 gap-2 rounded-[5px] border bg-muted/40 p-4 font-mono text-sm">
      <span v-for="code in codes" :key="code">{{ code }}</span>
    </div>

    <div class="mt-6 flex justify-end gap-2">
      <Button variant="outline" @click="downloadCodes">
        <Download class="h-4 w-4" /> Descargar
      </Button>
      <Button @click="emit('update:open', false)">
        <Check class="h-4 w-4" /> Ya los he guardado
      </Button>
    </div>
  </Dialog>
</template>
