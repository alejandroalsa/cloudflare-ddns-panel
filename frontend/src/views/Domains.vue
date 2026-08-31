<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { api, type Zone, type Record as DnsRecord, type ImportResult, type RecordType, type TestConnectionResult, type BulkRecordManualResult } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { useConfirm } from "@/lib/confirm";
import AppLayout from "@/components/AppLayout.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import PasswordInput from "@/components/ui/PasswordInput.vue";
import Label from "@/components/ui/Label.vue";
import Select from "@/components/ui/Select.vue";
import Badge from "@/components/ui/Badge.vue";
import Dialog from "@/components/ui/Dialog.vue";
import Switch from "@/components/ui/Switch.vue";
import {
  Plus,
  Trash2,
  X,
  Search,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Pencil,
  Cloud,
  CloudOff,
  CheckCircle2,
  Clock3,
  Save,
  Upload,
  Download,
  FileJson,
  FileDown,
  PlugZap,
  XCircle,
  Network,
  Layers,
} from "lucide-vue-next";

const auth = useAuthStore();
const { confirmDelete } = useConfirm();
const zones = ref<Zone[]>([]);
const loading = ref(true);
const error = ref("");

// --- Buscador ---
const search = ref("");
const filteredZones = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return zones.value;
  return zones.value
    .map((zone) => {
      const zoneMatches = zone.domain.toLowerCase().includes(q);
      const matchingRecords = zone.records.filter((r) => r.name.toLowerCase().includes(q));
      if (zoneMatches) return zone;
      if (matchingRecords.length) return { ...zone, records: matchingRecords };
      return null;
    })
    .filter((z): z is Zone => z !== null);
});

// --- Acordeón ---
const expanded = ref<Set<number>>(new Set());
function toggleExpanded(zoneId: number) {
  const next = new Set(expanded.value);
  if (next.has(zoneId)) next.delete(zoneId);
  else next.add(zoneId);
  expanded.value = next;
}

// --- Selección múltiple (grupo lógico) para edición en bloque ---
const selectedIds = ref<Set<number>>(new Set());
const allRecordsById = computed(() => {
  const map = new Map<number, DnsRecord>();
  for (const zone of zones.value) {
    for (const r of zone.records) map.set(r.id, r);
  }
  return map;
});
const selectedRecords = computed(() => Array.from(selectedIds.value).map((id) => allRecordsById.value.get(id)).filter(Boolean) as DnsRecord[]);
const selectedType = computed<RecordType | null>(() => selectedRecords.value[0]?.type || null);

function toggleSelect(record: DnsRecord) {
  const next = new Set(selectedIds.value);
  if (next.has(record.id)) {
    next.delete(record.id);
  } else {
    if (selectedType.value && record.type !== selectedType.value) return; // no mezclar tipos
    next.add(record.id);
  }
  selectedIds.value = next;
}

function clearSelection() {
  selectedIds.value = new Set();
}

// --- Diálogo nueva zona ---
const showZoneDialog = ref(false);
const newDomain = ref("");
const newZoneId = ref("");
const newApiToken = ref("");
const newRecordsRaw = ref("");
const savingZone = ref(false);

// --- Probar conexión ---
const testingConnection = ref(false);
const testResult = ref<TestConnectionResult | null>(null);

async function testConnection() {
  testingConnection.value = true;
  testResult.value = null;
  try {
    const { data } = await api.post<TestConnectionResult>("/zones/test-connection", {
      api_token: newApiToken.value,
      zone_id: newZoneId.value,
    });
    testResult.value = data;
  } catch (e: any) {
    testResult.value = { ok: false, zone_name: null, message: e?.response?.data?.detail || "Error al probar la conexión" };
  } finally {
    testingConnection.value = false;
  }
}

// --- Añadir registro a zona existente (diálogo) ---
const showAddRecordDialog = ref(false);
const addRecordZone = ref<Zone | null>(null);
const addName = ref("");
const addType = ref<RecordType>("A");
const addCreateInCf = ref(false);
const addIp = ref("");
const addProxied = ref(false);
const addTtlAuto = ref(true);
const addTtl = ref(3600);
const addSaving = ref(false);
const addError = ref("");

