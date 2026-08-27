<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from "vue";
import Chart from "chart.js/auto";
import "chartjs-adapter-date-fns";
import { api, type StatusOut, type PaginatedLogs } from "@/lib/api";
import AppLayout from "@/components/AppLayout.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import Badge from "@/components/ui/Badge.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import Label from "@/components/ui/Label.vue";
import { useAuthStore } from "@/stores/auth";
import { useConfirm } from "@/lib/confirm";
import {
  Wifi,
  Globe,
  ListChecks,
  Clock,
  RefreshCw,
  Trash2,
  XCircle,
  CheckCircle2,
  MinusCircle,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Filter,
  X,
} from "lucide-vue-next";

const auth = useAuthStore();
const { confirmDelete } = useConfirm();

const status = ref<StatusOut | null>(null);
const loading = ref(true);
const checking = ref(false);
const clearingLogs = ref(false);
const actionError = ref("");

// --- Gráfica de historial de IP ---
const chartCanvas = ref<HTMLCanvasElement | null>(null);
let chartInstance: Chart | null = null;

async function loadChart() {
  const { data } = await api.get("/status/ip-history", { params: { limit: 50 } });
  if (!chartCanvas.value) return;

  const ipOrder: string[] = [];
  const points = data
    .filter((log: any) => log.new_ip)
    .map((log: any) => {
      if (!ipOrder.includes(log.new_ip)) ipOrder.push(log.new_ip);
      return { x: log.timestamp, y: ipOrder.indexOf(log.new_ip), ip: log.new_ip };
    });

  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      datasets: [
        {
          label: "IP pública",
          data: points,
          stepped: true,
          borderColor: "#004BC3",
          backgroundColor: "#004BC3",
          pointRadius: 3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { type: "time", time: { unit: "day" } },
        y: {
          ticks: {
            callback: (value) => ipOrder[value as number] || "",
          },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx: any) => ctx.raw.ip,
          },
        },
      },
    },
  });
}

// --- Resumen ---
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
    await loadChart();
    await loadLogs();
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
    await loadChart();
    await loadLogs();
  } finally {
    clearingLogs.value = false;
  }
}

// --- Historial paginado con filtro de fechas ---
const logs = ref<PaginatedLogs | null>(null);
const page = ref(1);
const pageSize = 10;
const startDate = ref("");
const endDate = ref("");

async function loadLogs() {
  const params: Record<string, string | number> = { page: page.value, page_size: pageSize };
  if (startDate.value) params.start_date = startDate.value;
  if (endDate.value) params.end_date = endDate.value;
  const { data } = await api.get<PaginatedLogs>("/status/logs", { params });
  logs.value = data;
}

function applyFilter() {
  page.value = 1;
  loadLogs();
}

function clearFilter() {
  startDate.value = "";
  endDate.value = "";
  page.value = 1;
  loadLogs();
}

function nextPage() {
  if (!logs.value) return;
  const totalPages = Math.ceil(logs.value.total / logs.value.page_size);
  if (page.value < totalPages) {
    page.value++;
    loadLogs();
  }
}

function prevPage() {
  if (page.value > 1) {
    page.value--;
    loadLogs();
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

onMounted(async () => {
  await load();
  await nextTick();
  await loadChart();
  await loadLogs();
});
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
      <CardHeader>
        <CardTitle class="flex items-center gap-2"><TrendingUp class="h-4 w-4" /> Evolución de la IP</CardTitle>
        <CardDescription>Últimas 50 comprobaciones con IP registrada</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="h-64">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </CardContent>
    </Card>

    <Card class="mt-6">
      <CardHeader class="flex-col items-start gap-4 space-y-0 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle class="flex items-center gap-2"><Clock class="h-4 w-4" /> Historial de comprobaciones</CardTitle>
          <CardDescription>Filtra por rango de fechas o navega por páginas</CardDescription>
        </div>
        <Button
          v-if="auth.isAdmin && status?.total_records"
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
        <div class="mb-4 flex flex-wrap items-end gap-3">
          <div class="space-y-1.5">
            <Label class="text-xs">Desde</Label>
            <Input v-model="startDate" type="date" class="h-9" />
          </div>
          <div class="space-y-1.5">
            <Label class="text-xs">Hasta</Label>
            <Input v-model="endDate" type="date" class="h-9" />
          </div>
          <Button size="sm" variant="outline" @click="applyFilter">
            <Filter class="h-4 w-4" /> Filtrar
          </Button>
          <Button v-if="startDate || endDate" size="sm" variant="ghost" @click="clearFilter">
            <X class="h-4 w-4" /> Quitar filtro
          </Button>
        </div>

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
              <tr v-for="log in logs?.items" :key="log.id" class="border-b last:border-0">
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
              <tr v-if="!logs?.items?.length">
                <td colspan="6" class="py-6 text-center text-muted-foreground">
                  No hay comprobaciones para el rango seleccionado
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="logs && logs.total > pageSize" class="mt-4 flex items-center justify-between text-sm">
          <p class="text-muted-foreground">
            Página {{ logs.page }} de {{ Math.max(1, Math.ceil(logs.total / logs.page_size)) }}
            ({{ logs.total }} en total)
          </p>
          <div class="flex gap-2">
            <Button size="sm" variant="outline" :disabled="page <= 1" @click="prevPage">
              <ChevronLeft class="h-4 w-4" /> Anterior
            </Button>
            <Button
              size="sm"
              variant="outline"
              :disabled="page >= Math.ceil(logs.total / logs.page_size)"
              @click="nextPage"
            >
              Siguiente <ChevronRight class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  </AppLayout>
</template>
