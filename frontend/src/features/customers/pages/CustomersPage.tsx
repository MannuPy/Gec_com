import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Pencil, Plus, Search } from "lucide-react";

import { customersApi } from "@/api/endpoints/customers";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import { CUSTOMER_TYPES, type Customer, type CustomerWritePayload } from "@/types/customer";
import { formatCurrency } from "@/utils/format";

const EMPTY_FORM: CustomerWritePayload = {
  full_name: "",
  phone: "",
  customer_type: "SIMPLE",
  credit_limit: "0",
};

/**
 * Gestion des clients (RF-21) : liste, recherche, création et édition.
 * Cf. GET/POST/PUT /api/v1/sales/customers.
 */
export default function CustomersPage() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canWrite = hasPermission("customers:write");
  const queryClient = useQueryClient();

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState<CustomerWritePayload>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const customersQuery = useQuery({
    queryKey: ["customers", search],
    queryFn: () => customersApi.list(search || undefined),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setModalOpen(true);
  };

  const openEdit = (customer: Customer) => {
    setEditing(customer);
    setForm({
      full_name: customer.full_name,
      phone: customer.phone ?? "",
      customer_type: customer.customer_type,
      credit_limit: customer.credit_limit,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const saveMutation = useMutation({
    mutationFn: (payload: CustomerWritePayload) =>
      editing ? customersApi.update(editing.id, payload) : customersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      setModalOpen(false);
    },
    onError: (error) => {
      setFormError(getApiErrorMessage(error, "Impossible d'enregistrer le client."));
    },
  });

  const handleSubmit = () => {
    setFormError(null);
    if (!form.full_name.trim()) {
      setFormError("Le nom du client est obligatoire.");
      return;
    }
    saveMutation.mutate({
      ...form,
      phone: form.phone?.trim() ? form.phone.trim() : null,
    });
  };

  const customers = customersQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Clients</h1>
          <p className="text-sm text-muted">Clients particuliers et techniciens (tarifs et crédit)</p>
        </div>
        {canWrite && (
          <button type="button" className="btn-primary" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Nouveau client
          </button>
        )}
      </div>

      <div className="card space-y-4">
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            type="text"
            className="input pl-9"
            placeholder="Rechercher par nom ou téléphone"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>

        {customersQuery.isLoading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement...
          </div>
        )}

        {customersQuery.isError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(customersQuery.error, "Impossible de charger les clients.")}
          </div>
        )}

        {customersQuery.isSuccess && (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Téléphone</th>
                  <th>Type</th>
                  <th className="text-right">Encours</th>
                  <th className="text-right">Limite de crédit</th>
                  {canWrite && <th></th>}
                </tr>
              </thead>
              <tbody>
                {customers.length === 0 && (
                  <tr>
                    <td colSpan={canWrite ? 6 : 5} className="text-center text-muted">
                      Aucun client trouvé.
                    </td>
                  </tr>
                )}
                {customers.map((customer) => (
                  <tr key={customer.id}>
                    <td className="font-medium text-primary-dark">{customer.full_name}</td>
                    <td>{customer.phone ?? "-"}</td>
                    <td>
                      {customer.customer_type === "TECHNICIEN" ? (
                        <span className="badge badge-info">Technicien</span>
                      ) : (
                        <span className="badge badge-success">Particulier</span>
                      )}
                    </td>
                    <td className="text-right">{formatCurrency(customer.credit_balance)}</td>
                    <td className="text-right">{formatCurrency(customer.credit_limit)}</td>
                    {canWrite && (
                      <td className="text-right">
                        <button type="button" className="btn-ghost p-1.5" onClick={() => openEdit(customer)}>
                          <Pencil className="h-4 w-4" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalOpen && (
        <Modal title={editing ? "Modifier le client" : "Nouveau client"} onClose={() => setModalOpen(false)}>
          <div className="space-y-4">
            <div>
              <label className="label">Nom complet</label>
              <input
                type="text"
                className="input"
                value={form.full_name}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              />
            </div>

            <div>
              <label className="label">Téléphone</label>
              <input
                type="text"
                className="input"
                value={form.phone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              />
            </div>

            <div>
              <label className="label">Type de client</label>
              <select
                className="input"
                value={form.customer_type}
                onChange={(e) =>
                  setForm((f) => ({ ...f, customer_type: e.target.value as CustomerWritePayload["customer_type"] }))
                }
              >
                {CUSTOMER_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type === "TECHNICIEN" ? "Technicien (tarif spécial)" : "Particulier"}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Limite de crédit (FCFA)</label>
              <input
                type="number"
                min="0"
                step="1"
                className="input"
                value={form.credit_limit ?? "0"}
                onChange={(e) => setForm((f) => ({ ...f, credit_limit: e.target.value }))}
              />
              <p className="mt-1 text-xs text-muted">Plafond d'encours autorisé pour les ventes à crédit (RG-26).</p>
            </div>

            {formError && (
              <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setModalOpen(false)}>
                Annuler
              </button>
              <button type="button" className="btn-primary" disabled={saveMutation.isPending} onClick={handleSubmit}>
                {saveMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                {editing ? "Enregistrer" : "Créer"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