// --- Checks manuales en curso ---
const checkingZone = ref<{ [key: number]: boolean }>({});
const checkingRecord = ref<{ [key: number]: boolean }>({});

// --- Edición manual IP/proxy/TTL (individual y en bloque) ---
const showEditDialog = ref(false);
const isBulkEdit = ref(false);
const editingRecord = ref<DnsRecord | null>(null);
const editIp = ref("");
const editProxied = ref(false);
const editTtlAuto = ref(true);
const editTtl = ref(3600);
const savingEdit = ref(false);
const editError = ref("");

const showBulkResultDialog = ref(false);
const bulkResult = ref<BulkRecordManualResult | null>(null);

// --- Import / Export ---
const fileInput = ref<HTMLInputElement | null>(null);
const importing = ref(false);
const importResult = ref<ImportResult | null>(null);
const showImportResultDialog = ref(false);

async function load() {
  loading.value = true;
  try {
    const { data } = await api.get<Zone[]>("/zones");
    zones.value = data;
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "No se pudieron cargar los dominios";
  } finally {
    loading.value = false;
  }
}

function resetZoneForm() {
  newDomain.value = "";
  newZoneId.value = "";
  newApiToken.value = "";
  newRecordsRaw.value = "";
  testResult.value = null;
}

async function createZone() {
  savingZone.value = true;
  error.value = "";
  try {
    const recordsList = newRecordsRaw.value
      .split(/[\n,]/)
      .map((r) => r.trim())
      .filter(Boolean);
    await api.post("/zones", {
      domain: newDomain.value,
      zone_id: newZoneId.value,
      api_token: newApiToken.value,
      records: recordsList,
    });
    showZoneDialog.value = false;
    resetZoneForm();
    await load();
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "No se pudo crear el dominio";
  } finally {
    savingZone.value = false;
  }
}

async function deleteZone(zone: Zone) {
  const ok = await confirmDelete(
    `Eliminar ${zone.domain}`,
    `Se eliminará el dominio "${zone.domain}" y todos sus registros (${zone.records.length}). Esta acción no se puede deshacer.`
  );
  if (!ok) return;
  await api.delete(`/zones/${zone.id}`);
  await load();
}

function openAddRecordDialog(zone: Zone) {
  addRecordZone.value = zone;
  addName.value = "";
  addType.value = "A";
  addCreateInCf.value = false;
  addIp.value = "";
  addProxied.value = false;
  addTtlAuto.value = true;
  addTtl.value = 3600;
  addError.value = "";
  showAddRecordDialog.value = true;
}

async function submitAddRecord() {
  if (!addRecordZone.value) return;
  addSaving.value = true;
  addError.value = "";
  try {
    const payload: Record<string, unknown> = { name: addName.value, type: addType.value };
    if (addCreateInCf.value) {
      payload.ip = addIp.value;
      payload.proxied = addProxied.value;
      if (!addTtlAuto.value) payload.ttl = addTtl.value;
    }
    await api.post(`/zones/${addRecordZone.value.id}/records`, payload);
    showAddRecordDialog.value = false;
    await load();
  } catch (e: any) {
    addError.value = e?.response?.data?.detail || "No se pudo añadir el registro";
  } finally {
    addSaving.value = false;
  }
}

async function deleteRecord(record: DnsRecord) {
  const ok = await confirmDelete(
    `Eliminar registro ${record.name}`,
    "Este registro dejará de comprobarse y actualizarse automáticamente. Esta acción no se puede deshacer."
  );
  if (!ok) return;
  await api.delete(`/zones/records/${record.id}`);
  selectedIds.value.delete(record.id);
  await load();
}

async function checkZoneNow(zone: Zone) {
  checkingZone.value[zone.id] = true;
  error.value = "";
  try {
    await api.post(`/zones/${zone.id}/check`);
    await load();
  } catch (e: any) {
    error.value = e?.response?.data?.detail || `No se pudo comprobar ${zone.domain}`;
  } finally {
    checkingZone.value[zone.id] = false;
  }
}

