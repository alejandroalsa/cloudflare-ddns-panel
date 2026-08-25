<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "@/lib/api";
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
import ThemeToggle from "@/components/ui/ThemeToggle.vue";
import { ShieldCheck, Eye, UserCircle, Save, Palette } from "lucide-vue-next";

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
        <CardTitle class="flex items-center gap-2"><Palette class="h-4 w-4" /> Apariencia</CardTitle>
        <CardDescription>Elige cómo se ve el panel en este navegador.</CardDescription>
      </CardHeader>
      <CardContent>
        <ThemeToggle />
      </CardContent>
    </Card>
  </AppLayout>
</template>
