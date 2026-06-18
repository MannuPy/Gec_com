import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, useLocation, Navigate } from "react-router-dom";
import { Loader2, LogIn, Store } from "lucide-react";

import { authApi } from "@/api/endpoints/auth";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";

const loginSchema = z.object({
  email: z.string().min(1, "L'email est requis.").email("Adresse email invalide."),
  password: z.string().min(1, "Le mot de passe est requis."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

/**
 * Page de connexion. Cf. 17-API-REST.md (POST /auth/login) et 18-SECURITE.md.
 * Design : palette Adobe Color (fond #F2F2F2, carte blanche, accents #0439D9 / #011140).
 */
export default function LoginPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setSession = useAuthStore((s) => s.setSession);
  const navigate = useNavigate();
  const location = useLocation();

  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  // Deja connecte : redirige directement.
  if (accessToken) {
    const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? "/";
    return <Navigate to={redirectTo} replace />;
  }

  const onSubmit = async (values: LoginFormValues) => {
    setApiError(null);
    setIsSubmitting(true);
    try {
      const data = await authApi.login(values);
      setSession({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user: data.user,
      });
      const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? "/";
      navigate(redirectTo, { replace: true });
    } catch (error) {
      setApiError(getApiErrorMessage(error, "Email ou mot de passe incorrect."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white">
            <Store className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-semibold text-primary-dark">GesCom-BF</h1>
          <p className="text-sm text-muted">Connectez-vous a votre espace de gestion</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
          {apiError && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{apiError}</div>
          )}

          <div>
            <label htmlFor="email" className="label">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              className="input"
              placeholder="vous@gescom-bf.bf"
              {...register("email")}
            />
            {errors.email && <p className="error-text">{errors.email.message}</p>}
          </div>

          <div>
            <label htmlFor="password" className="label">
              Mot de passe
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="input"
              placeholder="********"
              {...register("password")}
            />
            {errors.password && <p className="error-text">{errors.password.message}</p>}
          </div>

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <LogIn className="h-4 w-4" />
            )}
            Se connecter
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-muted">
          GesCom-BF &middot; Gestion commerciale pour quincailleries
        </p>
      </div>
    </div>
  );
}