async function checkRecordNow(record: DnsRecord) {
  checkingRecord.value[record.id] = true;
  error.value = "";
  try {
    await api.post(`/zones/records/${record.id}/check`);
    await load();
  } catch (e: any) {
    error.value = e?.response?.data?.detail || `No se pudo comprobar ${record.name}`;
  } finally {
    checkingRecord.value[record.id] = false;
  }
}

function openEditDialog(record: DnsRecord) {
  isBulkEdit.value = false;
  editingRecord.value = record;
  editIp.value = record.last_ip || "";
  editProxied.value = record.proxied ?? false;
  editTtlAuto.value = !record.ttl || record.ttl === 1;
  editTtl.value = record.ttl && record.ttl > 1 ? record.ttl : 3600;
  editError.value = "";
  showEditDialog.value = true;
}

function openBulkEditDialog() {
  isBulkEdit.value = true;
  editingRecord.value = null;
  editIp.value = "";
  editProxied.value = false;
  editTtlAuto.value = true;
  editTtl.value = 3600;
  editError.value = "";
  showEditDialog.value = true;
}

async function saveManualEdit() {
  savingEdit.value = true;
  editError.value = "";
  try {
    if (isBulkEdit.value) {
      const { data } = await api.post<BulkRecordManualResult>("/zones/records/bulk-manual", {
        record_ids: Array.from(selectedIds.value),
        ip: editIp.value,
        proxied: editProxied.value,
        ttl: editTtlAuto.value ? null : editTtl.value,
      });
      showEditDialog.value = false;
      bulkResult.value = data;
      showBulkResultDialog.value = true;
      clearSelection();
    } else if (editingRecord.value) {
      await api.put(`/zones/records/${editingRecord.value.id}/manual`, {
        ip: editIp.value,
        proxied: editProxied.value,
        ttl: editTtlAuto.value ? null : editTtl.value,
      });
      showEditDialog.value = false;
    }
    await load();
  } catch (e: any) {
    editError.value = e?.response?.data?.detail || "No se pudo actualizar el registro";
  } finally {
    savingEdit.value = false;
  }
}

function formatDate(value: string | null) {
  if (!value) return "sin actualizar";
  return new Date(value).toLocaleString();
}

function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function downloadTemplate() {
  const template = {
    domains: {
      "ejemplo.com": {
        api_token: "tu_token_de_api_de_cloudflare",
        zone_id: "tu_zone_id_de_cloudflare",
        records: ["ejemplo.com", "www.ejemplo.com", "*.ejemplo.com"],
      },
    },
  };
  downloadJson(template, "plantilla-dominios.json");
}

async function exportAll() {
  const { data } = await api.get("/zones/export");
  downloadJson(data, "dominios-export.json");
}

async function exportZone(zone: Zone) {
  const { data } = await api.get(`/zones/${zone.id}/export`);
  downloadJson(data, `${zone.domain}-export.json`);
}

function triggerImport() {
  fileInput.value?.click();
}

async function onImportFile(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  importing.value = true;
  error.value = "";
  try {
    const text = await file.text();
    const payload = JSON.parse(text);
    const { data } = await api.post<ImportResult>("/zones/import", payload);
    importResult.value = data;
    showImportResultDialog.value = true;
    await load();
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "El archivo no es un JSON válido o no se pudo importar";
  } finally {
    importing.value = false;
    target.value = "";
  }
}

onMounted(() => {
  load().then(() => {
    const initial = new Set<number>();
    for (const z of zones.value) {
      if (z.records.length <= 5) initial.add(z.id);
    }
    expanded.value = initial;
  });
});
</script>

