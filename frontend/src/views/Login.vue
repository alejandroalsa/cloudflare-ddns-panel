<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import PasswordInput from "@/components/ui/PasswordInput.vue";
import Label from "@/components/ui/Label.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import { LogIn, ExternalLink, ShieldCheck } from "lucide-vue-next";

const username = ref("");
const password = ref("");
const totpCode = ref("");
const needsTotp = ref(false);
const error = ref("");
const loading = ref(false);

const auth = useAuthStore();
const router = useRouter();

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    const done = await auth.login(username.value, password.value, totpCode.value || undefined);
    if (done) {
      router.push("/");
    } else {
      needsTotp.value = true;
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "No se pudo iniciar sesión";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-muted/30 p-4">
    <Card class="w-full max-w-sm">
      <CardHeader class="items-center text-center">
        <img src="/logo.svg" alt="Cloudflare DDNS Panel" class="mb-2 h-12 w-12" />
        <CardTitle>Cloudflare DDNS Panel</CardTitle>
        <CardDescription>
          {{ needsTotp ? "Introduce el código de tu app de autenticación" : "Inicia sesión para gestionar tus dominios" }}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form v-if="!needsTotp" class="space-y-4" @submit.prevent="onSubmit">
          <div class="space-y-1.5">
            <Label for="username">Usuario</Label>
            <Input id="username" v-model="username" autocomplete="username" required />
          </div>
          <div class="space-y-1.5">
            <Label for="password">Contraseña</Label>
            <PasswordInput
              id="password"
              v-model="password"
              autocomplete="current-password"
              required
            />
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" class="w-full" :disabled="loading">
            <LogIn class="h-4 w-4" />
            {{ loading ? "Entrando..." : "Entrar" }}
          </Button>
        </form>

        <form v-else class="space-y-4" @submit.prevent="onSubmit">
          <div class="space-y-1.5">
            <Label for="totp">Código de verificación</Label>
            <Input id="totp" v-model="totpCode" maxlength="9" autofocus placeholder="123456 o XXXX-XXXX" required />
            <p class="text-xs text-muted-foreground">
              Introduce el código de tu app de autenticación, o un código de recuperación si no
              tienes acceso a ella.
            </p>
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" class="w-full" :disabled="loading">
            <ShieldCheck class="h-4 w-4" />
            {{ loading ? "Verificando..." : "Verificar" }}
          </Button>
        </form>
      </CardContent>
    </Card>
    <a
      href="https://github.com/alejandroalsa/cloudflare-ddns-updater"
      target="_blank"
      rel="noopener noreferrer"
      class="mt-6 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
    >
      <ExternalLink class="h-3.5 w-3.5" />
      Creado por alejandroalsa
    </a>
  </div>
</template>
