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
import { LogIn, ExternalLink } from "lucide-vue-next";

const username = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

const auth = useAuthStore();
const router = useRouter();

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(username.value, password.value);
    router.push("/");
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
        <CardDescription>Inicia sesión para gestionar tus dominios</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="onSubmit">
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
