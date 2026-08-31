<script setup lang="ts">
import { RouterLink, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import Button from "@/components/ui/Button.vue";
import {
  LayoutDashboard,
  Globe,
  Settings as SettingsIcon,
  Users,
  LogOut,
  UserCircle,
  ExternalLink,
  ScrollText,
} from "lucide-vue-next";

const emit = defineEmits<{ navigate: [] }>();

const auth = useAuthStore();
const router = useRouter();

function logout() {
  auth.logout();
  router.push("/login");
  emit("navigate");
}
</script>

<template>
  <div class="flex h-full flex-col">
    <nav class="flex flex-1 flex-col gap-1">
      <RouterLink
        to="/"
        class="flex items-center gap-3 rounded-[5px] px-3 py-2 text-sm font-medium hover:bg-accent"
        active-class="bg-accent text-accent-foreground"
        @click="emit('navigate')"
      >
        <LayoutDashboard class="h-4 w-4" /> Dashboard
      </RouterLink>
      <RouterLink
        to="/domains"
        class="flex items-center gap-3 rounded-[5px] px-3 py-2 text-sm font-medium hover:bg-accent"
        active-class="bg-accent text-accent-foreground"
        @click="emit('navigate')"
      >
        <Globe class="h-4 w-4" /> Dominios
      </RouterLink>
      <RouterLink
        v-if="auth.isAdmin"
        to="/settings"
        class="flex items-center gap-3 rounded-[5px] px-3 py-2 text-sm font-medium hover:bg-accent"
        active-class="bg-accent text-accent-foreground"
        @click="emit('navigate')"
      >
        <SettingsIcon class="h-4 w-4" /> Ajustes
      </RouterLink>
      <RouterLink
        v-if="auth.isAdmin"
        to="/users"
        class="flex items-center gap-3 rounded-[5px] px-3 py-2 text-sm font-medium hover:bg-accent"
        active-class="bg-accent text-accent-foreground"
        @click="emit('navigate')"
      >
        <Users class="h-4 w-4" /> Usuarios
      </RouterLink>
      <RouterLink
        v-if="auth.isAdmin"
        to="/audit"
        class="flex items-center gap-3 rounded-[5px] px-3 py-2 text-sm font-medium hover:bg-accent"
        active-class="bg-accent text-accent-foreground"
        @click="emit('navigate')"
      >
        <ScrollText class="h-4 w-4" /> Auditoría
      </RouterLink>
      <RouterLink
        to="/profile"
        class="flex items-center gap-3 rounded-[5px] px-3 py-2 text-sm font-medium hover:bg-accent"
        active-class="bg-accent text-accent-foreground"
        @click="emit('navigate')"
      >
        <UserCircle class="h-4 w-4" /> Mi perfil
      </RouterLink>
    </nav>

    <div class="mt-auto border-t pt-4">
      <RouterLink
        to="/profile"
        class="flex items-center gap-2 rounded-[5px] px-2 py-1.5 hover:bg-accent"
        active-class="bg-accent text-accent-foreground"
        @click="emit('navigate')"
      >
        <div>
          <p class="text-sm font-medium">{{ auth.user?.username }}</p>
          <p class="text-xs capitalize text-muted-foreground">{{ auth.user?.role }}</p>
        </div>
      </RouterLink>
      <Button variant="ghost" size="sm" class="mt-2 w-full justify-start" @click="logout">
        <LogOut class="h-4 w-4" /> Cerrar sesión
      </Button>

      <a
        href="https://github.com/alejandroalsa/cloudflare-ddns-updater"
        target="_blank"
        rel="noopener noreferrer"
        class="mt-4 flex items-center gap-1.5 px-2 text-xs text-muted-foreground hover:text-foreground"
      >
        <ExternalLink class="h-3.5 w-3.5" />
        Creado por alejandroalsa
      </a>
    </div>
  </div>
</template>
