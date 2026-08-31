<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type TwoFASetup, type TwoFAConfirmResult, type RecoveryCodesOut } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
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
import Badge from "@/components/ui/Badge.vue";
import Dialog from "@/components/ui/Dialog.vue";
import ThemeToggle from "@/components/ui/ThemeToggle.vue";
import RecoveryCodesDialog from "@/components/ui/RecoveryCodesDialog.vue";
import { ShieldCheck, Eye, UserCircle, Save, Palette, Smartphone, X, Check, KeyRound } from "lucide-vue-next";

const auth = useAuthStore();

const username = ref("");
const email = ref("");
const newPassword = ref("");

const saving = ref(false);
const message = ref("");
const error = ref("");

function loadFromStore() {
  username.value = auth.user?.username || "";
  email.value = auth.user?.email || "";
  newPassword.value = "";
}

async function save() {
  saving.value = true;
  message.value = "";
  error.value = "";
  try {
    const payload: Record<string, string> = { username: username.value, email: email.value };
    if (newPassword.value) payload.password = newPassword.value;
    await api.put("/auth/me", payload);
    await auth.fetchMe();
    newPassword.value = "";
    message.value = "Perfil actualizado correctamente";
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "No se pudo actualizar el perfil";
  } finally {
    saving.value = false;
  }
}

// ---------- 2FA: activar ----------
const showSetupDialog = ref(false);
const setupData = ref<TwoFASetup | null>(null);
const confirmCode = ref("");
const setupError = ref("");
const settingUp2fa = ref(false);
const confirming2fa = ref(false);

async function startSetup2fa() {
  settingUp2fa.value = true;
  setupError.value = "";
  confirmCode.value = "";
  try {
    const { data } = await api.post<TwoFASetup>("/auth/2fa/setup");
    setupData.value = data;
    showSetupDialog.value = true;
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "No se pudo iniciar la configuración de 2FA";
  } finally {
    settingUp2fa.value = false;
  }
}

async function confirmSetup2fa() {
  confirming2fa.value = true;
  setupError.value = "";
  try {
    const { data } = await api.post<TwoFAConfirmResult>("/auth/2fa/confirm", { code: confirmCode.value });
    await auth.fetchMe();
    showSetupDialog.value = false;
    recoveryCodes.value = data.recovery_codes;
    showRecoveryDialog.value = true;
  } catch (e: any) {
    setupError.value = e?.response?.data?.detail || "Código incorrecto";
  } finally {
    confirming2fa.value = false;
  }
}

// ---------- 2FA: desactivar (propia cuenta) ----------
const showDisableDialog = ref(false);
const disablePassword = ref("");
const disableError = ref("");
const disabling2fa = ref(false);

async function disable2fa() {
  disabling2fa.value = true;
  disableError.value = "";
  try {
    await api.post("/auth/2fa/disable", { password: disablePassword.value });
    await auth.fetchMe();
    showDisableDialog.value = false;
    disablePassword.value = "";
  } catch (e: any) {
    disableError.value = e?.response?.data?.detail || "No se pudo desactivar";
  } finally {
    disabling2fa.value = false;
  }
}

// ---------- Códigos de recuperación ----------
const showRecoveryDialog = ref(false);
const recoveryCodes = ref<string[]>([]);

const showRegenDialog = ref(false);
const regenPassword = ref("");
const regenError = ref("");
const regenerating = ref(false);

async function regenerateCodes() {
  regenerating.value = true;
  regenError.value = "";
  try {
    const { data } = await api.post<RecoveryCodesOut>("/auth/2fa/regenerate-codes", { password: regenPassword.value });
    showRegenDialog.value = false;
    regenPassword.value = "";
    recoveryCodes.value = data.codes;
    showRecoveryDialog.value = true;
  } catch (e: any) {
    regenError.value = e?.response?.data?.detail || "No se pudieron regenerar los códigos";
  } finally {
    regenerating.value = false;
  }
}

onMounted(loadFromStore);
</script>

