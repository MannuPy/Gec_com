import type { ReactNode } from "react";
import { X } from "lucide-react";

interface ModalProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
  widthClassName?: string;
}

/**
 * Fenêtre modale générique (formulaires de création/édition).
 * Superposition cliquable pour fermer + bouton "X".
 */
export function Modal({ title, onClose, children, widthClassName = "max-w-lg" }: ModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="absolute inset-0" onClick={onClose} />
      <div className={`relative w-full ${widthClassName} max-h-[90vh] overflow-y-auto rounded-xl bg-white p-6 shadow-card`}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-primary-dark">{title}</h2>
          <button type="button" className="btn-ghost p-1.5" onClick={onClose}>
            <X className="h-4 w-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
