import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ddns_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("ddns_token");
      localStorage.removeItem("ddns_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ---------- Tipos ----------
export type UserRole = "admin" | "viewer";

export interface User {
  id: number;
  username: string;
  email: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Record {
  id: number;
  zone_id: number;
  name: string;
  last_ip: string | null;
  last_updated: string | null;
  proxied: boolean | null;
}

export interface Zone {
  id: number;
  domain: string;
  zone_id: string;
  created_at: string;
  records: Record[];
  api_token_preview: string | null;
}

export interface SettingsPayload {
  update_interval: number;
  public_ip_service: string;
  app_debug: boolean;
  debug_ip: string | null;
  mail_host: string | null;
  mail_port: number;
  mail_username: string | null;
  mail_password: string | null;
  mail_from_address: string | null;
  mail_from_name: string;
  notification_email: string | null;
  notification_cc: string | null;
  notification_bcc: string | null;
}

export interface UpdateLog {
  id: number;
  timestamp: string;
  old_ip: string | null;
  new_ip: string | null;
  changed: boolean;
  domains_updated: string | null;
  success: boolean;
  message: string | null;
  source: string;
}

export interface StatusOut {
  current_ip: string | null;
  last_check: string | null;
  total_zones: number;
  total_records: number;
  recent_logs: UpdateLog[];
}

// ---------- Import / Export ----------
export interface ZoneImportEntry {
  api_token: string;
  zone_id: string;
  records: string[];
}

export interface ImportPayload {
  domains: { [domain: string]: ZoneImportEntry };
}

export interface ImportResult {
  created: string[];
  updated: string[];
  skipped: string[];
}