<template>
  <AppLayout>
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Dominios</h1>
        <p class="text-muted-foreground">Zonas de Cloudflare y registros gestionados</p>
      </div>
      <div v-if="auth.isAdmin" class="flex flex-wrap items-center gap-2">
        <input ref="fileInput" type="file" accept="application/json" class="hidden" @change="onImportFile" />
        <Button variant="outline" size="sm" title="Descargar plantilla JSON" @click="downloadTemplate">
          <FileDown class="h-4 w-4" /> Plantilla
        </Button>
        <Button variant="outline" size="sm" :disabled="importing" @click="triggerImport">
          <Upload class="h-4 w-4" /> {{ importing ? "Importando..." : "Importar JSON" }}
        </Button>
        <Button variant="outline" size="sm" :disabled="!zones.length" @click="exportAll">
          <Download class="h-4 w-4" /> Exportar todo
        </Button>
        <Button @click="showZoneDialog = true">
          <Plus class="h-4 w-4" /> Nuevo dominio
        </Button>
      </div>
    </div>

    <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="relative max-w-sm flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input v-model="search" placeholder="Buscar dominio o registro..." class="pl-9" />
      </div>

      <div v-if="selectedIds.size > 0" class="flex items-center gap-2 rounded-[5px] border bg-accent px-3 py-2">
        <Layers class="h-4 w-4 shrink-0" />
        <span class="text-sm font-medium">{{ selectedIds.size }} seleccionado(s) ({{ selectedType }})</span>
        <Button size="sm" @click="openBulkEditDialog">
          <Pencil class="h-4 w-4" /> Editar seleccionados
        </Button>
        <Button size="sm" variant="ghost" @click="clearSelection">
          <X class="h-4 w-4" /> Cancelar
        </Button>
      </div>
    </div>

    <p v-if="error" class="mb-4 text-sm text-destructive">{{ error }}</p>

    <div v-if="loading" class="text-muted-foreground">Cargando…</div>

    <div v-else class="space-y-4">
      <Card v-for="zone in filteredZones" :key="zone.id">
        <CardHeader class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <button
            class="flex flex-1 items-center gap-2 text-left min-w-0"
            @click="toggleExpanded(zone.id)"
          >
            <ChevronDown v-if="expanded.has(zone.id)" class="h-4 w-4 shrink-0 text-muted-foreground" />
            <ChevronRight v-else class="h-4 w-4 shrink-0 text-muted-foreground" />
            <div class="min-w-0">
              <CardTitle class="truncate">{{ zone.domain }}</CardTitle>
              <CardDescription class="break-words">
                Zone ID: {{ zone.zone_id }} · Token: {{ zone.api_token_preview }} ·
                {{ zone.records.length }} registro(s)
              </CardDescription>
            </div>
          </button>
          <div class="flex flex-wrap items-center gap-1 sm:shrink-0">
            <Button
              v-if="auth.isAdmin"
              variant="ghost"
              size="icon"
              title="Comprobar este dominio ahora"
              :disabled="checkingZone[zone.id]"
              @click="checkZoneNow(zone)"
            >
              <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': checkingZone[zone.id] }" />
            </Button>
            <Button
              v-if="auth.isAdmin"
              variant="ghost"
              size="icon"
              title="Exportar este dominio a JSON"
              @click="exportZone(zone)"
            >
              <FileJson class="h-4 w-4" />
            </Button>
            <Button v-if="auth.isAdmin" variant="ghost" size="icon" title="Eliminar dominio" @click="deleteZone(zone)">
              <Trash2 class="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </CardHeader>

        <CardContent v-if="expanded.has(zone.id)">
          <div class="space-y-2">
            <div
              v-for="record in zone.records"
              :key="record.id"
              class="flex flex-col gap-2 rounded-[5px] border px-3 py-2 sm:flex-row sm:items-center sm:justify-between"
              :class="{ 'border-primary bg-accent/50': selectedIds.has(record.id) }"
            >
              <div class="flex min-w-0 items-start gap-2">
                <input
                  v-if="auth.isAdmin"
                  type="checkbox"
                  class="mt-1 h-4 w-4 shrink-0 rounded-[3px]"
                  :checked="selectedIds.has(record.id)"
                  :disabled="!!selectedType && selectedType !== record.type && !selectedIds.has(record.id)"
                  @change="toggleSelect(record)"
                />
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <Badge variant="outline" class="gap-1">
                      <Network class="h-3.5 w-3.5" /> {{ record.type }}
                    </Badge>
                    <p class="text-sm font-medium break-words">{{ record.name }}</p>
                  </div>
                  <p class="text-xs text-muted-foreground">
                    Última IP: {{ record.last_ip || "—" }} · TTL: {{ record.ttl && record.ttl > 1 ? record.ttl + "s" : "auto" }} ·
                    {{ formatDate(record.last_updated) }}
                  </p>
                </div>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <Badge v-if="record.proxied" variant="secondary" class="gap-1">
                  <Cloud class="h-3.5 w-3.5" /> Proxied
                </Badge>
                <Badge v-else-if="record.proxied === false" variant="outline" class="gap-1">
                  <CloudOff class="h-3.5 w-3.5" /> DNS only
                </Badge>
                <Badge v-if="record.last_ip" variant="success" class="gap-1">
                  <CheckCircle2 class="h-3.5 w-3.5" /> OK
                </Badge>
                <Badge v-else variant="secondary" class="gap-1">
                  <Clock3 class="h-3.5 w-3.5" /> Pendiente
                </Badge>

                <Button
                  v-if="auth.isAdmin"
                  variant="ghost"
                  size="icon"
                  title="Comprobar este registro ahora"
                  :disabled="checkingRecord[record.id]"
                  @click="checkRecordNow(record)"
                >
                  <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': checkingRecord[record.id] }" />
                </Button>
                <Button
                  v-if="auth.isAdmin"
                  variant="ghost"
                  size="icon"
                  title="Editar IP / proxy / TTL manualmente"
                  @click="openEditDialog(record)"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
                <Button
                  v-if="auth.isAdmin"
                  variant="ghost"
                  size="icon"
                  title="Eliminar registro"
                  @click="deleteRecord(record)"
                >
                  <X class="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </div>
            <p v-if="!zone.records.length" class="text-sm text-muted-foreground">
              Sin registros configurados todavía.
            </p>
          </div>

          <div v-if="auth.isAdmin" class="mt-4">
            <Button variant="outline" class="w-full sm:w-auto" @click="openAddRecordDialog(zone)">
              <Plus class="h-4 w-4" /> Añadir registro
            </Button>
          </div>
        </CardContent>
      </Card>

      <p v-if="!filteredZones.length && search" class="text-muted-foreground">
        Ningún dominio o registro coincide con "{{ search }}".
      </p>
      <p v-else-if="!zones.length" class="text-muted-foreground">
        Todavía no hay dominios configurados. Crea el primero con "Nuevo dominio" o importa un JSON.
      </p>
    </div>

    <!-- Diálogo: nuevo dominio -->
    <Dialog v-model:open="showZoneDialog">
      <h2 class="mb-1 text-lg font-semibold">Nuevo dominio</h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Introduce los datos de la zona de Cloudflare. Puedes obtener el token y el Zone ID desde
        el dashboard de Cloudflare.
      </p>
      <form class="space-y-4" @submit.prevent="createZone">
        <div class="space-y-1.5">
          <Label>Dominio</Label>
          <Input v-model="newDomain" placeholder="ejemplo.com" required />
        </div>
        <div class="space-y-1.5">
          <Label>Zone ID</Label>
          <Input v-model="newZoneId" required />
        </div>
        <div class="space-y-1.5">
          <Label>API Token</Label>
          <PasswordInput v-model="newApiToken" required />
        </div>

        <div class="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            :disabled="testingConnection || !newApiToken || !newZoneId"
            @click="testConnection"
          >
            <PlugZap class="h-4 w-4" /> {{ testingConnection ? "Probando..." : "Probar conexión" }}
          </Button>
          <Badge v-if="testResult?.ok" variant="success" class="gap-1">
            <CheckCircle2 class="h-3.5 w-3.5" /> Conectado a "{{ testResult.zone_name }}"
          </Badge>
          <Badge v-else-if="testResult && !testResult.ok" variant="destructive" class="gap-1">
            <XCircle class="h-3.5 w-3.5" /> {{ testResult.message }}
          </Badge>
        </div>

        <div class="space-y-1.5">
          <Label>Registros a mantener actualizados</Label>
          <textarea
            v-model="newRecordsRaw"
            rows="3"
            class="flex w-full rounded-[5px] border border-input bg-background px-3 py-2 text-sm"
            placeholder="ejemplo.com, www.ejemplo.com, *.ejemplo.com"
          />
          <p class="text-xs text-muted-foreground">
            Sepáralos por comas o saltos de línea. Se crean como registros A; para AAAA añádelos
            luego desde el dominio ya creado.
          </p>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" @click="showZoneDialog = false">
            <X class="h-4 w-4" /> Cancelar
          </Button>
          <Button type="submit" :disabled="savingZone">
            <Save class="h-4 w-4" /> {{ savingZone ? "Guardando..." : "Guardar" }}
          </Button>
        </div>
      </form>
    </Dialog>

    <!-- Diálogo: añadir registro (con opción de crearlo directamente en Cloudflare) -->
    <Dialog v-model:open="showAddRecordDialog">
      <h2 class="mb-1 text-lg font-semibold">Añadir registro</h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Dominio: <strong>{{ addRecordZone?.domain }}</strong>
      </p>
      <form class="space-y-4" @submit.prevent="submitAddRecord">
        <div class="space-y-1.5">
          <Label>Nombre</Label>
          <Input v-model="addName" placeholder="ej: www.ejemplo.com o *.ejemplo.com" required />
        </div>
        <div class="space-y-1.5">
          <Label>Tipo</Label>
          <Select v-model="addType">
            <option value="A">A (IPv4)</option>
            <option value="AAAA">AAAA (IPv6)</option>
          </Select>
        </div>

        <div class="rounded-[5px] border px-3 py-2">
          <div class="flex items-center justify-between gap-3">
            <div class="min-w-0">
              <p class="text-sm font-medium">Crear el registro en Cloudflare</p>
              <p class="text-xs text-muted-foreground">
                {{
                  addCreateInCf
                    ? "Se creará como registro nuevo en Cloudflare con la IP que indiques."
                    : "El registro ya existe en Cloudflare — el panel solo empezará a vigilarlo."
                }}
              </p>
            </div>
            <Switch v-model="addCreateInCf" class="shrink-0" />
          </div>

          <div v-if="addCreateInCf" class="mt-3 space-y-3 border-t pt-3">
            <div class="space-y-1.5">
              <Label>{{ addType === "AAAA" ? "Dirección IPv6" : "Dirección IP" }}</Label>
              <Input v-model="addIp" :placeholder="addType === 'AAAA' ? '2001:db8::1' : '203.0.113.10'" required />
            </div>
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-medium">Proxy de Cloudflare (nube naranja)</p>
              <Switch v-model="addProxied" class="shrink-0" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-medium">TTL automático</p>
              <Switch v-model="addTtlAuto" class="shrink-0" />
            </div>
            <div v-if="!addTtlAuto" class="space-y-1.5">
              <Label class="text-xs">TTL (segundos)</Label>
              <Input v-model.number="addTtl" type="number" min="30" />
            </div>
          </div>
        </div>

        <p v-if="addError" class="text-sm text-destructive">{{ addError }}</p>
        <div class="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" @click="showAddRecordDialog = false">
            <X class="h-4 w-4" /> Cancelar
          </Button>
          <Button type="submit" :disabled="addSaving">
            <Save class="h-4 w-4" /> {{ addSaving ? "Guardando..." : "Guardar" }}
          </Button>
        </div>
      </form>
    </Dialog>

    <!-- Diálogo: editar IP / proxy / TTL manualmente (individual o en bloque) -->
    <Dialog v-model:open="showEditDialog">
      <h2 class="mb-1 text-lg font-semibold">
        {{ isBulkEdit ? `Editar ${selectedIds.size} registros seleccionados` : "Editar registro manualmente" }}
      </h2>
      <p class="mb-4 text-sm text-muted-foreground">
        <template v-if="isBulkEdit">
          Se aplicará la misma IP{{ selectedType === "AAAA" ? "v6" : "" }}, proxy y TTL a todos los
          registros seleccionados ({{ selectedType }}).
        </template>
        <template v-else>
          {{ editingRecord?.name }} ({{ editingRecord?.type }}) — esto actualiza el registro
          directamente en Cloudflare, sin esperar a la comprobación automática.
        </template>
      </p>
      <form class="space-y-4" @submit.prevent="saveManualEdit">
        <div class="space-y-1.5">
          <Label>{{ (isBulkEdit ? selectedType : editingRecord?.type) === "AAAA" ? "Dirección IPv6" : "Dirección IP" }}</Label>
          <Input
            v-model="editIp"
            :placeholder="(isBulkEdit ? selectedType : editingRecord?.type) === 'AAAA' ? '2001:db8::1' : '203.0.113.10'"
            required
          />
        </div>
        <div class="flex items-center justify-between gap-3 rounded-[5px] border px-3 py-2">
          <div class="min-w-0">
            <p class="text-sm font-medium">Proxy de Cloudflare (nube naranja)</p>
            <p class="text-xs text-muted-foreground">
              Activado = tráfico a través de Cloudflare. Desactivado = DNS only.
            </p>
          </div>
          <Switch v-model="editProxied" class="shrink-0" />
        </div>
        <div class="rounded-[5px] border px-3 py-2">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-medium">TTL automático</p>
            <Switch v-model="editTtlAuto" class="shrink-0" />
          </div>
          <div v-if="!editTtlAuto" class="mt-3 space-y-1.5">
            <Label class="text-xs">TTL (segundos)</Label>
            <Input v-model.number="editTtl" type="number" min="30" />
          </div>
        </div>
        <p v-if="editError" class="text-sm text-destructive">{{ editError }}</p>
        <div class="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" @click="showEditDialog = false">
            <X class="h-4 w-4" /> Cancelar
          </Button>
          <Button type="submit" :disabled="savingEdit">
            <Save class="h-4 w-4" /> {{ savingEdit ? "Guardando..." : "Guardar" }}
          </Button>
        </div>
      </form>
    </Dialog>

    <!-- Diálogo: resultado de edición en bloque -->
    <Dialog v-model:open="showBulkResultDialog">
      <h2 class="mb-4 text-lg font-semibold">Edición en bloque completada</h2>
      <div v-if="bulkResult" class="space-y-3 text-sm">
        <div v-if="bulkResult.updated.length">
          <p class="font-medium text-emerald-600">Actualizados ({{ bulkResult.updated.length }})</p>
          <p class="text-muted-foreground">{{ bulkResult.updated.join(", ") }}</p>
        </div>
        <div v-if="bulkResult.failed.length">
          <p class="font-medium text-destructive">Con errores ({{ bulkResult.failed.length }})</p>
          <p class="text-muted-foreground">{{ bulkResult.failed.join(" · ") }}</p>
        </div>
      </div>
      <div class="mt-6 flex justify-end">
        <Button @click="showBulkResultDialog = false">
          <CheckCircle2 class="h-4 w-4" /> Entendido
        </Button>
      </div>
    </Dialog>

    <!-- Diálogo: resultado de importación -->
    <Dialog v-model:open="showImportResultDialog">
      <h2 class="mb-4 text-lg font-semibold">Importación completada</h2>
      <div v-if="importResult" class="space-y-3 text-sm">
        <div v-if="importResult.created.length">
          <p class="font-medium text-emerald-600">Creados ({{ importResult.created.length }})</p>
          <p class="text-muted-foreground">{{ importResult.created.join(", ") }}</p>
        </div>
        <div v-if="importResult.updated.length">
          <p class="font-medium text-blue-600">Actualizados ({{ importResult.updated.length }})</p>
          <p class="text-muted-foreground">{{ importResult.updated.join(", ") }}</p>
        </div>
        <div v-if="importResult.skipped.length">
          <p class="font-medium text-muted-foreground">Omitidos ({{ importResult.skipped.length }})</p>
          <p class="text-muted-foreground">{{ importResult.skipped.join(", ") }}</p>
        </div>
      </div>
      <div class="mt-6 flex justify-end">
        <Button @click="showImportResultDialog = false">
          <CheckCircle2 class="h-4 w-4" /> Entendido
        </Button>
      </div>
    </Dialog>
  </AppLayout>
</template>
