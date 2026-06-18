/** Cf. backend/app/blueprints/users/schemas.py */
import type { RoleName } from "@/types/auth";

export interface Role {
  id: string;
  name: RoleName | string;
  description: string | null;
  permissions: string[];
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role_id: string;
  role_name: string | null;
  branch_id: string | null;
  branch_name: string | null;
  language: string;
  is_active: boolean;
  created_at: string;
}

export interface UserCreatePayload {
  email: string;
  password: string;
  full_name: string;
  role_id: string;
  branch_id?: string | null;
  language?: "fr" | "mos";
}

export interface UserUpdatePayload {
  full_name?: string;
  role_id?: string;
  branch_id?: string | null;
  language?: "fr" | "mos";
  is_active?: boolean;
  password?: string;
}

export interface UserListParams {
  branch_id?: string;
  role_id?: string;
}
