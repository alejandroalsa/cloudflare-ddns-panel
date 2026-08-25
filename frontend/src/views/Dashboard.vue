<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type StatusOut } from "@/lib/api";
import AppLayout from "@/components/AppLayout.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import Badge from "@/components/ui/Badge.vue";
import Button from "@/components/ui/Button.vue";
import { useAuthStore } from "@/stores/auth";
import { useConfirm } from "@/lib/confirm";
import { Wifi, Globe, ListChecks, Clock, RefreshCw, Trash2, XCircle, CheckCircle2, MinusCircle } from "lucide-vue-next";

const auth = useAuthStore();
const { confirmDelete } = useConfirm();
const status = ref<StatusOut | null>(null);
const loading = ref(true);
const checking = ref(false);
const clearingLogs = ref(false);
const actionError = ref("");

async function load() {
  loading.value = true;
  const { data } = await api.get<StatusOut>("/status");
  status.value = data;
  loading.value = false;
}

async function checkNow() {
  checking.value = true;
  actionError.value = "";
  try {
    await api.post("/status/check");
    await load();
  } catch (e: any) {
    actionError.value = e?.response?.data?.detail || "No se pudo comprobar la IP";
  } finally {
    checking.value = false;
  }
}

async function clearHistory() {
  const ok = await confirmDelete(
    "Borrar historial",
    "Se eliminará todo el historial de comprobaciones. Esta acción no se puede deshacer."
  );
  if (!ok) return;
  clearingLogs.value = true;
  try {
    await api.delete("/status/logs");
    await load();
  } finally {
    clearingLogs.value = false;
  }
}

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function domainsList(json: string | null) {
  if (!json) return [];
  try {
    return JSON.parse(json) as string[];
  } catch {
    return [];
  }
}

const sourceLabels: Record<string, string> = {
  scheduler: "Automático",
  manual_global: "Manual (todo)",
  manual_zone: "Manual (dominio)",
  manual_record: "Manual (registro)",
};

onMounted(load);
</script>

<template>
  <AppLayout>
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Dashboard</h1>
        <p class="text-muted-foreground">Estado actual del servicio DDNS</p>
      </div>
      <Button v-if="auth.isAdmin" :disabled="checking" @click="checkNow">
        <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': checking }" />
        {{ checking ? "Comprobando..." : "Comprobar ahora" }}
      </Button>
    </div>

    <p v-if="actionError" class="mb-4 text-sm text-destructive">{{ actionError }}</p>

    <div v-if="status" class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Card>
        <CardHeader class="flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">IP pública actual</CardTitle>
          <Wifi class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ status.current_ip || "—" }}</div>
          <p class="text-xs text-muted-foreground">Última comprobación: {{ formatDate(status.last_check) }}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">Dominios gestionados</CardTitle>
          <Globe class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ status.total_zones }}</div>
          <p class="text-xs text-muted-foreground">Zonas configuradas</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">Registros DNS</CardTitle>
          <ListChecks class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ status.total_records }}</div>
          <p class="text-xs text-muted-foreground">Subdominios monitorizados</p>
        </CardContent>
      </Card>
    </div>

    <Card class="mt-6">
      <CardHeader class="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle class="flex items-center gap-2"><Clock class="h-4 w-4" /> Historial reciente</CardTitle>
          <CardDescription>Últimas comprobaciones de IP</CardDescription>
        </div>
        <Button
          v-if="auth.isAdmin && status?.recent_logs?.length"
          variant="ghost"
          size="sm"
          :disabled="clearingLogs"
          @click="clearHistory"
        >
          <Trash2 class="h-4 w-4 text-destructive" />
          {{ clearingLogs ? "Borrando..." : "Borrar historial" }}
        </Button>
      </CardHeader>
      <CardContent>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b text-left text-muted-foreground">
                <th class="py-2 pr-4 font-medium">Fecha</th>
                <th class="py-2 pr-4 font-medium">Origen</th>
                <th class="py-2 pr-4 font-medium">IP anterior</th>
                <th class="py-2 pr-4 font-medium">IP nueva</th>
                <th class="py-2 pr-4 font-medium">Estado</th>
                <th class="py-2 pr-4 font-medium">Dominios actualizados</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in status?.recent_logs" :key="log.id" class="border-b last:border-0">
                <td class="py-2 pr-4 whitespace-nowrap">{{ formatDate(log.timestamp) }}</td>
                <td class="py-2 pr-4 text-xs text-muted-foreground">{{ sourceLabels[log.source] || log.source }}</td>
                <td class="py-2 pr-4">{{ log.old_ip || "—" }}</td>
                <td class="py-2 pr-4">{{ log.new_ip || "—" }}</td>
                <td class="py-2 pr-4">
                  <Badge v-if="!log.success" variant="destructive" class="gap-1">
                    <XCircle class="h-3.5 w-3.5" /> Error
                  </Badge>
                  <Badge v-else-if="log.changed" variant="success" class="gap-1">
                    <CheckCircle2 class="h-3.5 w-3.5" /> Actualizado
                  </Badge>
                  <Badge v-else variant="secondary" class="gap-1">
                    <MinusCircle class="h-3.5 w-3.5" /> Sin cambios
                  </Badge>
                </td>
                <td class="py-2 pr-4 text-xs text-muted-foreground">
                  {{ domainsList(log.domains_updated).join(", ") || "—" }}
                </td>
              </tr>
              <tr v-if="!status?.recent_logs?.length">
                <td colspan="6" class="py-6 text-center text-muted-foreground">
                  Todavía no hay comprobaciones registradas
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </AppLayout>
</template>
