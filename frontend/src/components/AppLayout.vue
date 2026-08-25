<script setup lang="ts">
import { ref } from "vue";
import SidebarContent from "@/components/SidebarContent.vue";
import { Menu, X } from "lucide-vue-next";

const mobileMenuOpen = ref(false);
</script>

<template>
  <div class="flex min-h-screen flex-col md:flex-row">
    <!-- Barra superior: solo móvil -->
    <header class="flex items-center justify-between border-b bg-card px-4 py-3 md:hidden">
      <div class="flex items-center gap-2">
        <img src="/logo.svg" alt="Cloudflare DDNS Panel" class="h-6 w-6" />
        <span class="text-base font-semibold">DDNS Panel</span>
      </div>
      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-[5px] hover:bg-accent"
        @click="mobileMenuOpen = true"
      >
        <Menu class="h-5 w-5" />
      </button>
    </header>

    <!-- Drawer: solo móvil -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="mobileMenuOpen"
          class="fixed inset-0 z-50 flex bg-black/50 md:hidden"
          @click.self="mobileMenuOpen = false"
        >
          <div class="flex h-full w-72 max-w-[85vw] flex-col bg-card px-4 py-6 shadow-lg">
            <div class="mb-6 flex items-center justify-between px-2">
              <div class="flex items-center gap-2">
                <img src="/logo.svg" alt="Cloudflare DDNS Panel" class="h-7 w-7" />
                <span class="text-lg font-semibold">DDNS Panel</span>
              </div>
              <button
                type="button"
                class="flex h-8 w-8 items-center justify-center rounded-[5px] hover:bg-accent"
                @click="mobileMenuOpen = false"
              >
                <X class="h-4 w-4" />
              </button>
            </div>
            <SidebarContent @navigate="mobileMenuOpen = false" />
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Sidebar: solo desktop -->
    <aside class="hidden w-64 shrink-0 flex-col border-r bg-card px-4 py-6 md:flex">
      <div class="mb-6 flex items-center gap-2 px-2">
        <img src="/logo.svg" alt="Cloudflare DDNS Panel" class="h-7 w-7" />
        <span class="text-lg font-semibold">DDNS Panel</span>
      </div>
      <SidebarContent />
    </aside>

    <main class="flex-1 bg-muted/30 p-4 sm:p-6 md:p-8">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
