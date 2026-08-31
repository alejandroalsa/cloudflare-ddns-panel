<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type PaginatedAudit } from "@/lib/api";
import AppLayout from "@/components/AppLayout.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import Label from "@/components/ui/Label.vue";
import Badge from "@/components/ui/Badge.vue";
import {
  ScrollText,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  User,
  Settings,
  FileJson,
  FileSpreadsheet,
} from "lucide-vue-next";

const audit = ref<PaginatedAudit | null>(null);
const page = ref(1);
const pageSize = 20;
const startDate = ref("");
const endDate = ref("");
const expandedIds = ref<Set<number>>(new Set());

function toggleDetails(id: number) {
  const next = new Set(expandedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  expandedIds.value = next;
}

async function load() {
  const params: Record<string, string | number> = { page: page.value, page_size: pageSize };
  if (startDate.value) params.start_date = startDate.value;
  if (endDate.value) params.end_date = endDate.value;
  const { data } = await api.get<PaginatedAudit>("/audit", { params });
  audit.value = data;
}

function applyFilter() {
  page.value = 1;
  load();
}

function clearFilter() {
  startDate.value = "";
  endDate.value = "";
  page.value = 1;
  load();
}

function nextPage() {
  if (!audit.value) return;
  const totalPages = Math.ceil(audit.value.total / audit.value.page_size);
  if (page.value < totalPages) {
    page.value++;
    load();
  }
}

function prevPage() {
  if (page.value > 1) {
    page.value--;
    load();
  }
}

async function exportLogs(format: "csv" | "json") {
  const params: Record<string, string> = { format };
  if (startDate.value) params.start_date = startDate.value;
  if (endDate.value) params.end_date = endDate.value;
  const response = await api.get("/audit/export", { params, responseType: "blob" });
  const blob = new Blob([response.data], { type: format === "csv" ? "text/csv" : "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `auditoria.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function safeParse(json: string | null): Record<string, any> | null {
  if (!json) return null;
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}

/** Construye una lista de {key, before, after, changed} comparando dos objetos (o snapshots anidados). */
function buildDiff(beforeJson: string | null, afterJson: string | null) {
  const before = safeParse(beforeJson);
  const after = safeParse(afterJson);
  if (!before && !after) return [];

  const keys = new Set([...(before ? Object.keys(before) : []), ...(after ? Object.keys(after) : [])]);
  return Array.from(keys).map((key) => {
    const b = before ? before[key] : undefined;
    const a = after ? after[key] : undefined;
    const format = (v: any) => (v === undefined ? "—" : typeof v === "object" && v !== null ? JSON.stringify(v) : String(v));
    return {
      key,
      before: format(b),
      after: format(a),
      changed: JSON.stringify(b) !== JSON.stringify(a),
    };
  });
}

const actionVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  login: "secondary",
  zone_delete: "destructive",
  record_delete: "destructive",
  user_delete: "destructive",
  logs_cleared: "destructive",
  admin_disable_2fa: "destructive",
};

function badgeVariant(action: string) {
  return actionVariant[action] || "outline";
}

const actionLabels: Record<string, string> = {
  login: "Inicio de sesión",
  recovery_code_used: "Login con código de recuperación",
  zone_create: "Dominio creado",
  zone_update: "Dominio editado",
  zone_delete: "Dominio eliminado",
  record_create: "Registro creado",
  record_delete: "Registro eliminado",
  record_manual_edit: "Registro editado manualmente",
  record_bulk_manual_edit: "Edición en bloque de registros",
  manual_check_zone: "Comprobación manual (dominio)",
  manual_check_record: "Comprobación manual (registro)",
  manual_check_global: "Comprobación manual (todo)",
  user_create: "Usuario creado",
  user_update: "Usuario editado",
  user_delete: "Usuario eliminado",
  user_self_update: "Perfil propio editado",
  settings_update: "Ajustes actualizados",
  test_email: "Email de prueba enviado",
  logs_cleared: "Historial borrado",
  zones_import: "Importación de dominios",
  "2fa_enabled": "2FA activado",
  "2fa_disabled": "2FA desactivado (propio)",
  admin_disable_2fa: "2FA desactivado por admin",
  recovery_codes_regenerated: "Códigos de recuperación regenerados",
};

onMounted(load);
</script>

<template>
  <AppLayout>
    <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Auditoría</h1>
        <p class="text-muted-foreground">Registro de acciones administrativas realizadas en el panel</p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" size="sm" @click="exportLogs('csv')">
          <FileSpreadsheet class="h-4 w-4" /> Exportar CSV
        </Button>
        <Button variant="outline" size="sm" @click="exportLogs('json')">
          <FileJson class="h-4 w-4" /> Exportar JSON
        </Button>
      </div>
    </div>

    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2"><ScrollText class="h-4 w-4" /> Historial de acciones</CardTitle>
        <CardDescription>Quién hizo qué y cuándo — despliega una entrada para ver el antes y el después</CardDescription>
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

        <div class="space-y-2">
          <div v-for="entry in audit?.items" :key="entry.id" class="rounded-[5px] border">
            <button
              class="flex w-full flex-col gap-2 px-3 py-2 text-left sm:flex-row sm:items-center sm:justify-between"
              @click="toggleDetails(entry.id)"
            >
              <div class="flex min-w-0 items-center gap-3">
                <ChevronDown
                  class="h-4 w-4 shrink-0 text-muted-foreground transition-transform"
                  :class="{ '-rotate-90': !expandedIds.has(entry.id) }"
                />
                <Badge :variant="badgeVariant(entry.action)" class="shrink-0 gap-1.5">
                  <Settings class="h-3.5 w-3.5" />
                  {{ actionLabels[entry.action] || entry.action }}
                </Badge>
                <p class="truncate text-sm text-muted-foreground">{{ entry.details }}</p>
              </div>
              <div class="flex shrink-0 items-center gap-3 text-xs text-muted-foreground">
                <span class="flex items-center gap-1"><User class="h-3.5 w-3.5" /> {{ entry.username || "—" }}</span>
                <span>{{ formatDate(entry.timestamp) }}</span>
              </div>
            </button>

            <div v-if="expandedIds.has(entry.id)" class="border-t px-3 py-3">
              <div v-if="buildDiff(entry.before_json, entry.after_json).length" class="overflow-x-auto">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="text-left text-muted-foreground">
                      <th class="pb-1 pr-4 font-medium">Campo</th>
                      <th class="pb-1 pr-4 font-medium">Antes</th>
                      <th class="pb-1 font-medium">Después</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="field in buildDiff(entry.before_json, entry.after_json)"
                      :key="field.key"
                      class="border-t"
                      :class="{ 'bg-amber-50': field.changed }"
                    >
                      <td class="py-1.5 pr-4 font-medium">{{ field.key }}</td>
                      <td class="py-1.5 pr-4 text-muted-foreground">{{ field.before }}</td>
                      <td class="py-1.5" :class="field.changed ? 'font-medium text-foreground' : 'text-muted-foreground'">
                        {{ field.after }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="text-xs text-muted-foreground">
                Esta acción no registró un antes/después detallado.
              </p>
            </div>
          </div>
          <p v-if="!audit?.items?.length" class="py-6 text-center text-muted-foreground">
            No hay acciones registradas para el rango seleccionado.
          </p>
        </div>

        <div v-if="audit && audit.total > pageSize" class="mt-4 flex items-center justify-between text-sm">
          <p class="text-muted-foreground">
            Página {{ audit.page }} de {{ Math.max(1, Math.ceil(audit.total / audit.page_size)) }}
            ({{ audit.total }} en total)
          </p>
          <div class="flex gap-2">
            <Button size="sm" variant="outline" :disabled="page <= 1" @click="prevPage">
              <ChevronLeft class="h-4 w-4" /> Anterior
            </Button>
            <Button
              size="sm"
              variant="outline"
              :disabled="page >= Math.ceil(audit.total / audit.page_size)"
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
