import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";

import { productsApi } from "@/api/endpoints/products";
import { usersApi } from "@/api/endpoints/users";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import type { User, UserCreatePayload, UserUpdatePayload } from "@/types/user";
import { formatDateTime } from "@/utils/format";

const LANGUAGES: { value: "fr" | "mos"; label: string }[] = [
  { value: "fr", label: "Français" },
  { value: "mos", label: "Mooré" },
];

/**
 * Gestion des utilisateurs (RF-01/RF-02, réservé ADMIN) : liste, création
 * et édition (rôle, site, statut, mot de passe).
 * Cf. GET/POST/PUT /api/v1/users, GET /users/roles.
 */
export default function UsersPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);

  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list(),
  });

  const rolesQuery = useQuery({
    queryKey: ["roles"],
    queryFn: () => usersApi.roles(),
  });

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
  });

  const users = usersQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Utilisateurs</h1>
          <p className="text-sm text-muted">Comptes, rôles et affectations par site (RBAC)</p>
        </div>
        <button
          type="button"
          className="btn-primary"
          onClick={() => {
            setEditing(null);
            setModalOpen(true);
          }}
        >
          <Plus className="h-4 w-4" />
          Nouvel utilisateur
        </button>
      </div>

      <div className="card">
        {usersQuery.isLoading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement...
          </div>
        )}

        {usersQuery.isError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(usersQuery.error, "Impossible de charger les utilisateurs.")}
          </div>
        )}

        {usersQuery.isSuccess && (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Email</th>
                  <th>Rôle</th>
                  <th>Site</th>
                  <th>Langue</th>
                  <th>Statut</th>
                  <th>Créé le</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 && (
                  <tr>
                    <td colSpan={8} className="text-center text-muted">
                      Aucun utilisateur trouvé.
                    </td>
                  </tr>
                )}
                {users.map((u) => (
                  <tr key={u.id}>
                    <td className="font-medium text-primary-dark">{u.full_name}</td>
                    <td>{u.email}</td>
                    <td>{u.role_name ?? "-"}</td>
                    <td>{u.branch_name ?? "Tous les sites"}</td>
                    <td>{u.language === "mos" ? "Mooré" : "Français"}</td>
                    <td>
                      {u.is_active ? (
                        <span className="badge badge-success">Actif</span>
                      ) : (
                        <span className="badge badge-danger">Inactif</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(u.created_at)}</td>
                    <td className="text-right">
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => {
                          setEditing(u);
                          setModalOpen(true);
                        }}
                      >
                        Modifier
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalOpen && (
        <UserFormModal
          editing={editing}
          roles={rolesQuery.data ?? []}
          branches={branchesQuery.data ?? []}
          onClose={() => setModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            setModalOpen(false);
          }}
        />
      )}
    </div>
  );
}

interface UserFormModalProps {
  editing: User | null;
  roles: { id: string; name: string }[];
  branches: { id: string; name: string }[];
  onClose: () => void;
  onSuccess: () => void;
}

function UserFormModal({ editing, roles, branches, onClose, onSuccess }: UserFormModalProps) {
  const [email, setEmail] = useState(editing?.email ?? "");
  const [fullName, setFullName] = useState(editing?.full_name ?? "");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState(editing?.role_id ?? roles[0]?.id ?? "");
  const [branchId, setBranchId] = useState(editing?.branch_id ?? "");
  const [language, setLanguage] = useState<"fr" | "mos">((editing?.language as "fr" | "mos") ?? "fr");
  const [isActive, setIsActive] = useState(editing?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: UserCreatePayload) => usersApi.create(payload),
    onSuccess,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de créer l'utilisateur.")),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: UserUpdatePayload) => usersApi.update(editing!.id, payload),
    onSuccess,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de mettre à jour l'utilisateur.")),
  });

  const handleSubmit = () => {
    setFormError(null);
    if (!fullName.trim()) {
      setFormError("Le nom complet est obligatoire.");
      return;
    }
    if (!roleId) {
      setFormError("Veuillez sélectionner un rôle.");
      return;
    }

    if (editing) {
      const payload: UserUpdatePayload = {
        full_name: fullName.trim(),
        role_id: roleId,
        branch_id: branchId || null,
        language,
        is_active: isActive,
      };
      if (password.trim()) {
        payload.password = password.trim();
      }
      updateMutation.mutate(payload);
      return;
    }

    if (!email.trim()) {
      setFormError("L'email est obligatoire.");
      return;
    }
    if (password.trim().length < 8) {
      setFormError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    createMutation.mutate({
      email: email.trim(),
      password: password.trim(),
      full_name: fullName.trim(),
      role_id: roleId,
      branch_id: branchId || null,
      language,
    });
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal title={editing ? "Modifier l'utilisateur" : "Nouvel utilisateur"} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="label">Nom complet</label>
          <input type="text" className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </div>

        <div>
          <label className="label">Email</label>
          <input
            type="email"
            className="input"
            value={email}
            disabled={!!editing}
            onChange={(e) => setEmail(e.target.value)}
          />
          {editing && <p className="mt-1 text-xs text-muted">L'email ne peut pas être modifié.</p>}
        </div>

        <div>
          <label className="label">{editing ? "Nouveau mot de passe (optionnel)" : "Mot de passe"}</label>
          <input
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={editing ? "Laisser vide pour ne pas changer" : "Minimum 8 caractères"}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Rôle</label>
            <select className="input" value={roleId} onChange={(e) => setRoleId(e.target.value)}>
              <option value="">Sélectionner</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Site</label>
            <select className="input" value={branchId} onChange={(e) => setBranchId(e.target.value)}>
              <option value="">Tous les sites</option>
              {branches.map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Langue</label>
          <select className="input" value={language} onChange={(e) => setLanguage(e.target.value as "fr" | "mos")}>
            {LANGUAGES.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>

        {editing && (
          <label className="flex items-center gap-2 text-sm text-primary-dark">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Compte actif
          </label>
        )}

        {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button type="button" className="btn-primary" disabled={isPending} onClick={handleSubmit}>
            {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {editing ? "Enregistrer" : "Créer"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