<template>
  <AppLayout>
    <div class="mb-6">
      <h1 class="text-2xl font-bold">Mi perfil</h1>
      <p class="text-muted-foreground">Gestiona tu nombre de usuario, email y contraseña</p>
    </div>

    <Card class="max-w-lg">
      <CardHeader>
        <CardTitle class="flex items-center gap-2"><UserCircle class="h-4 w-4" /> Datos de la cuenta</CardTitle>
        <CardDescription>
          Rol actual:
          <Badge :variant="auth.isAdmin ? 'default' : 'secondary'" class="ml-1 gap-1">
            <ShieldCheck v-if="auth.isAdmin" class="h-3.5 w-3.5" />
            <Eye v-else class="h-3.5 w-3.5" />
            {{ auth.isAdmin ? "Admin" : "Solo lectura" }}
          </Badge>
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <form class="space-y-4" @submit.prevent="save">
          <div class="space-y-1.5">
            <Label>Nombre de usuario</Label>
            <Input v-model="username" required />
          </div>
          <div class="space-y-1.5">
            <Label>Email</Label>
            <Input v-model="email" type="email" />
          </div>
          <div class="space-y-1.5">
            <Label>Nueva contraseña</Label>
            <PasswordInput v-model="newPassword" placeholder="Dejar en blanco para no cambiarla" />
          </div>
          <p v-if="message" class="text-sm text-emerald-600">{{ message }}</p>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" :disabled="saving">
            <Save class="h-4 w-4" /> {{ saving ? "Guardando..." : "Guardar cambios" }}
          </Button>
        </form>
      </CardContent>
    </Card>

    <Card class="mt-6 max-w-lg">
      <CardHeader>
        <CardTitle class="flex items-center gap-2"><Smartphone class="h-4 w-4" /> Verificación en dos pasos (2FA)</CardTitle>
        <CardDescription>Añade una capa extra de seguridad con una app de autenticación (Google Authenticator, Authy...)</CardDescription>
      </CardHeader>
      <CardContent class="space-y-3">
        <div class="flex items-center justify-between rounded-[5px] border px-3 py-2">
          <Badge v-if="auth.user?.totp_enabled" variant="success" class="gap-1">
            <ShieldCheck class="h-3.5 w-3.5" /> Activada
          </Badge>
          <Badge v-else variant="secondary" class="gap-1">
            <Smartphone class="h-3.5 w-3.5" /> Desactivada
          </Badge>

          <Button v-if="!auth.user?.totp_enabled" size="sm" :disabled="settingUp2fa" @click="startSetup2fa">
            {{ settingUp2fa ? "Generando..." : "Activar 2FA" }}
          </Button>
          <Button v-else size="sm" variant="destructive" @click="showDisableDialog = true">
            Desactivar 2FA
          </Button>
        </div>

        <Button
          v-if="auth.user?.totp_enabled"
          variant="outline"
          size="sm"
          class="w-full"
          @click="showRegenDialog = true"
        >
          <KeyRound class="h-4 w-4" /> Regenerar códigos de recuperación
        </Button>
      </CardContent>
    </Card>

    <Card class="mt-6 max-w-lg">
      <CardHeader>
        <CardTitle class="flex items-center gap-2"><Palette class="h-4 w-4" /> Apariencia</CardTitle>
        <CardDescription>Elige cómo se ve el panel en este navegador.</CardDescription>
      </CardHeader>
      <CardContent>
        <ThemeToggle />
      </CardContent>
    </Card>

    <!-- Diálogo: activar 2FA -->
    <Dialog v-model:open="showSetupDialog">
      <h2 class="mb-1 text-lg font-semibold">Activar verificación en dos pasos</h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Escanea este código QR con tu app de autenticación y luego introduce el código de 6
        dígitos para confirmar.
      </p>
      <div v-if="setupData" class="space-y-4">
        <div class="flex justify-center rounded-[5px] border p-4">
          <img :src="setupData.qr_code_base64" alt="Código QR 2FA" class="h-48 w-48" />
        </div>
        <div class="space-y-1.5">
          <Label class="text-xs">¿No puedes escanear? Introduce este código manualmente:</Label>
          <Input :model-value="setupData.secret" readonly class="font-mono text-xs" />
        </div>
        <form class="space-y-3" @submit.prevent="confirmSetup2fa">
          <div class="space-y-1.5">
            <Label>Código de 6 dígitos</Label>
            <Input v-model="confirmCode" inputmode="numeric" maxlength="6" placeholder="123456" required />
          </div>
          <p v-if="setupError" class="text-sm text-destructive">{{ setupError }}</p>
          <div class="flex justify-end gap-2">
            <Button type="button" variant="outline" @click="showSetupDialog = false">
              <X class="h-4 w-4" /> Cancelar
            </Button>
            <Button type="submit" :disabled="confirming2fa">
              <Check class="h-4 w-4" /> {{ confirming2fa ? "Verificando..." : "Confirmar" }}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>

    <!-- Diálogo: desactivar 2FA -->
    <Dialog v-model:open="showDisableDialog">
      <h2 class="mb-1 text-lg font-semibold">Desactivar verificación en dos pasos</h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Introduce tu contraseña para confirmar que quieres desactivar el 2FA de tu cuenta.
      </p>
      <form class="space-y-4" @submit.prevent="disable2fa">
        <div class="space-y-1.5">
          <Label>Contraseña</Label>
          <PasswordInput v-model="disablePassword" required />
        </div>
        <p v-if="disableError" class="text-sm text-destructive">{{ disableError }}</p>
        <div class="flex justify-end gap-2">
          <Button type="button" variant="outline" @click="showDisableDialog = false">
            <X class="h-4 w-4" /> Cancelar
          </Button>
          <Button type="submit" variant="destructive" :disabled="disabling2fa">
            {{ disabling2fa ? "Desactivando..." : "Desactivar" }}
          </Button>
        </div>
      </form>
    </Dialog>

    <!-- Diálogo: regenerar códigos -->
    <Dialog v-model:open="showRegenDialog">
      <h2 class="mb-1 text-lg font-semibold">Regenerar códigos de recuperación</h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Esto invalida los códigos anteriores. Introduce tu contraseña para confirmar.
      </p>
      <form class="space-y-4" @submit.prevent="regenerateCodes">
        <div class="space-y-1.5">
          <Label>Contraseña</Label>
          <PasswordInput v-model="regenPassword" required />
        </div>
        <p v-if="regenError" class="text-sm text-destructive">{{ regenError }}</p>
        <div class="flex justify-end gap-2">
          <Button type="button" variant="outline" @click="showRegenDialog = false">
            <X class="h-4 w-4" /> Cancelar
          </Button>
          <Button type="submit" :disabled="regenerating">
            <KeyRound class="h-4 w-4" /> {{ regenerating ? "Generando..." : "Regenerar" }}
          </Button>
        </div>
      </form>
    </Dialog>

    <!-- Diálogo: mostrar códigos de recuperación (tras activar o regenerar) -->
    <RecoveryCodesDialog v-model:open="showRecoveryDialog" :codes="recoveryCodes" />
  </AppLayout>
</template>
