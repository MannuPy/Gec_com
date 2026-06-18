import { apiClient } from "@/api/client";
import type { Role, User, UserCreatePayload, UserListParams, UserUpdatePayload } from "@/types/user";

export const usersApi = {
  roles: () => apiClient.get<Role[]>("/users/roles").then((r) => r.data),

  list: (params: UserListParams = {}) =>
    apiClient.get<User[]>("/users", { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  create: (payload: UserCreatePayload) =>
    apiClient.post<User>("/users", payload).then((r) => r.data),

  update: (id: string, payload: UserUpdatePayload) =>
    apiClient.put<User>(`/users/${id}`, payload).then((r) => r.data),
};
