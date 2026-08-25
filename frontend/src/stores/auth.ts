import { defineStore } from "pinia";
import { api, type User } from "@/lib/api";

interface LoginResponse {
  access_token: string;
  token_type: string;
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
    async login(username: string, password: string) {
      const form = new URLSearchParams();
      form.append("username", username);
      form.append("password", password);
      const { data } = await api.post<LoginResponse>("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      this.token = data.access_token;
      localStorage.setItem("ddns_token", data.access_token);
      await this.fetchMe();
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
