import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AuthUser } from "@/types/auth";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;

  /** Enregistre la session après un login réussi ou un refresh. */
  setSession: (payload: {
    accessToken: string;
    refreshToken?: string;
    user?: AuthUser;
  }) => void;

  /** Met seulement à jour le token d'accès (utilisé par l'intercepteur de refresh). */
  setAccessToken: (accessToken: string) => void;

  /** Met à jour le profil utilisateur courant (ex. après changement de mot de passe, RF-05). */
  updateUser: (user: AuthUser) => void;

  /** Efface la session (logout, token expiré). */
  clearSession: () => void;

  /** Vérifie qu'une permission est présente (RBAC). Le wildcard "*" donne tous les droits. */
  hasPermission: (code: string) => boolean;

  /** Vérifie le rôle courant. */
  hasRole: (...roles: string[]) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setSession: ({ accessToken, refreshToken, user }) =>
        set((state) => ({
          accessToken,
          refreshToken: refreshToken ?? state.refreshToken,
          user: user ?? state.user,
        })),

      setAccessToken: (accessToken) => set({ accessToken }),

      updateUser: (user) => set({ user }),

      clearSession: () => set({ accessToken: null, refreshToken: null, user: null }),

      hasPermission: (code) => {
        const permissions = get().user?.permissions ?? [];
        return permissions.includes("*") || permissions.includes(code);
      },

      hasRole: (...roles) => {
        const role = get().user?.role;
        return !!role && roles.includes(role);
      },
    }),
    {
      name: "gescom-bf-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
);

export const isAuthenticated = () => !!useAuthStore.getState().accessToken;
