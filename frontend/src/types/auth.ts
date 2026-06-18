/**
 * Types liés à l'authentification et au RBAC.
 * Cf. backend/app/blueprints/auth/routes.py (_serialize_user, _build_additional_claims)
 * et docs/18-SECURITE.md.
 */

export type RoleName = "ADMIN" | "MAGASINIER" | "VENDEUR";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: RoleName;
  permissions: string[];
  branch_id: string | null;
  branch_name: string | null;
  language: string;
  /** RF-05 : si vrai, l'utilisateur doit changer son mot de passe avant de
   * pouvoir accéder au reste de l'application (compte créé/réinitialisé par
   * un administrateur). */
  must_change_password: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export interface RefreshResponse {
  access_token: string;
}
