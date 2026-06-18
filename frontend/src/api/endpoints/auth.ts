import { apiClient } from "@/api/client";
import type { AuthUser, LoginResponse } from "@/types/auth";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export const authApi = {
  login: (payload: LoginPayload) =>
    apiClient.post<LoginResponse>("/auth/login", payload).then((r) => r.data),

  me: () => apiClient.get<AuthUser>("/auth/me").then((r) => r.data),

  logout: () => apiClient.post("/auth/logout").then((r) => r.data),

  /** RF-05 : change le mot de passe de l'utilisateur connecté. */
  changePassword: (payload: ChangePasswordPayload) =>
    apiClient.post<AuthUser>("/auth/change-password", payload).then((r) => r.data),
};
