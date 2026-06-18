import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="flex h-full flex-1 flex-col items-center justify-center gap-2 text-center">
      <h1 className="text-3xl font-bold text-primary-dark">404</h1>
      <p className="text-muted">Page introuvable.</p>
      <Link to="/" className="btn-primary mt-4">
        Retour au tableau de bord
      </Link>
    </div>
  );
}
