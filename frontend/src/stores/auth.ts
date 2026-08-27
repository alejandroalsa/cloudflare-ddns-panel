import { defineStore } from "pinia";
import { api, type User } from "@/lib/api";

interface LoginResponse {
  access_token: string | null;
  token_type: string;
  totp_required: boolean;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("ddns_token") as string | null,
    user: JSON.parse(localStorage.getItem("ddns_user") || "null") as User | null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === "admin",
  },
  actions: {
    /** Devuelve true si el login se completó, false si hace falta el código 2FA. */
    async login(username: string, password: string, totpCode?: string): Promise<boolean> {
      const { data } = await api.post<LoginResponse>("/auth/login", {
        username,
        password,
        totp_code: totpCode || null,
      });
      if (data.totp_required) {
        return false;
      }
      this.token = data.access_token;
      localStorage.setItem("ddns_token", data.access_token as string);
      await this.fetchMe();
      return true;
    },
    async fetchMe() {
      const { data } = await api.get<User>("/auth/me");
      this.user = data;
      localStorage.setItem("ddns_user", JSON.stringify(data));
    },
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("ddns_token");
      localStorage.removeItem("ddns_user");
    },
  },
});
