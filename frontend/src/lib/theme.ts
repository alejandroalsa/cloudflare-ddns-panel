import { ref, watch } from "vue";

export type ThemeMode = "light" | "dark" | "system";

const STORAGE_KEY = "ddns_theme";
const mode = ref<ThemeMode>((localStorage.getItem(STORAGE_KEY) as ThemeMode) || "system");
const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

// Si no hay sesión iniciada, ignoramos la preferencia guardada y usamos el sistema
let authenticated = false;

function resolveIsDark(m: ThemeMode): boolean {
  if (m === "system") return mediaQuery.matches;
  return m === "dark";
}

function applyTheme(m: ThemeMode) {
  const isDark = resolveIsDark(m);
  document.documentElement.classList.toggle("dark", isDark);
}

function currentEffectiveMode(): ThemeMode {
  return authenticated ? mode.value : "system";
}

// Aplicar inmediatamente al cargar el módulo (evita parpadeo) — sin sesión, siempre sistema
applyTheme("system");

// Si el modo efectivo es "system", seguir los cambios del SO en vivo
mediaQuery.addEventListener("change", () => {
  if (currentEffectiveMode() === "system") applyTheme("system");
});

watch(mode, (m) => {
  localStorage.setItem(STORAGE_KEY, m);
  if (authenticated) applyTheme(m);
});

/** Se llama cuando cambia el estado de autenticación (login/logout) para aplicar el tema correcto. */
export function setThemeAuthState(isAuthenticated: boolean) {
  authenticated = isAuthenticated;
  applyTheme(currentEffectiveMode());
}

export function useTheme() {
  function setTheme(m: ThemeMode) {
    mode.value = m;
  }
  return { mode, setTheme };
}
