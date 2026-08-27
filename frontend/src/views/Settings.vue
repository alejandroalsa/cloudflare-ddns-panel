<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type SettingsPayload, type TestEmailResult } from "@/lib/api";
import AppLayout from "@/components/AppLayout.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import Button from "@/components/ui/Button.vue";
import Badge from "@/components/ui/Badge.vue";
import Switch from "@/components/ui/Switch.vue";
import Input from "@/components/ui/Input.vue";
import PasswordInput from "@/components/ui/PasswordInput.vue";
import Label from "@/components/ui/Label.vue";
import { Save, Send, CheckCircle2, XCircle, Network } from "lucide-vue-next";

const form = ref<SettingsPayload>({
  update_interval: 300,
  public_ip_service: "https://api.ipify.org",
  app_debug: false,
  debug_ip: "",
  enable_ipv6: false,
  public_ipv6_service: "https://api6.ipify.org",
  debug_ipv6: "",
  mail_host: "",
  mail_port: 465,
  mail_username: "",
  mail_password: "",
  mail_from_address: "",
  mail_from_name: "Cloudflare DDNS Updater",
  notification_email: "",
  notification_cc: "",
  notification_bcc: "",
});

const loading = ref(true);
const saving = ref(false);
const message = ref("");
const error = ref("");

const testingEmail = ref(false);
const testEmailResult = ref<TestEmailResult | null>(null);

async function load() {
  loading.value = true;
  const { data } = await api.get<SettingsPayload>("/settings");
  form.value = { ...data, mail_password: "" }; // no mostramos la contraseña guardada
  loading.value = false;
}

async function save() {
  saving.value = true;
  message.value = "";
  error.value = "";
  try {
    await api.put("/settings", form.value);
    message.value = "Ajustes guardados correctamente";
    await load();
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "No se pudieron guardar los ajustes";
  } finally {
    saving.value = false;
  }
}

async function sendTestEmail() {
  testingEmail.value = true;
  testEmailResult.value = null;
  try {
    const { data } = await api.post<TestEmailResult>("/settings/test-email");
    testEmailResult.value = data;
  } catch (e: any) {
    testEmailResult.value = { ok: false, message: e?.response?.data?.detail || "Error al enviar el correo" };
  } finally {
    testingEmail.value = false;
  }
}

onMounted(load);
</script>

<template>
  <AppLayout>
    <div class="mb-6">
      <h1 class="text-2xl font-bold">Ajustes</h1>
      <p class="text-muted-foreground">Configuración global del servicio DDNS</p>
    </div>

    <div v-if="!loading" class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Comprobación de IP</CardTitle>
          <CardDescription>Con qué frecuencia y servicio se comprueba la IP pública</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-1.5">
            <Label>Intervalo (segundos)</Label>
            <Input v-model.number="form.update_interval" type="number" min="30" />
          </div>
          <div class="space-y-1.5">
            <Label>Servicio de IP pública (IPv4)</Label>
            <Input v-model="form.public_ip_service" />
          </div>
          <div class="flex items-center gap-2">
            <input id="debug" v-model="form.app_debug" type="checkbox" class="h-4 w-4" />
            <Label for="debug">Modo debug (forzar una IP concreta)</Label>
          </div>
          <div v-if="form.app_debug" class="space-y-1.5">
            <Label>IP de depuración</Label>
            <Input v-model="form.debug_ip" placeholder="203.0.113.10" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2"><Network class="h-4 w-4" /> IPv6 (registros AAAA)</CardTitle>
          <CardDescription>Necesario solo si vas a mantener registros AAAA actualizados</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex items-center justify-between rounded-[5px] border px-3 py-2">
            <div>
              <p class="text-sm font-medium">Habilitar comprobación de IPv6</p>
              <p class="text-xs text-muted-foreground">Solo se consulta si tienes algún registro AAAA configurado.</p>
            </div>
            <Switch v-model="form.enable_ipv6" />
          </div>
          <div v-if="form.enable_ipv6" class="space-y-1.5">
            <Label>Servicio de IP pública (IPv6)</Label>
            <Input v-model="form.public_ipv6_service" />
          </div>
          <div v-if="form.enable_ipv6 && form.app_debug" class="space-y-1.5">
            <Label>IPv6 de depuración</Label>
            <Input v-model="form.debug_ipv6" placeholder="2001:db8::1" />
          </div>
        </CardContent>
      </Card>

      <Card class="lg:col-span-2">
        <CardHeader>
          <CardTitle>Notificaciones por email</CardTitle>
          <CardDescription>Servidor SMTP usado para avisar de cambios de IP</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div class="space-y-1.5">
              <Label>Host SMTP</Label>
              <Input v-model="form.mail_host" placeholder="smtp.miproveedor.com" />
            </div>
            <div class="space-y-1.5">
              <Label>Puerto</Label>
              <Input v-model.number="form.mail_port" type="number" />
            </div>
          </div>
          <div class="space-y-1.5">
            <Label>Usuario SMTP</Label>
            <Input v-model="form.mail_username" />
          </div>
          <div class="space-y-1.5">
            <Label>Contraseña SMTP</Label>
            <PasswordInput v-model="form.mail_password" placeholder="Dejar en blanco para no cambiar" />
          </div>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div class="space-y-1.5">
              <Label>Nombre remitente</Label>
              <Input v-model="form.mail_from_name" />
            </div>
            <div class="space-y-1.5">
              <Label>Email remitente</Label>
              <Input v-model="form.mail_from_address" />
            </div>
          </div>
          <div class="space-y-1.5">
            <Label>Destinatarios (Para)</Label>
            <Input v-model="form.notification_email" placeholder="alguien@correo.com, otro@correo.com" />
            <p class="text-xs text-muted-foreground">Varias direcciones separadas por comas.</p>
          </div>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div class="space-y-1.5">
              <Label>CC</Label>
              <Input v-model="form.notification_cc" placeholder="opcional, separadas por comas" />
            </div>
            <div class="space-y-1.5">
              <Label>CCO</Label>
              <Input v-model="form.notification_bcc" placeholder="opcional, separadas por comas" />
            </div>
          </div>

          <div class="flex items-center gap-3 border-t pt-4">
            <Button type="button" variant="outline" size="sm" :disabled="testingEmail" @click="sendTestEmail">
              <Send class="h-4 w-4" /> {{ testingEmail ? "Enviando..." : "Enviar email de prueba" }}
            </Button>
            <Badge v-if="testEmailResult?.ok" variant="success" class="gap-1">
              <CheckCircle2 class="h-3.5 w-3.5" /> {{ testEmailResult.message }}
            </Badge>
            <Badge v-else-if="testEmailResult && !testEmailResult.ok" variant="destructive" class="gap-1">
              <XCircle class="h-3.5 w-3.5" /> {{ testEmailResult.message }}
            </Badge>
          </div>
          <p class="text-xs text-muted-foreground">
            Guarda los ajustes antes de probar si acabas de cambiar el host, usuario o contraseña SMTP.
          </p>
        </CardContent>
      </Card>
    </div>

    <div class="mt-6 flex items-center gap-4">
      <Button :disabled="saving" @click="save">
        <Save class="h-4 w-4" /> {{ saving ? "Guardando..." : "Guardar ajustes" }}
      </Button>
      <p v-if="message" class="text-sm text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    </div>
  </AppLayout>
</template>
