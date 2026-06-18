import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { KeyRound, Loader2, LogOut } from "lucide-react";

import { authApi } from "@/api/endpoints/auth";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";

const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Le mot de passe actuel est requis."),
    new_password: z
      .string()
      .min(8, "Le nouveau mot de passe doit contenir au moins 8 caractères."),
    confirm_password: z.string().min(1, "Veuillez confirmer le nouveau mot de passe."),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Les mots de passe ne correspondent pas.",
    path: ["confirm_password"],
  });

type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

/**
 * Page de changement de mot de passe obligatoire (RF-05).
 *
 * Affichée à la place du reste de l'application lorsque
 * `user.must_change_password` est vrai (compte créé ou réinitialisé par un
 * administrateur, cf. ProtectedRoute). Une fois le mot de passe changé,
 * `must_change_password` repasse à `false` et l'utilisateur est redirigé
 * vers l'accueil.
 */
export default function ChangePasswordPage() {
  const user = useAuthStore((s) => s.user);
  const updateUser = useAuthStore((s) => s.updateUser);
  const clearSession = useAuthStore((s) => s.clearSession);
  const navigate = useNavigate();

  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { current_password: "", new_password: "", confirm_password: "" },
  });

  const onSubmit = async (values: ChangePasswordFormValues) => {
    setApiError(null);
    setIsSubmitting(true);
    try {
      const updated = await authApi.changePassword({
        current_password: values.current_password,
        new_password: values.new_password,
      });
      updateUser(updated);
      navigate("/", { replace: true });
    } catch (error) {
      setApiError(getApiErrorMessage(error, "Impossible de changer le mot de passe."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Le jeton est peut-être déjà expiré : on déconnecte localement quoi qu'il arrive.
    }
    clearSession();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white">
            <KeyRound className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-semibold text-primary-dark">Changement de mot de passe</h1>
          <p className="text-sm text-muted">
            {user
              ? `Bonjour ${user.full_name}, vous devez définir un nouveau mot de passe avant de continuer.`
              : "Vous devez définir un nouveau mot de passe avant de continuer."}
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
          {apiError && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{apiError}</div>
          )}

          <div>
            <label htmlFor="current_password" className="label">
              Mot de passe actuel
            </label>
            <input
              id="current_password"
              type="password"
              autoComplete="current-password"
              className="input"
              placeholder="********"
              {...register("current_password")}
            />
            {errors.current_password && (
              <p className="error-text">{errors.current_password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="new_password" className="label">
              Nouveau mot de passe
            </label>
            <input
              id="new_password"
              type="password"
              autoComplete="new-password"
              className="input"
              placeholder="8 caractères minimum"
              {...register("new_password")}
            />
            {errors.new_password && <p className="error-text">{errors.new_password.message}</p>}
          </div>

          <div>
            <label htmlFor="confirm_password" className="label">
              Confirmer le nouveau mot de passe
            </label>
            <input
              id="confirm_password"
              type="password"
              autoComplete="new-password"
              className="input"
              placeholder="********"
              {...register("confirm_password")}
            />
            {errors.confirm_password && (
              <p className="error-text">{errors.confirm_password.message}</p>
            )}
          </div>

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <KeyRound className="h-4 w-4" />
            )}
            Changer le mot de passe
          </button>

          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center justify-center gap-2 text-sm text-muted hover:text-primary-dark"
          >
            <LogOut className="h-4 w-4" />
            Se déconnecter
          </button>
        </form>
      </div>
    </div>
  );
}
