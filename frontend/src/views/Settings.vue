<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type SettingsPayload } from "@/lib/api";
import AppLayout from "@/components/AppLayout.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import Button from "@/components/ui/Button.vue";
import { Save } from "lucide-vue-next";
import Input from "@/components/ui/Input.vue";
import PasswordInput from "@/components/ui/PasswordInput.vue";
import Label from "@/components/ui/Label.vue";

const form = ref<SettingsPayload>({
  update_interval: 300,
  public_ip_service: "https://api.ipify.org",
  app_debug: false,
  debug_ip: "",
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
            <Label>Servicio de IP pública</Label>
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
          <CardTitle>Notificaciones por email</CardTitle>
          <CardDescription>Servidor SMTP usado para avisar de cambios de IP</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
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
          <div class="space-y-1.5">
            <Label>Nombre remitente</Label>
            <Input v-model="form.mail_from_name" />
          </div>
          <div class="space-y-1.5">
            <Label>Email remitente</Label>
            <Input v-model="form.mail_from_address" />
          </div>
          <div class="space-y-1.5">
            <Label>Destinatarios (Para)</Label>
            <Input v-model="form.notification_email" placeholder="alguien@correo.com, otro@correo.com" />
            <p class="text-xs text-muted-foreground">Varios direcciones separadas por comas.</p>
          </div>
          <div class="space-y-1.5">
            <Label>CC</Label>
            <Input v-model="form.notification_cc" placeholder="opcional, separadas por comas" />
          </div>
          <div class="space-y-1.5">
            <Label>CCO</Label>
            <Input v-model="form.notification_bcc" placeholder="opcional, separadas por comas" />
          </div>
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
