import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/app/store";
import type { RefreshResponse } from "@/types/auth";

/**
 * Base URL de l'API.
 * En dev, Vite proxy `/api` -> backend Flask (cf. vite.config.ts), donc on
 * peut laisser VITE_API_URL vide. En prod, définir VITE_API_URL (ex. via
 * docker-compose / nginx).
 */
const baseURL = import.meta.env.VITE_API_URL || "/api/v1";

export const apiClient = axios.create({ baseURL });

// Instance dédiée au refresh, sans intercepteur, pour éviter les boucles.
const refreshClient = axios.create({ baseURL });

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) {
    throw new Error("Aucun refresh token disponible.");
  }

  const { data } = await refreshClient.post<RefreshResponse>(
    "/auth/refresh",
    {},
    { headers: { Authorization: `Bearer ${refreshToken}` } }
  );

  useAuthStore.getState().setAccessToken(data.access_token);
  return data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    const status = error.response?.status;
    const errorCode = (error.response?.data as { error?: string } | undefined)?.error;

    const isAuthRoute = originalRequest?.url?.includes("/auth/");

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthRoute) {
      originalRequest._retry = true;
      try {
        // Évite les rafraîchissements concurrents multiples.
        refreshPromise = refreshPromise ?? refreshAccessToken();
        const newToken = await refreshPromise;
        refreshPromise = null;

        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        refreshPromise = null;
        useAuthStore.getState().clearSession();
        window.location.assign("/login");
        return Promise.reject(refreshError);
      }
    }

    if (status === 401 && (errorCode === "TOKEN_EXPIRED" || isAuthRoute)) {
      useAuthStore.getState().clearSession();
    }

    return Promise.reject(error);
  }
);

/** Extrait un message d'erreur lisible depuis une erreur Axios de l'API. */
export function getApiErrorMessage(error: unknown, fallback = "Une erreur est survenue."): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string; error?: string } | undefined;
    return data?.message || data?.error || fallback;
  }
  return fallback;
}
